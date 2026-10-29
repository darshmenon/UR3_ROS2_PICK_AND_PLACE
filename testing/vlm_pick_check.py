#!/usr/bin/env python3
"""End to end: does MTC pick the object the VLM was asked for, among several?

Launches the six-object world (red cylinder, green cube, blue cube, yellow cylinder, orange tall box, red ball), the colour/depth
detector, vlm_grounding_node and the MTC retry node. Sends one text query, waits for the VLM's choice, runs ONE
MTC pick-and-place and reports which object ended up at the place spot (0.35, 0.20) and how far each object moved.

    python3 testing/vlm_pick_check.py --query "the green cube" --expect green_box --domain 80
"""
import argparse
import math
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402
import benchmark_mtc as bmtc  # noqa: E402

MODELS = ["red_cylinder", "green_box", "blue_box", "yellow_cylinder", "orange_tall_box", "red_ball"]
WORLD = "colored_two_objects.world"
YCB_MODELS = ["ycb_005_tomato_soup_can", "ycb_013_apple", "ycb_011_banana", "ycb_025_mug", "ycb_010_potted_meat_can"]


def poses(models=None):
    out = {}
    for m in (models or MODELS):
        bench.OBJECT = m
        out[m] = bench.object_pose()
    return out


def spawn(cmd, domain, log):
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain), GZ_VERSION="harmonic")
    full = f"source /opt/ros/humble/setup.bash && source {bench.REPO}/install/setup.bash && exec {cmd}"
    return subprocess.Popen(["bash", "-c", full], env=env, stdout=log, stderr=subprocess.STDOUT,
                            preexec_fn=os.setsid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--expect", required=True)
    ap.add_argument("--world", default=WORLD)
    ap.add_argument("--models", nargs="+", default=MODELS, help="model names to track (default: the coloured set)")
    ap.add_argument("--gripper", default="robotiq_2f_85")
    ap.add_argument("--domain", type=int, default=80)
    ap.add_argument("--settle", type=float, default=45.0)
    ap.add_argument("--mtc-startup", type=float, default=40.0)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--record-dir", default=str(bench.REPO / "testing" / "_out" / "recordings"),
                    help="save an MP4 (and GIF) of the 960x540 showcase camera from the query to the end of the pick")
    args = ap.parse_args()

    (bench.REPO / "logs").mkdir(exist_ok=True)
    log = open(bench.REPO / "logs" / "vlm_pick_check.log", "w")
    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    sim = mtc = perc = vlm = bridge = None
    verdict = "NO RESULT"
    try:
        sim, _ = bench.launch_sim(args.gripper, args.world, args.domain, args.settle)
        mtc = bmtc.launch_mtc(args.gripper, args.domain, 1, args.mtc_startup)
        perc = spawn("ros2 launch ur_perception perception.launch.py publish_planning_scene:=false",
                     args.domain, log)
        vlm = spawn("ros2 run ur_perception vlm_grounding_node.py", args.domain, log)
        bridge = spawn("ros2 run ros_gz_image image_bridge /showcase_cam/image", args.domain, log)
        time.sleep(20)

        import rclpy
        from geometry_msgs.msg import PoseStamped
        from rclpy.node import Node
        from std_msgs.msg import String
        from std_srvs.srv import Trigger
        rclpy.init()
        node = Node("vlm_pick_check")
        got, status = {}, {"text": ""}
        node.create_subscription(PoseStamped, "/vlm/target_pose", lambda m: got.__setitem__("pose", m), 10)
        node.create_subscription(String, "/vlm/target_object_id", lambda m: got.__setitem__("id", m.data), 10)
        node.create_subscription(String, "/mtc_bt/status", lambda m: status.update(text=m.data), 10)
        pub = node.create_publisher(String, "/vlm/query", 10)
        client = node.create_client(Trigger, "/mtc_bt/run")
        frames = []
        rec = {"on": False, "last": 0.0}

        def on_image(m):
            now = time.time()
            if not rec["on"] or now - rec["last"] < 0.1:
                return
            rec["last"] = now
            import cv2
            import numpy as np
            img = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, -1)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) if m.encoding == "rgb8" else img.copy()
            cv2.putText(img, f'"{args.query}"  t={now - rec["t0"]:.0f}s', (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(img, f'"{args.query}"  t={now - rec["t0"]:.0f}s', (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (255, 255, 255), 1, cv2.LINE_AA)
            frames.append(img)

        from sensor_msgs.msg import Image as RosImage
        node.create_subscription(RosImage, "/showcase_cam/image", on_image, 1)
        threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()
        if not client.wait_for_service(timeout_sec=90.0):
            sys.exit("MTC /mtc_bt/run not available")

        models = args.models
        before = poses(models)
        print("before:", {k: tuple(round(x, 3) for x in v) if v else None for k, v in before.items()}, flush=True)

        t0 = time.time()
        rec["t0"] = t0
        rec["on"] = True
        last = 0.0
        while "pose" not in got and time.time() - t0 < 150:
            if time.time() - last > 5.0:      # a single publish can be lost while the sim is loading discovery
                pub.publish(String(data=args.query))
                last = time.time()
            time.sleep(0.2)
        if "pose" not in got:
            verdict = "VLM gave no target"
            print(verdict, flush=True)
            return
        p = got["pose"].pose.position
        chosen = min((m for m in models if before[m]),
                     key=lambda m: math.hypot(before[m][0] - p.x, before[m][1] - p.y))
        d = math.hypot(before[chosen][0] - p.x, before[chosen][1] - p.y) * 1000
        print(f'VLM "{args.query}" -> id={got.get("id")!r} pose=({p.x:.3f}, {p.y:.3f}) nearest object: {chosen} '
              f'({d:.0f} mm)  [{time.time() - t0:.0f}s]', flush=True)

        resp = client.call_async(Trigger.Request())
        end = time.time() + 20
        while not resp.done() and time.time() < end:
            time.sleep(0.1)
        end = time.time() + args.timeout
        while time.time() < end and not any(k in status["text"] for k in ("SUCCESS", "FAILURE", "stopped")):
            time.sleep(1.0)
        print("MTC status:", status["text"] or "timeout", flush=True)
        time.sleep(3)

        after = poses(models)
        place = (bench.PLACE_XY[0], bench.PLACE_XY[1])
        at_place = [m for m in models if after[m] and math.hypot(after[m][0] - place[0], after[m][1] - place[1]) < 0.05]
        for m in models:
            if before[m] and after[m]:
                mv = math.hypot(after[m][0] - before[m][0], after[m][1] - before[m][1]) * 1000
                print(f"  {m:16s} moved {mv:6.0f} mm  now ({after[m][0]:.3f}, {after[m][1]:.3f}, {after[m][2]:.3f})")
        ok = at_place == [args.expect]
        verdict = (f"PASS: {args.expect} was picked and placed" if ok else
                   f"FAIL: expected {args.expect}, at place spot: {at_place or 'nothing'}")
        print(verdict, flush=True)
    finally:
        try:
            rec["on"] = False
            if frames:
                import cv2
                out = Path(args.record_dir)
                out.mkdir(parents=True, exist_ok=True)
                name = f"vlm_pick_{args.expect}_{'PASS' if verdict.startswith('PASS') else 'FAIL'}"
                h, w = frames[0].shape[:2]
                vw = cv2.VideoWriter(str(out / f"{name}.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10, (w, h))
                for f in frames:
                    vw.write(f)
                vw.release()
                try:
                    from PIL import Image as PILImage
                    ims = [PILImage.fromarray(cv2.cvtColor(cv2.resize(f, (640, 360), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB))
                           for f in frames]
                    ims[0].save(out / f"{name}.gif", save_all=True, append_images=ims[1:], duration=100, loop=0)
                except ImportError:
                    pass
                print(f"recording saved: {out / name}.mp4 ({len(frames)} frames)", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"recording failed: {e}", flush=True)
        for p in (bridge, vlm, perc, mtc):
            if p is not None:
                try:
                    os.killpg(os.getpgid(p.pid), signal.SIGINT)
                    p.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                except Exception:  # noqa: BLE001
                    pass
        bench.stop_sim([sim])
        try:
            rclpy.shutdown()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()

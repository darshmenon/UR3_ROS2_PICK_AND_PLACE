#!/usr/bin/env python3
"""Film one pick and place from the showcase camera and write it as a README GIF.

    python3 testing/record_showcase.py --gripper onrobot_rg2 --object cube_5cm --out assets/pick_and_place_rg2.gif
    python3 testing/record_showcase.py --gripper robotiq_2f_85 --object cylinder_5cm --mode mtc --out assets/mtc_2f85.gif

mode executor: MotionExecutor (IK + Pilz).  mode mtc: MoveIt Task Constructor through the retry node.
The showcase camera (960x540, in every colored_*.world) is off unless subscribed to, so it costs nothing otherwise.
Frames are kept in --frames-dir (default /tmp) so a GIF can be rebuilt with a different crop or speed.
"""
import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402

CROP = "130,25,830,475"        # keeps the whole table, the arm and both the pick and the place spot


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gripper", default="onrobot_rg2", choices=bench.DEFAULT_GRIPPERS)
    ap.add_argument("--object", default="cube_5cm", choices=list(bench.OBJECTS))
    ap.add_argument("--mode", default="executor", choices=["executor", "mtc"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--period", type=float, default=0.3)
    ap.add_argument("--frames-dir", default=None)
    ap.add_argument("--width", type=int, default=520)
    ap.add_argument("--fps", type=float, default=8.0)
    ap.add_argument("--max-mb", type=float, default=1.6)
    args = ap.parse_args()

    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    env = dict(os.environ, ROS_DOMAIN_ID=str(args.domain), GZ_VERSION="harmonic")
    src = f"source /opt/ros/humble/setup.bash && source {bench.REPO}/install/setup.bash && "
    obj = bench.OBJECTS[args.object]
    bench.OBJECT = obj["model"]
    frames = Path(args.frames_dir or f"/tmp/showcase_{args.gripper}_{args.object}_{args.mode}")
    subprocess.run(["rm", "-rf", str(frames)])
    frames.mkdir(parents=True)

    import cv2
    import numpy as np
    import rclpy
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from sensor_msgs.msg import Image
    from std_msgs.msg import String
    from std_srvs.srv import Trigger

    rclpy.init()
    (bench.REPO / "logs").mkdir(exist_ok=True)
    sim = bench.launch_sim(args.gripper, obj["world"], args.domain, 45)
    bridge = subprocess.Popen(["bash", "-c", src + "exec ros2 run ros_gz_image image_bridge /showcase_cam/image"], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
    mtc = None
    node = Node("record_showcase")
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    threading.Thread(target=executor.spin, daemon=True).start()
    state = {"last": 0.0, "n": 0, "on": False}

    def on_image(m):
        now = time.time()
        if not state["on"] or now - state["last"] < args.period:
            return
        state["last"] = now
        im = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, -1)
        cv2.imwrite(str(frames / f"{state['n']:05d}.png"), cv2.cvtColor(im, cv2.COLOR_RGB2BGR) if m.encoding == "rgb8" else im)
        state["n"] += 1

    node.create_subscription(Image, "/showcase_cam/image", on_image, 5)
    ok = False
    try:
        time.sleep(4)
        if args.mode == "executor":
            from ur_llm_planner.motion_executor import MotionExecutor
            mover = MotionExecutor(node)
            mover.set_gripper(args.gripper)
            mover.wait_for_servers(60.0)
            depth = min(0.03, 0.4 * obj["height"])
            pick_z = obj["top_z"] - (obj.get("grasp_depth") or depth)
            state["on"] = True
            ok = mover.execute_task_list([
                {"action": "move_to_named_pose", "pose_name": "home"}, {"action": "open_gripper"},
                {"action": "pick", "object_id": obj["model"], "object_x": 0.35, "object_y": 0.0, "object_z": pick_z},
                {"action": "place", "x": 0.35, "y": 0.20, "z": pick_z + 0.01},
                {"action": "move_to_named_pose", "pose_name": "home"}])
            time.sleep(1.5)
        else:
            mtc = subprocess.Popen(["bash", "-c", src + f"exec ros2 launch ur_bt_planner mtc_retry.launch.py gripper:={args.gripper} max_attempts:=3"],
                                   env=env, stdout=open(bench.REPO / "logs" / "showcase_mtc.log", "w"), stderr=subprocess.STDOUT,
                                   preexec_fn=os.setsid)
            time.sleep(40)
            status = {"t": ""}
            node.create_subscription(String, "/mtc_bt/status", lambda m: status.update(t=m.data), 10)
            cli = node.create_client(Trigger, "/mtc_bt/run")
            cli.wait_for_service(timeout_sec=60)
            state["on"] = True
            fut = cli.call_async(Trigger.Request())
            end = time.time() + 600
            while time.time() < end and not any(k in status["t"] for k in ("SUCCESS", "FAILURE")):
                time.sleep(1.0)
            ok = "SUCCESS" in status["t"]
            time.sleep(3.0)
        state["on"] = False
    finally:
        for p in (mtc, bridge):
            if p is not None:
                for sig in (signal.SIGINT, signal.SIGKILL):
                    try:
                        os.killpg(os.getpgid(p.pid), sig)
                        p.wait(timeout=20)
                        break
                    except (subprocess.TimeoutExpired, ProcessLookupError):
                        continue
        bench.stop_sim(sim)
        executor.shutdown()
        rclpy.shutdown()
    print(f"{state['n']} frames in {frames}; sequence {'succeeded' if ok else 'did NOT succeed'}", flush=True)
    if state["n"] > 5:
        subprocess.run([sys.executable, str(Path(__file__).with_name("make_gif.py")), str(frames), args.out,
                        "--crop", CROP, "--width", str(args.width), "--fps", str(args.fps), "--max-mb", str(args.max_mb)])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

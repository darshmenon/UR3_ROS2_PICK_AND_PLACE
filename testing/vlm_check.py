#!/usr/bin/env python3
"""Check the VLM grounding node against Gazebo ground truth.

Launches the sim (head camera), the colour/depth detector and vlm_grounding_node, sends text queries on
/vlm/query and prints the VLM pose and chosen object id next to the true object position:

    python3 testing/vlm_check.py --object cylinder_5cm --domain 78
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


def spawn(cmd, domain, log):
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain), GZ_VERSION="harmonic")
    full = f"source /opt/ros/humble/setup.bash && source {bench.REPO}/install/setup.bash && exec {cmd}"
    return subprocess.Popen(["bash", "-c", full], env=env, stdout=log, stderr=subprocess.STDOUT,
                            preexec_fn=os.setsid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gripper", default="robotiq_2f_85")
    ap.add_argument("--object", default="cylinder_5cm", choices=list(bench.OBJECTS))
    ap.add_argument("--queries", nargs="+", default=["the red cylinder", "the red object on the table",
                                                       "the blue sphere"])
    ap.add_argument("--domain", type=int, default=78)
    ap.add_argument("--settle", type=float, default=45.0)
    ap.add_argument("--model", default="qwen2.5vl:3b")
    args = ap.parse_args()

    obj = bench.OBJECTS[args.object]
    bench.OBJECT = obj["model"]
    (bench.REPO / "logs").mkdir(exist_ok=True)
    log = open(bench.REPO / "logs" / "vlm_check.log", "w")
    sim, perc, vlm = None, None, None
    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    try:
        sim, _ = bench.launch_sim(args.gripper, obj["world"], args.domain, args.settle)
        perc = spawn("ros2 launch ur_perception perception.launch.py publish_planning_scene:=false",
                     args.domain, log)
        vlm = spawn(f"ros2 run ur_perception vlm_grounding_node.py --ros-args -p model:={args.model}",
                    args.domain, log)
        time.sleep(15)

        import rclpy
        from geometry_msgs.msg import PoseStamped
        from rclpy.node import Node
        from std_msgs.msg import String
        rclpy.init()
        node = Node("vlm_check")
        got = {}
        node.create_subscription(PoseStamped, "/vlm/target_pose", lambda m: got.__setitem__("pose", m), 10)
        node.create_subscription(String, "/vlm/target_object_id", lambda m: got.__setitem__("id", m.data), 10)
        pub = node.create_publisher(String, "/vlm/query", 10)
        from ur_interfaces.msg import DetectedObjectArray
        det = {}
        node.create_subscription(DetectedObjectArray, "/detected_objects",
                                 lambda m: det.__setitem__("red", [o for o in m.objects if o.label == "red"]), 10)
        threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()
        time.sleep(2)

        truth = bench.object_pose()
        print(f"truth (gz world): {truth}", flush=True)
        reds = det.get("red") or []
        if reds and truth:
            o = reds[0]
            print(f"colour+depth detector: ({o.position.x:.3f}, {o.position.y:.3f}, {o.position.z:.3f}) "
                  f"err_xy={math.hypot(o.position.x - truth[0], o.position.y - truth[1]) * 1000:.0f}mm "
                  f"({len(reds)} red object(s))", flush=True)
        else:
            print("colour+depth detector: no red detection", flush=True)
        for q in args.queries:
            got.clear()
            t0 = time.time()
            pub.publish(String(data=q))
            while "pose" not in got and time.time() - t0 < 90:
                time.sleep(0.2)
            if "pose" in got:
                p = got["pose"].pose.position
                err = math.hypot(p.x - truth[0], p.y - truth[1]) * 1000 if truth else float("nan")
                time.sleep(0.5)
                print(f'"{q}": pose=({p.x:.3f}, {p.y:.3f}, {p.z:.3f}) err_xy={err:.0f}mm '
                      f'id={got.get("id")!r} {time.time() - t0:.1f}s', flush=True)
            else:
                print(f'"{q}": no pose within 90 s (not found, or error: see logs/vlm_check.log)', flush=True)
            time.sleep(2)
    finally:
        for p in (vlm, perc):
            if p is not None:
                try:
                    os.killpg(os.getpgid(p.pid), signal.SIGINT)
                    p.wait(timeout=15)
                except Exception:  # noqa: BLE001
                    pass
        bench.stop_sim([sim])
        try:
            rclpy.shutdown()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()

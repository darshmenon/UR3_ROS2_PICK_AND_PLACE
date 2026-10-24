#!/usr/bin/env python3
"""Pick boxes off the conveyor and drop each into the bin of its colour, recording the conveyor camera.

    python3 testing/conveyor_pick_demo.py --boxes 2 --record-dir /tmp/conv_pick --domain 91

Launches the conveyor world headless (arm base on the ground: table_height:=0.0, there is no mount table here),
the conveyor node (one box every --spawn-interval s) and the showcase camera bridge. For each box that
reaches the pick zone it tells the conveyor node the box is picked (otherwise the node keeps teleporting it),
picks it with MotionExecutor and places it above the bin of its colour (red/green/blue), then checks from Gazebo's ground truth that the box ended up on that bin.
Frames go to --record-dir; turn them into a GIF with testing/make_gif.py. One sim at a time.
"""
import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402

BINS = {"red": (0.06, 0.38), "green": (0.20, 0.28), "blue": (0.34, 0.28)}   # conveyor_sorting.world, all within ~0.45 m of the arm base
PICK_ZONE = (0.35, 0.0)
BOX_TOP_Z = 0.10      # belt top 0.05 + 5 cm box
BIN_TOP_Z = 0.03     # bin models are 6 cm tall, centred at z=0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boxes", type=int, default=2, help="boxes to sort")
    ap.add_argument("--gripper", default="onrobot_rg2")
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--settle", type=float, default=70.0)
    ap.add_argument("--belt-speed", type=float, default=0.03)
    ap.add_argument("--spawn-interval", type=float, default=50.0, help="longer than one pick+place (~40 s): the belt holds every arrived box at the same spot, so boxes would pile up")
    ap.add_argument("--grasp-depth", type=float, default=0.03, help="grasp this far below the box top (m)")
    ap.add_argument("--record-dir", default=None)
    args = ap.parse_args()

    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    env = dict(os.environ, GZ_VERSION="harmonic")
    src = f"source /opt/ros/humble/setup.bash && source {REPO}/install/setup.bash && "
    procs = []

    def spawn(cmd, log):
        p = subprocess.Popen(["bash", "-c", src + "exec " + cmd], env=env, stdout=open(log, "w") if log else subprocess.DEVNULL,
                             stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        procs.append(p)
        return p

    bench.stop_sim([])
    results = []
    try:
        spawn(f"ros2 launch ur_gazebo ur.gazebo.launch.py world_file:=conveyor_sorting.world table_height:=0.0 "
              f"use_gazebo_gui:=false use_rviz:=false gripper:={args.gripper}", REPO / "logs" / "conv_pick_sim.log")
        time.sleep(args.settle)

        import rclpy
        from rclpy.executors import SingleThreadedExecutor
        from rclpy.node import Node
        from sensor_msgs.msg import Image
        from std_msgs.msg import String
        from ur_llm_planner.motion_executor import MotionExecutor

        rclpy.init()
        node = Node("conveyor_pick_demo")
        ex_spin = SingleThreadedExecutor()
        ex_spin.add_node(node)
        threading.Thread(target=ex_spin.spin, daemon=True).start()
        ex = MotionExecutor(node)
        ex.set_gripper(args.gripper)
        if not (ex.wait_for_servers(timeout=60.0) and ex.execute_task_list([{"action": "move_to_named_pose", "pose_name": "home"}])):
            print("sim not serving goals", flush=True)
            return 1

        ready = []
        node.create_subscription(String, "/conveyor/object_ready", lambda m: ready.append(m.data.split()), 10)
        picked_pub = node.create_publisher(String, "/conveyor/picked", 10)

        rec_on = threading.Event()
        if args.record_dir:
            import cv2
            import numpy as np
            Path(args.record_dir).mkdir(parents=True, exist_ok=True)
            spawn("ros2 run ros_gz_image image_bridge /showcase_cam_conveyor/image", None)
            last = {}
            node.create_subscription(Image, "/showcase_cam_conveyor/image", lambda m: last.update(i=m), 2)

            def record():
                k = 0
                while True:
                    m = last.pop("i", None)
                    if m is not None and rec_on.is_set():
                        im = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, -1)
                        cv2.imwrite(f"{args.record_dir}/f{k:05d}.png", cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
                        k += 1
                    time.sleep(0.35)
            threading.Thread(target=record, daemon=True).start()

        spawn(f"ros2 run ur_conveyor conveyor_node.py --ros-args -p spawn_interval_s:={args.spawn_interval} "
              f"-p belt_speed:={args.belt_speed} -p belt_z:=0.075 -p world_name:=default -p hold_timeout_s:=60.0",
              REPO / "logs" / "conv_pick_node.log")
        time.sleep(8)
        subprocess.run(["bash", "-c", src + "ros2 service call /conveyor/start std_srvs/srv/Trigger {}"], env=env,
                       capture_output=True, timeout=30)
        rec_on.set()

        sorted_n = 0
        deadline = time.time() + 900
        while sorted_n < args.boxes and time.time() < deadline:
            if not ready:
                time.sleep(0.5)
                continue
            name, color = ready.pop(0)
            if color not in BINS:
                print(f"[demo] {name} is {color}: no bin, leaving it", flush=True)
                continue
            bench.OBJECT = name
            bx, by = BINS[color]
            pick_z = BOX_TOP_Z - args.grasp_depth
            # Let the belt bring the box to rest at the pick spot first; grabbing it while it still creeps in (x ~0.37) failed.
            end_wait = time.time() + 45
            pos = bench.object_pose()
            while pos is not None and pos[0] > PICK_ZONE[0] + 0.008 and time.time() < end_wait:
                time.sleep(1.0)
                pos = bench.object_pose()
            if pos is None:
                print(f"[demo] {name}: pose not found", flush=True)
                continue
            ok = False
            for attempt in (1, 2):
                print(f"[demo] {name} ({color}) attempt {attempt} at ({pos[0]:.3f}, {pos[1]:.3f}) -> bin {color} ({bx}, {by})", flush=True)
                picked_pub.publish(String(data=name))          # the conveyor node stops moving it
                tasks = [
                    {"action": "open_gripper"},
                    {"action": "pick", "object_id": name, "object_x": pos[0], "object_y": pos[1], "object_z": pick_z, "object_yaw": 0.0},
                    {"action": "place", "x": bx, "y": by, "z": 0.06 + 0.04 + bench.PLACE_DZ},
                    {"action": "move_to_named_pose", "pose_name": "home"},
                ]
                ok = bool(ex.execute_task_list(tasks))
                time.sleep(2.0)
                end = bench.object_pose()
                if ok or end is None or not (abs(end[2] - 0.075) < 0.02 and abs(end[1]) < 0.05):
                    break                       # placed, lost, or dropped somewhere that is not the belt: do not retry
                print(f"[demo] {name}: pick failed, box still on the belt at {tuple(round(v, 3) for v in end)} - retrying", flush=True)
                ex.execute_task_list([{"action": "open_gripper"}, {"action": "move_to_named_pose", "pose_name": "home"}])
                pos = end
            end = bench.object_pose()
            on_bin = end is not None and abs(end[0] - bx) < 0.07 and abs(end[1] - by) < 0.07 and end[2] > BIN_TOP_Z
            results.append((name, color, ok, on_bin, end))
            print(f"[demo] {name}: executed={ok} on_bin={on_bin} end={None if end is None else tuple(round(v, 3) for v in end)}", flush=True)
            sorted_n += 1
            if not ok:
                print('[demo] stopping: the arm may still be holding the box', flush=True)
                break
        time.sleep(3)
        rec_on.clear()
        print(f"[demo] sorted {sum(1 for r in results if r[3])}/{len(results)} boxes onto the right bin", flush=True)
    finally:
        for p in reversed(procs):
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGINT)
            except Exception:       # noqa: BLE001
                pass
        time.sleep(6)
        bench.stop_sim([])
    return 0 if results and all(r[3] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

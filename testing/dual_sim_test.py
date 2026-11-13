#!/usr/bin/env python3
"""Simulation test of the dual-arm whole-body coordinator.

Launches the headless dual-arm sim and the coordinator, moves both hands to a meeting pose, "grasps" (freezes the
hands' relative pose), then moves the object along a path while measuring from TF how rigid the hands really stay.

    python3 testing/dual_sim_test.py --domain 91
"""
import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "ur_dual_coordination"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


PICK_Y = 0.12      # half distance between the hands when both grip the plank from above

BAR_SDF = """<sdf version='1.9'><model name='carry_bar'><pose>{x} {y} {z} 0 0 0</pose><link name='link'>
<inertial><mass>0.06</mass><inertia><ixx>0.0003</ixx><iyy>0.0003</iyy><izz>0.0003</izz></inertia></inertial>
<collision name='c'><geometry><box><size>0.06 {len} 0.06</size></box></geometry>
<surface><friction><ode><mu>4.0</mu><mu2>4.0</mu2></ode></friction></surface></collision>
<visual name='v'><geometry><box><size>0.06 {len} 0.06</size></box></geometry>
<material><ambient>0.9 0.2 0.1 1</ambient><diffuse>0.9 0.2 0.1 1</diffuse></material></visual></link></model></sdf>"""


def gz_create(sdf):
    subprocess.run(["gz", "service", "-s", "/world/default/create", "--reqtype", "gz.msgs.EntityFactory",
                    "--reptype", "gz.msgs.Boolean", "--timeout", "5000", "--req", f'sdf: "{sdf.replace(chr(34), chr(39))}"'],
                   check=False, capture_output=True)


def log_plank(label, hands_mid=None):
    """Print the plank's ground-truth position (world frame) and yaw, and its offset from the hands' midpoint."""
    import benchmark_grippers as bench
    bench.OBJECT = "carry_bar"
    pos, yaw = bench.object_pose(), bench.object_yaw_deg()
    if pos is None:
        print(f"   plank [{label}]: not found", flush=True)
        return
    off = "" if hands_mid is None else " offset from hands (%.0f, %.0f, %.0f) mm" % tuple(
        1000 * (np.array(pos) - np.array(hands_mid)))
    print("   plank [%s]: pos (%.3f, %.3f, %.3f) yaw %.0f deg%s" % (label, *pos, yaw or 0.0, off), flush=True)


def close_grippers(node, position=0.8, sides=("left", "right")):
    from control_msgs.action import GripperCommand
    from rclpy.action import ActionClient
    for side in sides:
        cli = ActionClient(node, GripperCommand, f"/{side}_gripper_controller/gripper_cmd")
        cli.wait_for_server(timeout_sec=10)
        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = 200.0
        cli.send_goal_async(goal)
    time.sleep(3.0)


def hold_bar(node, left, right, bar_len):
    """Spawn a bar centred between the two hands and close both grippers on its ends."""
    from control_msgs.action import GripperCommand
    from rclpy.action import ActionClient
    mid = 0.5 * (left.translation + right.translation)
    # A small shelf under the bar's centre holds it in the air while the grippers close, then is removed.
    shelf = ("<sdf version='1.9'><model name='carry_shelf'><static>true</static><pose>%f %f %f 0 0 0</pose><link name='l'>"
             "<collision name='c'><geometry><box><size>0.03 0.03 0.02</size></box></geometry></collision></link></model></sdf>"
             % (mid[0], mid[1], mid[2] - 0.04))
    for side in ("left", "right"):
        cli = ActionClient(node, GripperCommand, f"/{side}_gripper_controller/gripper_cmd")
        cli.wait_for_server(timeout_sec=10)
        goal = GripperCommand.Goal()
        goal.command.position = 0.8
        goal.command.max_effort = 200.0
        cli.send_goal_async(goal)
    time.sleep(3.0)
    gz_create(shelf)
    sdf = BAR_SDF.format(x=mid[0], y=mid[1], z=mid[2], len=bar_len).replace("\n", "")
    gz_create(sdf)
    time.sleep(1.0)
    time.sleep(5.0)
    subprocess.run(["gz", "service", "-s", "/world/default/remove", "--reqtype", "gz.msgs.Entity", "--reptype", "gz.msgs.Boolean",
                    "--timeout", "5000", "--req", 'name: "carry_shelf" type: MODEL'], check=False, capture_output=True)
    time.sleep(1.0)
    print("bar spawned and both grippers closed", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--gripper", default="robotiq_2f_85")
    ap.add_argument("--settle", type=float, default=70.0)
    ap.add_argument("--object", action="store_true", help="spawn a block between the hands and hold it with both grippers")
    ap.add_argument("--pick", action="store_true", help="pick the block up from the table, carry it and set it back down (implies --object)")
    ap.add_argument("--record-from-grasp", action="store_true", help="with --pick: start saving frames once both grippers hold the plank")
    ap.add_argument("--block-y", type=float, default=0.098, help="block length between the hands (m)")
    ap.add_argument("--record-dir", default="", help="save /showcase_cam_dual/image frames here (for make_gif.py)")
    args = ap.parse_args()
    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    env = dict(os.environ, ROS_DOMAIN_ID=str(args.domain), GZ_VERSION="harmonic")
    src = f"source /opt/ros/humble/setup.bash && source {REPO}/install/setup.bash && "

    import pinocchio as pin
    import rclpy
    import tf2_ros
    from builtin_interfaces.msg import Duration
    from geometry_msgs.msg import PoseStamped
    from rclpy.node import Node
    from std_srvs.srv import Trigger
    from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
    from ur_dual_coordination.controller import reach_poses
    from ur_dual_coordination.kinematics import ARM_JOINTS, DualArm
    import benchmark_grippers as bench

    xml = subprocess.run(["bash", "-c", src + f"xacro {REPO}/moveit_config/config/dual_ur.urdf.xacro gripper:={args.gripper}"],
                         capture_output=True, text=True, check=True).stdout
    dual = DualArm(xml)
    q0 = dual.q_from_dict({f"{s}_{j}": v for s in ("left", "right") for j, v in (
        ("shoulder_lift_joint", -1.2), ("elbow_joint", 1.6), ("wrist_1_joint", -1.9), ("wrist_2_joint", -1.57))})
    # Hands 12 cm apart for the bare coordination test; with a bar the fingers point inward ~145 mm, so the tool
    # flanges sit 40 cm apart and the pads meet the bar's two ends.
    HALF_GAP = 0.20 if args.object else 0.06
    left = pin.SE3(np.column_stack([[1, 0, 0], np.cross([0, -1, 0], [1, 0, 0]), [0, -1, 0]]), np.array([0.20, HALF_GAP, 0.25]))
    right = pin.SE3(np.column_stack([[1, 0, 0], np.cross([0, 1, 0], [1, 0, 0]), [0, 1, 0]]), np.array([0.20, -HALF_GAP, 0.25]))
    if args.pick:
        args.object = True
        # Top-down grasp of the two ends of a plank (6 wide x 40 long x 10 tall cm) lying on the table: tool z points down, the fingertips
        # reach ~14.5 cm past tool0, so tool0 is 20.5 cm above the table to grip the plank's top 4 cm.
        dual.lower = np.maximum(dual.lower, -3.0)       # the sim controller rejects trajectories beyond +-pi
        dual.upper = np.minimum(dual.upper, 3.0)
        r_down = np.column_stack([[0, 1, 0], [1, 0, 0], [0, 0, -1]])   # fingers close along world x, across the plank

        def hands(z):
            return (pin.SE3(r_down, np.array([0.20, PICK_Y, z])), pin.SE3(r_down, np.array([0.20, -PICK_Y, z])))
        q_pre, el, er = reach_poses(dual, q0, *hands(0.34), iterations=800, q_ref=q0, posture_gain=0.3)
        print(f"hover pose residual {el:.1e}, {er:.1e}", flush=True)
        # straight-down descent in small warm-started steps so no joint (the wrist above all) makes a big turn next to the plank
        q_way, q_cur = [], q_pre
        for z in np.linspace(0.34, 0.19, 5)[1:]:
            q_cur, el, er = reach_poses(dual, q_cur, *hands(z), iterations=300, q_ref=q0, posture_gain=0.3)
            q_way.append(q_cur)
        q_meet = q_way[-1]
        left, right = hands(0.19)
    else:
        q_meet, el, er = reach_poses(dual, q0, left, right)
    print(f"meeting pose found (residual {el:.1e}, {er:.1e})", flush=True)

    (REPO / "logs").mkdir(exist_ok=True)
    sim = subprocess.Popen(["bash", "-c", src + f"exec ros2 launch ur_gazebo dual_ur.gazebo.launch.py use_gazebo_gui:=false "
                            f"use_rviz:=false use_move_group:=false gripper:={args.gripper}"], env=env,
                           stdout=open(REPO / "logs" / "dual_sim.log", "w"), stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    time.sleep(args.settle)
    coord = subprocess.Popen(["bash", "-c", src + "exec ros2 run ur_dual_coordination coordinator_node.py"],
                             env=env, stdout=open(REPO / "logs" / "dual_coord.log", "w"), stderr=subprocess.STDOUT,
                             preexec_fn=os.setsid)
    rclpy.init()
    node = Node("dual_sim_test")
    ex = rclpy.executors.SingleThreadedExecutor()
    ex.add_node(node)
    threading.Thread(target=ex.spin, daemon=True).start()
    buf = tf2_ros.Buffer()
    tf2_ros.TransformListener(buf, node)
    bridge = None
    if args.record_dir:
        import cv2
        from sensor_msgs.msg import Image
        Path(args.record_dir).mkdir(parents=True, exist_ok=True)
        bridge = subprocess.Popen(["bash", "-c", src + "exec ros2 run ros_gz_image image_bridge /showcase_cam_dual/image"],
                                  env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
        cam = {}
        node.create_subscription(Image, "/showcase_cam_dual/image", lambda m: cam.update(img=m), 2)

        rec_on = threading.Event()
        if not args.record_from_grasp:
            rec_on.set()

        def record():
            n = 0
            rec_on.wait()
            while True:
                m = cam.pop("img", None)
                if m is not None:
                    im = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, -1)
                    cv2.imwrite(f"{args.record_dir}/f{n:05d}.png", cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
                    n += 1
                time.sleep(0.4)
        threading.Thread(target=record, daemon=True).start()
    pubs = {s: node.create_publisher(JointTrajectory, f"/{s}_arm_controller/joint_trajectory", 10) for s in ("left", "right")}
    target_pub = node.create_publisher(PoseStamped, "/dual/object_target", 10)
    from std_msgs.msg import String
    status = {"last": ""}
    node.create_subscription(String, "/dual/status", lambda m: status.update(last=m.data), 10)

    def tool_pose(side):
        t = buf.lookup_transform("world", f"{side}_tool0", rclpy.time.Time()).transform
        return pin.SE3(pin.Quaternion(t.rotation.w, t.rotation.x, t.rotation.y, t.rotation.z).matrix(),
                       np.array([t.translation.x, t.translation.y, t.translation.z]))

    def send(q, secs):
        for side, cols in (("left", dual.left_cols), ("right", dual.right_cols)):
            m = JointTrajectory()
            m.joint_names = [f"{side}_{j}" for j in ARM_JOINTS]
            p = JointTrajectoryPoint()
            p.positions = [float(q[c]) for c in cols]
            p.time_from_start = Duration(sec=int(secs))
            m.points = [p]
            pubs[side].publish(m)

    from sensor_msgs.msg import JointState
    js = {}
    node.create_subscription(JointState, "/joint_states", lambda m: js.update(zip(m.name, m.position)), 5)

    def wait_q(q, timeout=150.0, tol=0.03):
        """Block until both arms are within tol rad of q (the sim can run well below real time while recording)."""
        end = time.time() + timeout
        while time.time() < end:
            errs = {f"{side}_{j}": abs(js.get(f"{side}_{j}", 1e3) - float(q[c]))
                    for side, cols in (("left", dual.left_cols), ("right", dual.right_cols)) for j, c in zip(ARM_JOINTS, cols)}
            err = max(errs.values())
            if err < tol:
                return True
            time.sleep(0.5)
        worst = max(errs, key=errs.get)
        print("   (timeout waiting for the arms, worst joint %s off by %.2f rad)" % (worst, err), flush=True)
        return False

    def go_to(q, what, attempts=3):
        """Send both arms to q and wait for them; resend if they stall, give up (raise) if they never arrive."""
        for attempt in range(attempts):
            for _ in range(3):
                send(q, 8)
                time.sleep(1.0)
            if wait_q(q, timeout=120.0, tol=0.1):
                return
            print(f"   {what}: attempt {attempt + 1} stalled, resending", flush=True)
        raise RuntimeError(f"arms never reached the {what}")

    result = {}
    try:
        t_end = time.time() + 40
        while time.time() < t_end:
            try:
                tool_pose("left"), tool_pose("right")
                break
            except Exception:       # noqa: BLE001
                time.sleep(1.0)
        if args.pick:
            subprocess.run(["gz", "service", "-s", "/world/default/remove", "--reqtype", "gz.msgs.Entity", "--reptype", "gz.msgs.Boolean",
                            "--timeout", "5000", "--req", 'name: "red_box" type: MODEL'], check=False, capture_output=True)
            print("sending both arms above the plank", flush=True)
            go_to(q_pre, "hover pose")
            hover_mid = 0.5 * (tool_pose("left").translation + tool_pose("right").translation)
            # spawn the plank right under the hands as they actually are (they sit up to ~2 cm off the commanded x)
            gz_create(BAR_SDF.format(x=hover_mid[0], y=hover_mid[1], z=1.015 + 0.052, len=0.32).replace("<size>0.06 0.32 0.06</size>", "<size>0.04 0.32 0.10</size>").replace("<mass>0.06</mass>", "<mass>0.2</mass>").replace("\n", ""))
            time.sleep(2.0)
        print("sending both arms to the meeting pose", flush=True)
        if args.pick:
            for k, qw in enumerate(q_way):
                go_to(qw, "descent step %d of %d" % (k + 1, len(q_way)))
        else:
            for _ in range(3):
                send(q_meet, 8)
                time.sleep(1.0)
            time.sleep(10)
        goalL, goalR = tool_pose("left"), tool_pose("right")
        print("meeting pose errors (mm): left %.1f right %.1f" % (
            1000 * np.linalg.norm(goalL.translation - left.translation), 1000 * np.linalg.norm(goalR.translation - right.translation)), flush=True)
        if args.pick:
            # one arm takes the plank first, the other joins, then the coordinator moves it
            log_plank("before grasp")
            close_grippers(node, sides=("left",))
            print("left gripper holds the plank", flush=True)
            log_plank("left closed")
            close_grippers(node, sides=("right",))
            print("right gripper joined", flush=True)
            log_plank("both closed")
            time.sleep(2.0)
            if bridge is not None:
                cam.pop("img", None)
                rec_on.set()
        elif args.object:
            hold_bar(node, goalL, goalR, args.block_y)
        cli = node.create_client(Trigger, "/dual/grasp")
        cli.wait_for_service(timeout_sec=20)
        fut = cli.call_async(Trigger.Request())
        end = time.time() + 15
        while not fut.done() and time.time() < end:
            time.sleep(0.1)
        print("grasp:", fut.result().message if fut.done() else "no response", flush=True)
        time.sleep(3.0)     # let the grip settle before taking the reference relative pose
        rel0 = tool_pose("left").inverse() * tool_pose("right")
        mid0 = 0.5 * (tool_pose("left").translation + tool_pose("right").translation)
        steps = [("lift 6 cm", [0, 0, 0.06]), ("forward 6 cm", [0.06, 0, 0]), ("sideways 6 cm", [0, 0.06, 0]),
                 ("back to start", [0.0, 0.0, 0.0])]
        mid = mid0.copy()
        for name, delta in steps:
            goal = mid0 + np.array(delta) if name == "back to start" else mid + np.array(delta)
            msg = PoseStamped()
            msg.header.frame_id = "world"
            msg.pose.position.x, msg.pose.position.y, msg.pose.position.z = [float(v) for v in goal]
            msg.pose.orientation.w = 1.0
            # object frame orientation: whatever it was at grasp, so send the current object orientation
            Lp = tool_pose("left")
            qn = pin.Quaternion(Lp.rotation)
            msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z, msg.pose.orientation.w = qn.x, qn.y, qn.z, qn.w
            worst = 0.0
            target_pub.publish(msg)
            t0 = time.time()
            while time.time() - t0 < (90 if args.pick else 14):
                rel = tool_pose("left").inverse() * tool_pose("right")
                d = float(np.linalg.norm((rel0.inverse() * rel).translation))
                worst = max(worst, d)
                if args.object and name == "lift 6 cm" and int(10 * (time.time() - t0)) % 20 == 0:
                    print("   t=%4.1f drift %.1f mm  left z %.3f right z %.3f  left y %.3f right y %.3f" % (
                        time.time() - t0, 1000 * d, tool_pose("left").translation[2], tool_pose("right").translation[2],
                        tool_pose("left").translation[1], tool_pose("right").translation[1]), flush=True)
                time.sleep(0.1)
                if args.pick and time.time() - t0 > 4 and np.linalg.norm(
                        0.5 * (tool_pose("left").translation + tool_pose("right").translation) - goal) < 0.002:
                    break
            mid = 0.5 * (tool_pose("left").translation + tool_pose("right").translation)
            print("   coordinator status:", status["last"], flush=True)
            err = float(np.linalg.norm(mid - goal))
            result[name] = (err, worst)
            if args.pick:
                log_plank(name, mid + np.array([0.0, 0.0, 0.0]))
            print(f"{name:15s} object midpoint error {1000 * err:6.1f} mm | worst hand-to-hand drift {1000 * worst:6.1f} mm", flush=True)
        if args.pick:
            rel = node.create_client(Trigger, "/dual/release")
            rel.wait_for_service(timeout_sec=10)
            f = rel.call_async(Trigger.Request())
            time.sleep(1.0)
            close_grippers(node, 0.0)
            for _ in range(3):
                send(q_pre, 8)
                time.sleep(1.0)
            wait_q(q_pre)
            print("block set down, grippers open, arms backed off", flush=True)
    finally:
        for p in (bridge, coord, sim):
            if p is None:
                continue
            for sig in (signal.SIGINT, signal.SIGKILL):
                try:
                    os.killpg(os.getpgid(p.pid), sig)
                    p.wait(timeout=20)
                    break
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    continue
        bench.stop_sim([])
        rclpy.shutdown()
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())

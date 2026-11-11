#!/usr/bin/env python3
"""Run the UR3 peg-in-hole in headless Gazebo, film it, and plot the contact force.

    python3 ur_force_control/scripts/record_peg_in_hole.py --out assets/gifs/peg_in_hole.gif --offset-x 0.0015 --search

Starts the sim (server only, headless rendering), moves the UR3 above the hole with arm_controller, switches ONCE to the
effort controller (switching back leaves the Gazebo joints in force mode), runs the Cartesian impedance controller and the
task node while saving frames from the close-up camera, then writes <out>.gif, <out>.csv and <out>_forces.png.
"""
import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HOVER_Q = "0.0966,-1.4885,1.9917,-2.0739,-1.5708,-1.4742"   # tool-down above the hole (from the MuJoCo IK, matches Gazebo)


def sh(cmd, env, **kw):
    return subprocess.Popen(["bash", "-c", f"source /opt/ros/humble/setup.bash && source {REPO}/install/setup.bash && {cmd}"],
                            env=env, preexec_fn=os.setsid, **kw)


def run(cmd, env, timeout=60):
    return subprocess.run(["bash", "-c", f"source /opt/ros/humble/setup.bash && source {REPO}/install/setup.bash && {cmd}"],
                          env=env, capture_output=True, text=True, timeout=timeout).stdout


def kill(p):
    for sig in (signal.SIGINT, signal.SIGKILL):
        try:
            os.killpg(os.getpgid(p.pid), sig)
            p.wait(timeout=20)
            return
        except (subprocess.TimeoutExpired, ProcessLookupError):
            continue


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="output GIF path (CSV and force plot are written next to it)")
    ap.add_argument("--domain", type=int, default=78)
    ap.add_argument("--camera", default="peg_close", choices=["peg_close", "peg_cam"])
    ap.add_argument("--offset-x", type=float, default=0.0004)
    ap.add_argument("--offset-y", type=float, default=0.0)
    ap.add_argument("--stiffness", type=float, default=800.0)
    ap.add_argument("--search", action="store_true", help="spiral search when the peg lands on the top face")
    ap.add_argument("--period", type=float, default=0.25, help="seconds between saved frames (wall clock)")
    ap.add_argument("--width", type=int, default=520)
    ap.add_argument("--fps", type=float, default=8.0)
    args = ap.parse_args()

    os.environ["ROS_DOMAIN_ID"] = str(args.domain)       # this process subscribes to the camera too
    env = dict(os.environ, ROS_DOMAIN_ID=str(args.domain), GZ_VERSION="harmonic")
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    frames = Path(f"/tmp/peg_frames_{out.stem}")
    subprocess.run(["rm", "-rf", str(frames)])
    frames.mkdir(parents=True)
    csv = out.with_suffix(".csv")
    procs = []
    ok = False
    try:
        sim = sh("ros2 launch ur_gazebo ur.gazebo.launch.py gripper:=peg world_file:=peg_in_hole.world use_gazebo_gui:=false "
                 "use_rviz:=false use_move_group:=false", env, stdout=open("/tmp/peg_sim.log", "w"), stderr=subprocess.STDOUT)
        procs.append(sim)
        print("waiting for the sim and controllers...", flush=True)
        for _ in range(60):
            time.sleep(3)
            ctl = run("ros2 control list_controllers", env, timeout=20)
            if "arm_controller" in ctl and "active" in ctl.split("arm_controller")[1].split("\n")[0]:
                break
        else:
            raise RuntimeError("arm_controller never became active; see /tmp/peg_sim.log")
        time.sleep(3)
        bridge = sh(f"exec ros2 run ros_gz_image image_bridge /{args.camera}/image", env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(bridge)
        cic = sh(f"exec ros2 run ur_force_control cartesian_impedance_controller --ros-args -p use_sim_time:=true "
                 f"-p stiffness:=\"[{args.stiffness},{args.stiffness},{args.stiffness},30.0,30.0,30.0]\"", env,
                 stdout=open("/tmp/peg_cic.log", "w"), stderr=subprocess.STDOUT)
        procs.append(cic)
        joints = "[shoulder_pan_joint, shoulder_lift_joint, elbow_joint, wrist_1_joint, wrist_2_joint, wrist_3_joint]"
        print("moving above the hole...", flush=True)
        run(f"ros2 topic pub --once /arm_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "
            f"\"{{joint_names: {joints}, points: [{{positions: [{HOVER_Q}], time_from_start: {{sec: 8}}}}]}}\"", env)
        time.sleep(11)
        for _ in range(8):                       # the controller may still be building its model: retry until it answers
            try:
                if "success=True" in run("ros2 service call /cartesian_impedance_controller/hold_current_pose "
                                         "std_srvs/srv/Trigger", env, timeout=15):
                    break
            except subprocess.TimeoutExpired:
                pass
            time.sleep(2)
        else:
            raise RuntimeError("cartesian_impedance_controller never answered hold_current_pose; see /tmp/peg_cic.log")
        run("ros2 control switch_controllers --deactivate arm_controller --activate forward_command_controller_effort", env)

        import cv2
        import numpy as np
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import qos_profile_sensor_data
        from sensor_msgs.msg import Image
        rclpy.init()
        node = Node("peg_recorder")
        st = {"last": 0.0, "n": 0}

        def on_image(m):
            now = time.time()
            if now - st["last"] < args.period:
                return
            st["last"] = now
            im = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, -1)
            cv2.imwrite(str(frames / f"{st['n']:05d}.png"), cv2.cvtColor(im, cv2.COLOR_RGB2BGR) if m.encoding == "rgb8" else im)
            st["n"] += 1

        node.create_subscription(Image, f"/{args.camera}/image", on_image, qos_profile_sensor_data)   # the bridge is best-effort
        task = sh(f"exec ros2 run ur_force_control peg_in_hole_task.py --ros-args -p use_sim_time:=true -p offset_x:={args.offset_x} "
                  f"-p offset_y:={args.offset_y} -p stiffness:={args.stiffness} -p search:={'true' if args.search else 'false'} "
                  f"-p log_csv:={csv}", env, stdout=open("/tmp/peg_task.log", "w"), stderr=subprocess.STDOUT)
        procs.append(task)
        while task.poll() is None:
            rclpy.spin_once(node, timeout_sec=0.1)
        time.sleep(1.0)
        rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
        rclpy.shutdown()
        ok = "INSERTED" in open("/tmp/peg_task.log").read() and "NOT inserted" not in open("/tmp/peg_task.log").read()
        print(f"{st['n']} frames; task log: {open('/tmp/peg_task.log').read().strip().splitlines()[-1:]}", flush=True)
    finally:
        for p in reversed(procs):
            kill(p)
    if csv.exists():
        plot(csv, out.with_name(out.stem + "_forces.png"), args)
    if any(frames.iterdir()):
        subprocess.run([sys.executable, str(REPO / "testing" / "make_gif.py"), str(frames), str(out),
                        "--width", str(args.width), "--fps", str(args.fps), "--max-mb", "2.0"])
    return 0 if ok else 1


def plot(csv, png, args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    d = np.genfromtxt(csv, delimiter=",", names=True)
    fig, ax = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    ax[0].plot(d["t"], d["depth"] * 1e3); ax[0].set_ylabel("insertion depth (mm)")
    ax[1].plot(d["t"], d["f_axial"], label="axial"); ax[1].plot(d["t"], d["f_lateral"], label="lateral")
    ax[1].set_ylabel("impedance force (N)"); ax[1].legend()
    ax[2].plot(d["t"], d["mode"], drawstyle="steps-post"); ax[2].set_ylabel("mode (0/1/2)")
    ax[2].set_xlabel("time (s)  (mode: 0 descend, 1 spiral search, 2 insert)")
    for a in ax:
        a.grid(alpha=.3)
    fig.suptitle(f"UR3 peg-in-hole in Gazebo, K={args.stiffness:.0f} N/m, offset={args.offset_x*1e3:.1f} mm, "
                 f"{'spiral search' if args.search else 'plain descent'}")
    fig.tight_layout()
    fig.savefig(png, dpi=130)
    print("saved", png)


if __name__ == "__main__":
    sys.exit(main())

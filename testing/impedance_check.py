#!/usr/bin/env python3
"""Hold / push / release test for ur_force_control's joint impedance controller in the sim.

    python3 testing/impedance_check.py --wrist-scales 1 4

Per scale (multiplies stiffness and damping of the three wrist joints): launch the single-arm sim headless, switch the arm to
effort mode, wait until it has stopped moving, capture the pose with /joint_impedance_controller/hold_current_pose, then report
the largest joint deviation from that pose (rad) while holding, while a sideways force is applied to the wrist, and after it is
released. A working controller holds within a few hundredths of a rad and returns after the release. One sim at a time.
"""
import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402

JOINTS = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
STIFF = [80.0, 80.0, 60.0, 15.0, 15.0, 15.0]
DAMP = [8.0, 8.0, 6.0, 1.5, 1.5, 1.5]


def one_run(scale, args):
    env = dict(os.environ, ROS_DOMAIN_ID=str(args.domain), GZ_VERSION="harmonic")
    src = f"source /opt/ros/humble/setup.bash && source {REPO}/install/setup.bash && "
    procs = []

    def spawn(cmd, log):
        p = subprocess.Popen(["bash", "-c", src + "exec " + cmd], env=env, stdout=open(log, "w"), stderr=subprocess.STDOUT,
                             preexec_fn=os.setsid)
        procs.append(p)

    def run(cmd, t=40):
        subprocess.run(["bash", "-c", src + cmd], env=env, capture_output=True, text=True, timeout=t)

    def wrench(fy):
        subprocess.run(["gz", "topic", "-t", "/world/default/wrench/persistent", "-m", "gz.msgs.EntityWrench", "-p",
                        'entity {name: "ur::wrist_3_link" type: LINK} wrench {force {x: 0 y: %f z: 0}}' % fy],
                       capture_output=True, timeout=20)

    kp = [k * (scale if i >= 3 else 1.0) for i, k in enumerate(STIFF)]
    kd = [d * (scale if i >= 3 else 1.0) for i, d in enumerate(DAMP)]
    bench.stop_sim([])
    out = {}
    try:
        spawn(f"ros2 launch ur_gazebo ur.gazebo.launch.py world_file:=colored_blocks.world use_gazebo_gui:=false use_rviz:=false "
              f"gripper:={args.gripper}", REPO / "logs" / "imp_check_sim.log")
        time.sleep(args.settle)
        spawn("ros2 run ur_force_control joint_impedance_controller --ros-args -p use_sim_time:=true "
              f"-p stiffness:='{kp}' -p damping:='{kd}' -p sim_time_timer:={'true' if args.sim_time_timer else 'false'} "
              f"-p gravity_scale:={args.gravity_scale}",
              REPO / "logs" / "imp_check_node.log")
        time.sleep(8)
        run("ros2 control switch_controllers --deactivate arm_controller --activate forward_command_controller_effort")

        import rclpy
        from rclpy.node import Node
        from sensor_msgs.msg import JointState
        os.environ["ROS_DOMAIN_ID"] = str(args.domain)
        rclpy.init()
        n = Node("impedance_check")
        js = {}
        n.create_subscription(JointState, "/joint_states", lambda m: js.update(zip(m.name, m.position)), 5)

        def q():
            for _ in range(6):
                rclpy.spin_once(n, timeout_sec=0.1)
            return [js.get(j, float("nan")) for j in JOINTS]

        # wait until the arm has stopped moving
        prev, still, end = q(), 0, time.time() + 90
        while time.time() < end and still < 4:
            time.sleep(2.0)
            cur = q()
            still = still + 1 if max(abs(a - b) for a, b in zip(cur, prev)) < 0.01 else 0
            prev = cur
        out["settled"] = still >= 4
        run("ros2 service call /joint_impedance_controller/hold_current_pose std_srvs/srv/Trigger {}")
        ref = q()

        def dev():
            return [a - b for a, b in zip(q(), ref)]

        samples = []

        def worst(secs):
            w, end = 0.0, time.time() + secs
            while time.time() < end:
                d = dev()
                samples.append(d)
                w = max(w, max(abs(v) for v in d))
                time.sleep(0.25)
            return w
        out["hold"] = worst(args.hold)
        import numpy as np
        arr = np.array(samples)
        tail = arr[-min(20, len(arr)):]
        print("   per joint during the hold (rad): final deviation / oscillation (std of the last ~5 s)", flush=True)
        for j, name in enumerate(JOINTS):
            print(f"     {name:22s} {arr[-1, j]:+.3f} / {tail[:, j].std():.3f}", flush=True)
        wrench(args.force)
        time.sleep(args.push)
        out["pushed"] = max(abs(v) for v in dev())
        wrench(0.0)
        out["released_5s"] = (time.sleep(5.0), max(abs(v) for v in dev()))[1]
        out["released_20s"] = (time.sleep(15.0), max(abs(v) for v in dev()))[1]
    finally:
        try:
            wrench(0.0)
        except Exception:       # noqa: BLE001
            pass
        for p in reversed(procs):
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGINT)
            except Exception:   # noqa: BLE001
                pass
        time.sleep(6)
        bench.stop_sim([])
        try:
            import rclpy
            rclpy.shutdown()
        except Exception:       # noqa: BLE001
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wrist-scales", type=float, nargs="+", default=[1.0, 4.0])
    ap.add_argument("--gripper", default="onrobot_rg2")
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--settle", type=float, default=70.0)
    ap.add_argument("--hold", type=float, default=10.0)
    ap.add_argument("--push", type=float, default=12.0)
    ap.add_argument("--force", type=float, default=45.0, help="sideways force on wrist_3_link (N)")
    ap.add_argument("--sim-time-timer", action="store_true")
    ap.add_argument("--gravity-scale", type=float, default=1.0, help="multiplier on the gravity feedforward (1 = controller default)")
    args = ap.parse_args()
    print(f"{'wrist scale':>11} {'settled':>8} {'hold':>7} {'pushed':>7} {'rel+5s':>7} {'rel+20s':>8}   (max |joint deviation| in rad)")
    for s in args.wrist_scales:
        r = one_run(s, args)
        print(f"{s:>11.1f} {str(r.get('settled')):>8} {r.get('hold', float('nan')):>7.3f} {r.get('pushed', float('nan')):>7.3f} "
              f"{r.get('released_5s', float('nan')):>7.3f} {r.get('released_20s', float('nan')):>8.3f}", flush=True)


if __name__ == "__main__":
    main()

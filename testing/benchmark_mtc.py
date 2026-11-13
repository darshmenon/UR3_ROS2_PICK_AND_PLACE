#!/usr/bin/env python3
"""Pick-and-place benchmark through MoveIt Task Constructor (MTC), scored like benchmark_grippers.py.

Same grippers, objects, worlds, ground-truth scoring (true object pose from Gazebo, within --tol of
pick + (0, 0.20)), so the CSV can be put next to the MotionExecutor results:

    python3 testing/benchmark_mtc.py --grippers robotiq_2f_85 --objects cube_5cm --trials 3 --domain 91 \
        --output testing/benchmark_mtc.csv
    python3 testing/compare_pipelines.py testing/benchmark_grippers_final3.csv testing/benchmark_mtc.csv

Each trial resets the object, asks the MTC retry node (ur_bt_planner mtc_retry.launch.py) for ONE
attempt (--attempts) and waits for its SUCCESS/FAILURE status. MTC does its own perception and
grasp search, so there is no pick position to pass in. One cell per process, one sim at a time.
"""
import argparse
import csv
import math
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402

# moveit_config/config/initial_positions.yaml: pan, lift, elbow, wrist_1, wrist_2, wrist_3
START_POSE = [-0.1, -1.6315, 0.0, 1.8251, 0.0, 1.2844]
FIELDS = ["pipeline", "gripper", "object", "trial", "executed", "success", "error_xy_m", "error_z_m",
          "perception_error_xy_m", "cycle_time_s", "lifted_m", "err_dx_m", "err_dy_m", "notes"]


def launch_mtc(gripper, domain, attempts, startup):
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain), GZ_VERSION="harmonic")
    cmd = ["bash", "-c",
           f"source /opt/ros/humble/setup.bash && source {bench.REPO}/install/setup.bash && "
           f"exec ros2 launch ur_bt_planner mtc_retry.launch.py gripper:={gripper} max_attempts:={attempts}"]
    log = open(bench.REPO / "logs" / f"bench_mtc_{gripper}.log", "w")
    proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    time.sleep(startup)
    return proc


def clear_scene(node, log):
    """Remove every world and attached object from move_group's planning scene; return their names."""
    from moveit_msgs.msg import AttachedCollisionObject, CollisionObject, PlanningScene
    from moveit_msgs.srv import ApplyPlanningScene, GetPlanningScene
    get = node.create_client(GetPlanningScene, "/get_planning_scene")
    apply_ = node.create_client(ApplyPlanningScene, "/apply_planning_scene")
    if not (get.wait_for_service(timeout_sec=10.0) and apply_.wait_for_service(timeout_sec=10.0)):
        log("planning scene services not available")
        return []
    req = GetPlanningScene.Request()
    req.components.components = 4 | 8      # WORLD_OBJECT_NAMES | WORLD_OBJECT_GEOMETRY
    req.components.components |= 2 ** 5    # ROBOT_STATE_ATTACHED_OBJECTS
    fut = get.call_async(req)
    end = time.time() + 10
    while not fut.done() and time.time() < end:
        time.sleep(0.05)
    if not fut.done():
        return []
    scene = fut.result().scene
    diff = PlanningScene()
    diff.is_diff = True
    names = []
    for co in scene.world.collision_objects:
        rm = CollisionObject()
        rm.id, rm.header.frame_id, rm.operation = co.id, co.header.frame_id, CollisionObject.REMOVE
        diff.world.collision_objects.append(rm)
        names.append(f"world:{co.id}")
    for ac in scene.robot_state.attached_collision_objects:
        rm = AttachedCollisionObject()
        rm.link_name, rm.object.id, rm.object.operation = ac.link_name, ac.object.id, CollisionObject.REMOVE
        diff.robot_state.attached_collision_objects.append(rm)
        diff.robot_state.is_diff = True
        names.append(f"attached:{ac.object.id}@{ac.link_name}")
    if names:
        areq = ApplyPlanningScene.Request()
        areq.scene = diff
        fut = apply_.call_async(areq)
        end = time.time() + 10
        while not fut.done() and time.time() < end:
            time.sleep(0.05)
    return names


class DemoRecorder:
    """Log joint states (and the object's true pose, 2 Hz) during one MTC run; saved as an .npz only for successes,
    so the files are demonstrations for imitation learning (obs = q, qd, object pose; action = next q)."""

    def __init__(self, node, out_dir):
        from sensor_msgs.msg import JointState
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.q, self.obj, self.on = [], [], False
        node.create_subscription(JointState, "/joint_states", self._js, 50)

    def _js(self, m):
        if self.on:
            self.q.append((time.time(), dict(zip(m.name, m.position))))

    def start(self):
        self.q, self.obj, self.on = [], [], True
        threading.Thread(target=self._poll, daemon=True).start()

    def _poll(self):
        while self.on:
            p = bench.object_pose()
            if p:
                self.obj.append((time.time(), *p[:3]))
            time.sleep(0.5)

    def save(self, name, success):
        self.on = False
        if not success or len(self.q) < 20:
            return
        import numpy as np
        names = sorted(self.q[0][1])
        np.savez_compressed(self.out / f"{name}.npz", t=np.array([t for t, _ in self.q]), joints=np.array(names),
                            q=np.array([[d.get(n, np.nan) for n in names] for _, d in self.q]),
                            obj=np.array(self.obj))
        print(f"[mtc] saved demo {name}: {len(self.q)} joint samples", flush=True)


def wait_controllers(domain, timeout=300.0, need=("arm_controller", "gripper_controller", "joint_state_broadcaster")):
    """Block until `ros2 control list_controllers` shows every controller in `need` as active (or time runs out)."""
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain))
    end = time.time() + timeout
    while time.time() < end:
        try:
            out = subprocess.run(["bash", "-c", f"source /opt/ros/humble/setup.bash && source {bench.REPO}/install/setup.bash "
                                  "&& ros2 control list_controllers"], env=env, capture_output=True, text=True,
                                 timeout=30).stdout
        except subprocess.TimeoutExpired:
            out = ""
        out = re.sub(r"\x1b\[[0-9;]*m", "", out)      # list_controllers colours its output
        active = {ln.split()[0].split("[")[0] for ln in out.splitlines() if ln.split() and ln.split()[-1] == "active"}
        if all(n in active for n in need):
            print(f"[mtc] controllers active after {timeout - (end - time.time()):.0f}s", flush=True)
            return True
        time.sleep(5.0)
    print("[mtc] WARNING: controllers not active before the timeout", flush=True)
    return False


def run_cell(args, g, name):
    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    import rclpy
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from std_msgs.msg import String
    from std_srvs.srv import Trigger
    from ur_llm_planner.motion_executor import MotionExecutor

    obj = bench.OBJECTS[name]
    bench.OBJECT = obj["model"]
    bench.OBJECT_YAW = 0.0
    (bench.REPO / "logs").mkdir(exist_ok=True)
    rows = []
    rclpy.init()
    sim = bench.launch_sim(g, obj["world"], args.domain, args.settle)
    # A fixed sleep is too short when the machine is busy: wait until the controllers are really active.
    wait_controllers(args.domain, timeout=300.0)
    mtc = launch_mtc(g, args.domain, args.attempts, args.mtc_startup)
    node = Node("benchmark_mtc")
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    threading.Thread(target=executor.spin, daemon=True).start()
    status = {"text": ""}
    node.create_subscription(String, "/mtc_bt/status", lambda m: status.update(text=m.data), 10)
    client = node.create_client(Trigger, "/mtc_bt/run")
    try:
        if not client.wait_for_service(timeout_sec=90.0):
            rows.append(dict(pipeline="mtc", gripper=g, object=name, trial=0, executed=False, success=False,
                             error_xy_m=float("nan"), error_z_m=float("nan"),
                             perception_error_xy_m=float("nan"), cycle_time_s=0.0,
                             lifted_m=float("nan"), err_dx_m=float("nan"), err_dy_m=float("nan"),
                             notes="mtc not ready"))
            return rows
        # MTC leaves the arm over the place spot, and it plans badly from there and from the "home" pose
        # (arm straight up, wrist camera next to the torso link). It works from the simulator's start pose,
        # so return to that before every trial, gripper open.
        mover = MotionExecutor(node)
        mover.set_gripper(g)
        recorder = bench.Recorder(node, args.record_topic, args.record_dir, args.record_period,
                                  args.record_frames) if args.record_dir else None
        demo = DemoRecorder(node, args.demo_dir) if args.demo_dir else None
        # The object is spawned slightly above the table and drops on start-up: take the reference pose only once
        # z has stopped changing, otherwise it is the pre-drop height (never reached again after a reset).
        initial, last = bench.object_pose(), None
        for _ in range(30):
            time.sleep(1.0)
            initial = bench.object_pose()
            if initial and last and max(abs(a - b) for a, b in zip(initial[:3], last[:3])) < 0.0005:
                break
            last = initial
        print(f"[mtc] resting reference pose: {initial}", flush=True)
        for t in range(args.trial_start, args.trial_start + args.trials):
            if args.restart_mtc and t > args.trial_start:        # diagnostic: does state leak from one MTC run into the next?
                for sig in (signal.SIGINT, signal.SIGKILL):
                    try:
                        os.killpg(os.getpgid(mtc.pid), sig)
                        mtc.wait(timeout=20)
                        break
                    except (subprocess.TimeoutExpired, ProcessLookupError):
                        continue
                mtc = launch_mtc(g, args.domain, args.attempts, args.mtc_startup)
                client.wait_for_service(timeout_sec=60.0)
            # Clear the old scene FIRST: leftover collision objects can block the move back, and an arm still
            # hovering over the place spot shows up in the point cloud as extra "objects".
            left = clear_scene(node, lambda m: print(f"[mtc] {m}", flush=True))
            print(f"[mtc] trial {t}: planning scene held before clearing: {left}", flush=True)
            mover.open_gripper()
            homed = False
            for _ in range(3):
                # the perception node re-adds support_surface/objects between tries; an arm resting on the
                # table then starts in collision (INVALID_MOTION_PLAN), so clear again before every attempt
                clear_scene(node, lambda m: print(f"[mtc] {m}", flush=True))
                homed = mover._move_to_joint_values("arm", START_POSE)
                if homed:
                    break
                time.sleep(1.0)
            print(f"[mtc] trial {t}: arm back at start pose: {homed}", flush=True)
            if not homed:
                # the arm/MoveGroup stopped answering: every later trial would just fail. End this process so the
                # parent can start a fresh sim and carry on from this trial.
                print(f"[mtc] trial {t}: arm hung, ending this sim (parent restarts it)", flush=True)
                break
            # A reset cylinder can wobble, tip and roll before the arm moves: wait until it is still and
            # upright (z back at its standing height) and re-reset if not, rather than plan on a lying object.
            before = None
            for _ in range(8):
                # no drop height: a cylinder released 5 mm above the table lands, rocks and tips over
                bench.reset_object(initial, lift=0.0)
                time.sleep(2.0)
                # set_pose does not clear velocity, and a cylinder can sit upright for a second or two and then
                # tip and roll off. Only call it settled once z AND xy stay at the start pose for 4 s straight.
                good = 0
                for _ in range(8):
                    before = bench.object_pose()
                    still = bool(before and initial and abs(before[2] - initial[2]) < 0.004
                                 and math.hypot(before[0] - initial[0], before[1] - initial[1]) < 0.005)
                    good = good + 1 if still else 0
                    if good >= 8 or (before and initial and before[2] < initial[2] - 0.01):
                        break
                    time.sleep(0.5)
                if good >= 8:
                    break
                print(f"[mtc] trial {t}: object not settled upright (z={before and before[2]}), re-resetting",
                      flush=True)
            if good < 8:
                # a toppled/rolling start is a harness problem, not an MTC failure: do not score it
                print(f"[mtc] {g}/{name} trial {t}: SKIPPED, object would not settle (pose {before})", flush=True)
                rows.append(dict(pipeline="mtc", gripper=g, object=name, trial=t, executed=False, success=False,
                                 error_xy_m=float("nan"), error_z_m=float("nan"),
                                 perception_error_xy_m=float("nan"), cycle_time_s=0.0, lifted_m=float("nan"),
                                 err_dx_m=float("nan"), err_dy_m=float("nan"), notes="skipped: start not settled"))
                continue
            status["text"] = ""
            if recorder is not None:
                recorder.start()
            if demo is not None:
                demo.start()
            t0 = time.time()
            with bench.LiftWatcher() as watcher:
                resp = None
                busy_until = time.time() + 300      # the previous trial's retry loop can still be running
                while True:
                    fut = client.call_async(Trigger.Request())
                    end = time.time() + 20
                    while not fut.done() and time.time() < end:
                        time.sleep(0.1)
                    resp = fut.result() if fut.done() else None
                    if resp is not None and not resp.success and "Already running" in resp.message \
                            and time.time() < busy_until:
                        time.sleep(5.0)
                        continue
                    break
                t0 = time.time()                    # the cycle time starts when MTC really starts
                notes = ""
                if resp is None or not resp.success:
                    notes = f"run not accepted: {getattr(resp, 'message', 'no reply')}"
                else:
                    end = time.time() + args.trial_timeout
                    while time.time() < end and not any(k in status["text"] for k in ("SUCCESS", "FAILURE", "stopped")):
                        time.sleep(1.0)
                    if not any(k in status["text"] for k in ("SUCCESS", "FAILURE", "stopped")):
                        notes = "timeout"
            cycle = time.time() - t0
            time.sleep(2.0)   # let the object settle
            after = bench.object_pose()
            ex_xy = ex_z = err_dx = err_dy = float("nan")
            success = False
            if before is None or after is None:
                notes = (notes + "; " if notes else "") + "no gz pose"
            else:
                tx = before[0] + (bench.PLACE_XY[0] - bench.PICK_XY[0])
                ty = before[1] + (bench.PLACE_XY[1] - bench.PICK_XY[1])
                err_dx, err_dy = after[0] - tx, after[1] - ty
                ex_xy = math.hypot(err_dx, err_dy)
                ex_z = after[2] - before[2]
                moved = math.hypot(after[0] - before[0], after[1] - before[1]) > 0.05
                carried = watcher.max_z is not None and watcher.max_z - before[2] > 0.03   # really lifted off the table
                success = moved and carried and ex_xy < args.tol
                # a fail by a few mm vs. a toppled/rolled object: z back at standing height means still upright
                upright = abs(ex_z) < 0.01
                notes = (notes + "; " if notes else "") + \
                    f"final xy={ex_xy * 1000:.0f}mm {'upright' if upright else 'TOPPLED'}" \
                    + (" near(<30mm)" if moved and ex_xy < 0.03 else "")
                if not moved:
                    notes = (notes + "; " if notes else "") + "object not moved"
                elif not carried:
                    notes = (notes + "; " if notes else "") + "object never lifted (pushed or rolled, not carried)"
            lifted = (watcher.max_z - before[2]) if (before is not None and watcher.max_z is not None) \
                else float("nan")
            rows.append(dict(pipeline="mtc", gripper=g, object=name, trial=t,
                             executed="SUCCESS" in status["text"], success=success, error_xy_m=ex_xy,
                             error_z_m=ex_z, perception_error_xy_m=float("nan"), cycle_time_s=cycle,
                             lifted_m=lifted, err_dx_m=err_dx, err_dy_m=err_dy, notes=(notes + " | " if notes else "") + status["text"]))
            if recorder is not None:
                recorder.save(f"mtc_{g}_{name}_t{t}", success)
            if demo is not None:
                demo.save(f"mtc_{g}_{name}_t{t}_{int(time.time())}", success)
            print(f"[mtc] {g}/{name} trial {t}: success={success} xy={ex_xy * 1000:.0f}mm "
                  f"status={status['text']!r} {cycle:.0f}s", flush=True)
            bench.reset_object(initial, lift=0.0)
    finally:
        for p in (mtc,):
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGINT)
                p.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)   # only our own launch's process group
            except ProcessLookupError:
                pass
        bench.stop_sim(sim)
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grippers", nargs="+", default=bench.DEFAULT_GRIPPERS)
    ap.add_argument("--objects", nargs="+", default=[o for o in bench.OBJECTS if o != "ball_6cm"], choices=list(bench.OBJECTS))
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--attempts", type=int, default=1, help="MTC attempts per trial (1 = no retries)")
    ap.add_argument("--tol", type=float, default=0.02)
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--settle", type=float, default=45.0, help="seconds after the sim launch")
    ap.add_argument("--mtc-startup", type=float, default=40.0, help="seconds after the MTC launch")
    ap.add_argument("--record-dir", default=None, help="save a labelled frame strip per trial here")
    ap.add_argument("--record-topic", default="/camera_head/color/image_raw")
    ap.add_argument("--record-period", type=float, default=0.5)
    ap.add_argument("--record-frames", type=int, default=24)
    ap.add_argument("--demo-dir", default=None, help="save joint-state demos of successful trials here (.npz)")
    ap.add_argument("--restart-mtc", action="store_true", help="relaunch the MTC nodes before every trial after the first")
    ap.add_argument("--chunk", type=int, default=4,
                    help="trials per sim: a fresh sim every N trials (and after a hang), the sim degrades after ~5")
    ap.add_argument("--trial-start", type=int, default=1, help=argparse.SUPPRESS)
    ap.add_argument("--trial-timeout", type=float, default=420.0)
    ap.add_argument("--output", default=None)
    ap.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    out = Path(args.output or bench.REPO / "testing" / f"benchmark_mtc_{datetime.now():%Y%m%d_%H%M%S}.csv")
    if args.child:
        rows = run_cell(args, args.grippers[0], args.objects[0])
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        return 0

    all_rows = []
    for g in args.grippers:
        for name in args.objects:
            done, stalled = 0, 0
            while done < args.trials and stalled < 2:
                n = min(args.chunk, args.trials - done)
                tmp = out.with_suffix(f".{g}.{name}.tmp.csv")
                subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", "--grippers", g,
                                "--objects", name, "--trials", str(n), "--trial-start", str(done + 1),
                                "--attempts", str(args.attempts),
                                "--tol", str(args.tol), "--domain", str(args.domain), "--settle", str(args.settle),
                                "--mtc-startup", str(args.mtc_startup), "--trial-timeout", str(args.trial_timeout),
                                *(["--restart-mtc"] if args.restart_mtc else []),
                                *(["--record-dir", args.record_dir, "--record-topic", args.record_topic,
                                   "--record-period", str(args.record_period), "--record-frames", str(args.record_frames)]
                                  if args.record_dir else []),
                                *(["--demo-dir", args.demo_dir] if args.demo_dir else []),
                                "--output", str(tmp)], check=False)
                got = []
                if tmp.exists():
                    got = bench.load_rows_from(list(csv.DictReader(open(tmp))))
                    tmp.unlink()
                trials = [int(r["trial"]) for r in got if r["trial"]]
                all_rows += got
                new_done = max(trials) if trials else done
                stalled = stalled + 1 if new_done <= done else 0     # a sim that cannot run even one trial: give up
                done = new_done
    if not all_rows:
        print("no results")
        return 1
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    bench.summarise([r for r in all_rows if r["trial"]], args.grippers, args.objects)
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

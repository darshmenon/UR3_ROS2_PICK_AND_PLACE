#!/usr/bin/env python3
"""
Gripper benchmark harness — pick-and-place accuracy per gripper.

For every gripper this launches the headless sim (isolated ROS domain), runs N
pick-and-place trials with MotionExecutor, and reads the object's ground-truth
pose from Gazebo before and after each trial. Accuracy is the distance between
where the object ended up and where it should have ended up
(initial pose + (place - pick) displacement), so the world/base frame offset
doesn't matter.

Usage:
    source install/setup.bash
    python3 testing/benchmark_grippers.py --trials 5
    python3 testing/benchmark_grippers.py --grippers robotiq_2f_85 onrobot_rg2 --trials 10

    # sim already running with one gripper (no launch/teardown):
    ROS_DOMAIN_ID=77 python3 testing/benchmark_grippers.py --no-launch \
        --grippers robotiq_2f_85 --trials 5

Modes:
    default          pick at the known object coordinates (isolates gripper accuracy)
    --perception     launch with wrist_camera:=true + the colour/depth detector on the
                     /camera_wrist/* topics; the pick XY comes from /detected_objects, and
                     the detector's XY error vs Gazebo ground truth is recorded too.
                     If nothing is detected the trial falls back to the known XY and says
                     so in notes (counted as a perception miss).
    --objects ...    subset of: cube_5cm tall_box cylinder_5cm cylinder_4cm (default: all)

Grippers supported by ur.gazebo.launch.py: robotiq_2f_85, robotiq_2f_140,
onrobot_rg2, onrobot_rg6. dh_ag95 / robotiq_hande are not wired into the launch
file's `gripper` choices yet, so they are not in the default list.

Results CSV columns:
    gripper, object, trial, executed, success, error_xy_m, error_z_m,
    perception_error_xy_m, cycle_time_s, notes
Success = task list completed AND final object error_xy < --tol (default 2 cm)
AND the object actually moved.
"""

import argparse
import csv
import math
import os
import random
import re
import signal
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_GRIPPERS = ["robotiq_2f_85", "robotiq_2f_140", "onrobot_rg2", "onrobot_rg6"]

# world file, model name, base-frame z of the object's top surface (base_link is
# at world z=1.0; table top is 1.055). Objects sit at world (0.35, 0.0).
OBJECTS = {
    # cube spawns 2 cm above the table and settles: rest centre 1.08 -> top 1.105
    "cube_5cm":       dict(world="colored_blocks.world",         model="red_box",      top_z=0.105, height=0.05),
    "tall_box":       dict(world="colored_tall_box.world",       model="red_box",      top_z=0.145, height=0.09),
    "cylinder_5cm":   dict(world="colored_cylinder.world",       model="red_cylinder", top_z=0.135, height=0.08),
    "cylinder_4cm":   dict(world="colored_small_cylinder.world", model="red_cylinder", top_z=0.115, height=0.06),
}
PICK_XY = (0.35, 0.0)
PLACE_XY = (0.35, 0.20)  # drop_zone
# Perception scan pose: tool0 height and x-offset from the pick XY (camera ~0.20 m above the object top; higher is out of top-down IK reach).
YAW_SIGN = 1.0   # --yaw-sign: -1 flips the grasp yaw direction
PLACE_DZ = 0.01   # release height above the grasp height (--place-dz)
NO_YAW_ALIGN = False   # --no-yaw-align: baseline, always grasp square-on
OBJECT_YAW = 0.0   # rad, set by --object-yaw-deg: how far the object is rotated about z
SCAN_TOOL_Z = 0.35
SCAN_DX = 0.04
WORLD = "default"
OBJECT = None  # set per run by main()
POSE_TOPIC = f"/world/{WORLD}/pose/info"


def object_yaw_deg():
    """Ground-truth yaw (deg) of OBJECT about world z, or None."""
    try:
        out = subprocess.run(["gz", "topic", "-e", "-n", "1", "-t", POSE_TOPIC],
                             capture_output=True, text=True, timeout=10).stdout
    except subprocess.TimeoutExpired:
        return None
    for block in out.split("pose {"):
        if f'name: "{OBJECT}"' in block:
            q = block.split("orientation {", 1)[-1].split("}", 1)[0]
            v = {k: float(x) for k, x in re.findall(r"(\w+):\s*(-?[\d.e+-]+)", q)}
            x, y, z, w = (v.get(k, 0.0) for k in "xyzw")
            return math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
    return None


def object_pose():
    """Ground-truth (x, y, z) of OBJECT in the Gazebo world frame, or None."""
    try:
        out = subprocess.run(
            ["gz", "topic", "-e", "-n", "1", "-t", POSE_TOPIC],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except subprocess.TimeoutExpired:
        return None
    for block in out.split("pose {"):
        if f'name: "{OBJECT}"' in block:
            pos = block.split("position {", 1)[-1].split("}", 1)[0]
            vals = {k: float(v) for k, v in re.findall(r"(\w+):\s*(-?[\d.e+-]+)", pos)}
            return vals.get("x", 0.0), vals.get("y", 0.0), vals.get("z", 0.0)
    return None


class Detections:
    """Latest /detected_objects, filtered to red objects (all test objects are red)."""

    def __init__(self, node):
        from ur_interfaces.msg import DetectedObjectArray
        self.latest = None
        node.create_subscription(DetectedObjectArray, "/detected_objects", self._cb, 10)

    def _cb(self, msg):
        red = [o for o in msg.objects if o.label == "red"]
        if red:
            self.latest = (time.time(), red[0])

    def wait(self, timeout=15.0):
        """Fresh red detection (base_link frame), or None."""
        self.latest = None
        end = time.time() + timeout
        while time.time() < end:
            if self.latest:
                return self.latest[1]
            time.sleep(0.2)
        return None


def launch_sim(gripper, world, domain, settle, perception=False):
    if sim_running():
        raise RuntimeError("a gz/ros2 sim is already running -- stop it first, otherwise "
                           "ground-truth poses would come from the wrong world")
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain), GZ_VERSION="harmonic")
    cmd = ["bash", "-c",
           f"source /opt/ros/humble/setup.bash && source {REPO}/install/setup.bash && "
           f"exec ros2 launch ur_gazebo ur.gazebo.launch.py gripper:={gripper} world_file:={world} "
           f"use_gazebo_gui:=false use_rviz:=false"
           + (" wrist_camera:=true" if perception else "")]
    log = open(REPO / "logs" / f"bench_{gripper}_{world}.log", "w")
    proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT,
                            preexec_fn=os.setsid)
    time.sleep(settle)
    perc = None
    if perception:
        pcmd = ["bash", "-c",
                f"source /opt/ros/humble/setup.bash && source {REPO}/install/setup.bash && "
                "exec ros2 launch ur_perception perception.launch.py "
                "color_topic:=/camera_wrist/color/image_raw "
                "depth_topic:=/camera_wrist/depth/image_rect_raw "
                "camera_info_topic:=/camera_wrist/camera_info publish_planning_scene:=false"]
        perc = subprocess.Popen(pcmd, env=env, stdout=log, stderr=subprocess.STDOUT,
                                preexec_fn=os.setsid)
        time.sleep(10)
    return proc, perc


# Only ever match THIS workspace's gz server (its world/model paths live under REPO), so other
# ROS projects running on the machine are never touched.
GZ_PATTERN = f"gz sim .*{REPO.name}"


def sim_running():
    return subprocess.run(["pgrep", "-f", GZ_PATTERN], capture_output=True).returncode == 0


def stop_sim(procs):
    """Tear the sim down completely. A surviving gz server makes the next launch's
    ground-truth pose reads come from the OLD world, so wait until it is gone."""
    for proc in reversed([p for p in (procs or []) if p is not None]):
        for sig, wait in ((signal.SIGINT, 20), (signal.SIGKILL, 5)):
            try:
                os.killpg(os.getpgid(proc.pid), sig)
                proc.wait(timeout=wait)
                break
            except subprocess.TimeoutExpired:
                continue
            except ProcessLookupError:
                break
    for sig in ("-TERM", "-KILL"):
        if not sim_running():
            break
        subprocess.run(["pkill", sig, "-f", GZ_PATTERN], check=False)
        end = time.time() + 15
        while sim_running() and time.time() < end:
            time.sleep(0.5)
    time.sleep(3)


def reset_object(initial, tries=4):
    """Put the object back upright at its initial pose and confirm it got there."""
    if initial is None:
        return False
    req = (f'name: "{OBJECT}", position: {{x: {initial[0]}, y: {initial[1]}, z: {initial[2] + 0.005}}}, '
           'orientation: {x: 0, y: 0, z: ' + f'{math.sin(OBJECT_YAW / 2):.6f}, w: {math.cos(OBJECT_YAW / 2):.6f}' + '}')
    for _ in range(tries):
        r = subprocess.run(["gz", "service", "-s", f"/world/{WORLD}/set_pose",
                            "--reqtype", "gz.msgs.Pose", "--reptype", "gz.msgs.Boolean",
                            "--timeout", "3000", "--req", req], check=False,
                           capture_output=True, text=True)
        time.sleep(1.5)
        now = object_pose()
        print(f"[reset] rc={r.returncode} out={r.stdout.strip()!r} err={r.stderr.strip()[:120]!r} "
              f"now={now} initial={initial}", flush=True)
        if now and math.hypot(now[0] - initial[0], now[1] - initial[1]) < 0.01 \
                and abs(now[2] - initial[2]) < 0.02:
            return True
    return False


class LiftWatcher:
    """Samples the object's true height in a thread while a trial runs, to see whether it was
    really lifted off the table (not just dragged or knocked somewhere)."""

    def __init__(self):
        self.max_z = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.is_set():
            pose = object_pose()
            if pose is not None:
                self.max_z = pose[2] if self.max_z is None else max(self.max_z, pose[2])

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join(timeout=15)


class Recorder:
    """Keeps downscaled camera frames during a trial and writes one labelled strip per trial."""

    def __init__(self, node, topic, out_dir, period=0.5, keep=12):
        import numpy as np
        from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import Image
        self._np = np
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.period = period
        self.keep = keep
        self.frames = []
        self.active = False
        self._last = 0.0
        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         history=HistoryPolicy.KEEP_LAST, depth=1)
        node.create_subscription(Image, topic, self._cb, qos)

    def _cb(self, msg):
        now = time.time()
        if not self.active or now - self._last < self.period:
            return
        self._last = now
        import cv2
        # Decoded by hand: cv_bridge is built against NumPy 1.x and crashes with NumPy 2.
        img = self._np.frombuffer(msg.data, self._np.uint8).reshape(msg.height, msg.width, -1)
        if msg.encoding == "rgb8":
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        self.frames.append((now, cv2.resize(img, (320, 180))))

    def start(self):
        self.frames = []
        self.active = True

    def save(self, label, passed):
        import cv2
        self.active = False
        if not self.frames:
            return
        keep = self._np.linspace(0, len(self.frames) - 1, min(self.keep, len(self.frames))).astype(int)
        t0 = self.frames[0][0]
        tiles = []
        for i in keep:
            tt, im = self.frames[i]
            im = im.copy()
            cv2.putText(im, f"{tt - t0:.1f}s", (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            tiles.append(im)
        while len(tiles) % 4:
            tiles.append(self._np.zeros_like(tiles[0]))
        sheet = self._np.vstack([self._np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)])
        cv2.putText(sheet, f"{label}  {'PASS' if passed else 'FAIL'}", (8, sheet.shape[0] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0) if passed else (0, 0, 255), 2)
        cv2.imwrite(str(self.out_dir / f"{label}_{'PASS' if passed else 'FAIL'}.png"), sheet)


def run_trials(gripper, obj_name, top_z, trials, tol, node, ex, det=None, grasp_depth=None, height=0.05,
               jitter=0.0, recorder=None):
    rows = []
    initial = object_pose()
    if OBJECT_YAW:
        reset_object(initial)
    for t in range(1, trials + 1):
        # Move the object a few cm from the nominal spot each trial so a pass doesn't depend on
        # one lucky position (seeded, so every gripper sees the same offsets).
        off = (0.0, 0.0)
        if jitter and initial is not None:
            rng = random.Random(1000 + t)
            off = (rng.uniform(-jitter, jitter), rng.uniform(-jitter, jitter))
            reset_object((initial[0] + off[0], initial[1] + off[1], initial[2]))
        before = object_pose()
        pick_xy, perc_err, notes = (PICK_XY[0] + off[0], PICK_XY[1] + off[1]), float("nan"), ""
        pick_yaw = 0.0 if NO_YAW_ALIGN or abs(OBJECT_YAW) >= math.pi / 4 else YAW_SIGN * OBJECT_YAW
        if det is not None:
            # At "home" the wrist camera looks sideways/up, away from the table. Scan from a
            # tool-down pose instead: the camera sits (+0.06 x, -0.04 z) from tool0 and leans
            # 25 deg toward -X, so tool0 is placed ahead of the object to centre it in view.
            ex.execute_task_list([{"action": "move_to_named_pose", "pose_name": "home"}])
            if not ex.move_to_pose(ex._make_downward_pose(
                    PICK_XY[0] + SCAN_DX, PICK_XY[1], SCAN_TOOL_Z - ex._tcp_offset_z)):
                node.get_logger().warn("scan pose unreachable -- camera will not see the object")
            time.sleep(1.5)
            d = det.wait()
            if d is None:
                notes = "perception miss (used known XY)"
            else:
                pick_xy = (d.position.x, d.position.y)
                pick_yaw = 0.0 if NO_YAW_ALIGN else float(getattr(d, "yaw", 0.0))
                perc_err = math.hypot(d.position.x - PICK_XY[0], d.position.y - PICK_XY[1])
        # MotionExecutor grasps 1 cm ABOVE the z it is given, which leaves the pads barely touching
        # the top edge of the object (flaky). Grasp grasp_depth below the true top instead, and
        # release at the same height the object was held.
        depth = grasp_depth if grasp_depth is not None else min(0.03, 0.4 * height)
        pick_z = top_z - depth
        tasks = [
            {"action": "move_to_named_pose", "pose_name": "home"},
            {"action": "open_gripper"},
            {"action": "pick", "object_id": OBJECT, "object_x": pick_xy[0],
             "object_y": pick_xy[1], "object_z": pick_z, "object_yaw": pick_yaw},
            {"action": "place", "x": PLACE_XY[0], "y": PLACE_XY[1], "z": pick_z + PLACE_DZ},
            {"action": "move_to_named_pose", "pose_name": "home"},
        ]
        print(f"[obj] trial {t} start yaw={object_yaw_deg()} deg (commanded grasp yaw "
              f"{math.degrees(pick_yaw):.0f})", flush=True)
        js = ex._latest_joint_state
        if js is not None:
            state = {n: round(v, 3) for n, v in zip(js.name, js.position)}
            print(f"[state] trial {t} start: {state}", flush=True)
        t0 = time.time()
        if recorder is not None:
            recorder.start()
        with LiftWatcher() as watcher:
            executed = bool(ex.execute_task_list(tasks))
        js = ex._latest_joint_state
        if js is not None:
            print(f"[state] trial {t} end:   {({n: round(v, 3) for n, v in zip(js.name, js.position)})}",
                  flush=True)
        cycle = time.time() - t0
        after = object_pose()

        lifted = (watcher.max_z - before[2]) if (before is not None and watcher.max_z is not None) \
            else float("nan")
        ex_xy = ex_z = float("nan")
        err_dx = err_dy = float("nan")
        success = False
        if before is None or after is None:
            notes = (notes + "; " if notes else "") + "no gz pose"
        else:
            tx = before[0] + (PLACE_XY[0] - PICK_XY[0])
            ty = before[1] + (PLACE_XY[1] - PICK_XY[1])
            err_dx, err_dy = after[0] - tx, after[1] - ty
            ex_xy = math.hypot(err_dx, err_dy)
            ex_z = after[2] - before[2]
            moved = math.hypot(after[0] - before[0], after[1] - before[1]) > 0.05
            # Judge by where the object ended up. The final retreat/home move often fails with
            # CONTROL_FAILED after a good place, which must not turn a good place into a failure.
            success = moved and ex_xy < tol
            if not moved:
                notes = (notes + "; " if notes else "") + "object not moved"
        rows.append(dict(gripper=gripper, object=obj_name, trial=t, executed=executed,
                         success=success, error_xy_m=ex_xy, error_z_m=ex_z, perception_error_xy_m=perc_err,
                         cycle_time_s=cycle, lifted_m=lifted, err_dx_m=err_dx, err_dy_m=err_dy,
                         notes=notes))
        node.get_logger().info(f"{gripper}/{obj_name} trial {t}: {rows[-1]}")
        if recorder is not None:
            recorder.save(f"{gripper}_{obj_name}_t{t}", success)
        reset_object(initial)
    return rows


LIFT_MIN_M = 0.03   # the object must rise this far to count as picked (when lifted_m is recorded)


def _picked(row):
    """Strict when the object's height was tracked: it rose at least LIFT_MIN_M. Otherwise
    (older CSVs) it only had to leave its start position, which also counts dragged objects."""
    lifted = row.get("lifted_m")
    if lifted is not None and not math.isnan(lifted):
        return lifted >= LIFT_MIN_M
    return "object not moved" not in row["notes"]


def summarise(rows, grippers, objects):
    """pick = object left its start spot; place = ended within tolerance (of those picked);
    pick&place = both, i.e. the overall success rate."""
    print(f"\n{'gripper':<16}{'object':<14}{'n':>3}{'pick':>7}{'place':>7}{'pick&place':>12}"
          f"{'xy mean mm':>12}{'xy std mm':>11}{'percep mm':>11}{'cycle s':>9}")
    for g in grippers:
        for o in objects:
            r = [x for x in rows if x["gripper"] == g and x["object"] == o]
            if not r:
                continue
            picked = [x for x in r if _picked(x)]
            ok = [x for x in r if x["success"]]
            errs = [x["error_xy_m"] * 1000 for x in r if not math.isnan(x["error_xy_m"])]
            perc = [x["perception_error_xy_m"] * 1000 for x in r
                    if not math.isnan(x["perception_error_xy_m"])]
            mean = statistics.mean(errs) if errs else float("nan")
            std = statistics.pstdev(errs) if len(errs) > 1 else 0.0
            pmean = statistics.mean(perc) if perc else float("nan")
            cyc = statistics.mean(x["cycle_time_s"] for x in r)
            place = 100 * len(ok) / len(picked) if picked else float("nan")
            print(f"{g:<16}{o:<14}{len(r):>3}{100 * len(picked) / len(r):>6.0f}%{place:>6.0f}%"
                  f"{100 * len(ok) / len(r):>11.0f}%{mean:>12.1f}{std:>11.1f}{pmean:>11.1f}{cyc:>9.1f}")
    print(f"\n{'gripper':<16}{'pick':>7}{'place':>7}{'pick&place':>12}")
    for g in grippers:
        r = [x for x in rows if x["gripper"] == g]
        if r:
            picked = [x for x in r if _picked(x)]
            ok = [x for x in r if x["success"]]
            place = 100 * len(ok) / len(picked) if picked else float("nan")
            print(f"{g:<16}{100 * len(picked) / len(r):>6.0f}%{place:>6.0f}%{100 * len(ok) / len(r):>11.0f}%")


def load_rows(path):
    return load_rows_from(list(csv.DictReader(open(path))))


def load_rows_from(rows):
    for r in rows:
        for k in ("error_xy_m", "error_z_m", "perception_error_xy_m", "cycle_time_s", "lifted_m",
                  "err_dx_m", "err_dy_m"):
            r[k] = float(r[k]) if r.get(k) not in (None, "") else float("nan")
        r["trial"] = int(r["trial"])
        r["success"] = str(r["success"]) == "True"
        r["executed"] = str(r["executed"]) == "True"
    return rows


def orchestrate(args):
    """Run every (gripper, object) cell in its own fresh process.

    A single long-lived rclpy process accumulates participants/clients across sim launches and
    eventually stops getting goals accepted by move_group, so each cell gets a clean process,
    and a cell whose sim never served goals is retried in another fresh one.
    """
    out = Path(args.output or REPO / "testing" / f"benchmark_grippers_{datetime.now():%Y%m%d_%H%M%S}.csv")
    base = [sys.executable, str(Path(__file__).resolve()), "--child", "--trials", str(args.trials),
            "--tol", str(args.tol), "--domain", str(args.domain), "--settle", str(args.settle),
            "--launch-retries", "1"]
    if args.perception:
        base.append("--perception")
    if args.no_launch:
        base.append("--no-launch")
    if args.grasp_depth is not None:
        base += ["--grasp-depth", str(args.grasp_depth)]
    if args.tcp_offset is not None:
        base += ["--tcp-offset", str(args.tcp_offset)]
    if args.object_yaw_deg:
        base += ["--object-yaw-deg", str(args.object_yaw_deg)]
    if args.no_yaw_align:
        base.append("--no-yaw-align")
    if args.yaw_sign != 1.0:
        base += ["--yaw-sign", str(args.yaw_sign)]
    if args.jitter_cm:
        base += ["--jitter-cm", str(args.jitter_cm)]
    if args.record_dir:
        base += ["--record-dir", args.record_dir]
    if args.place_dz != 0.01:
        base += ["--place-dz", str(args.place_dz)]
    if args.record_topic:
        base += ["--record-topic", args.record_topic]
    if args.record_dir:
        base += ["--record-period", str(args.record_period), "--record-frames", str(args.record_frames)]
    all_rows = []
    for g in args.grippers:
        for name in args.objects:
            tmp = out.with_suffix(f".{g}.{name}.tmp.csv")
            rows = []
            for attempt in range(1, args.launch_retries + 1):
                subprocess.run(base + ["--grippers", g, "--objects", name, "--output", str(tmp)], check=False)
                rows = list(csv.DictReader(open(tmp))) if tmp.exists() else []
                if rows and not any(r["notes"] == "sim not ready" for r in rows):
                    break
                print(f"[bench] {g}/{name}: sim not ready (attempt {attempt}/{args.launch_retries})", flush=True)
            tmp.unlink(missing_ok=True)
            if not rows:
                rows = [dict(gripper=g, object=name, trial=0, executed=False, success=False,
                             error_xy_m=float("nan"), error_z_m=float("nan"),
                             perception_error_xy_m=float("nan"), cycle_time_s=0.0,
                             lifted_m=float("nan"), err_dx_m=float("nan"), err_dy_m=float("nan"),
                             notes="sim not ready")]
            all_rows += load_rows_from(rows)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)
    summarise([r for r in all_rows if r["trial"]], args.grippers, args.objects)
    print(f"\nWrote {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grippers", nargs="+", default=DEFAULT_GRIPPERS)
    ap.add_argument("--objects", nargs="+", default=list(OBJECTS), choices=list(OBJECTS))
    ap.add_argument("--perception", action="store_true",
                    help="pick at wrist-camera detections instead of known coordinates")
    ap.add_argument("--grasp-depth", type=float, default=None,
                    help="grasp this far below the object's top surface (m); "
                         "default min(3 cm, 40%% of the object's height)")
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--tol", type=float, default=0.02, help="success radius in m")
    ap.add_argument("--domain", type=int, default=77)
    ap.add_argument("--settle", type=float, default=60.0, help="seconds to wait after launch")
    ap.add_argument("--tcp-offset", type=float, default=None,
                    help="override tool0->fingertip z offset (m) for every gripper")
    ap.add_argument("--launch-retries", type=int, default=3,
                    help="relaunch the sim this many times if it never serves goals")
    ap.add_argument("--no-launch",action="store_true", help="use the already-running sim")
    ap.add_argument("--output", default=None)
    ap.add_argument("--object-yaw-deg", type=float, default=0.0,
                    help="rotate the object about z by this angle (|angle| < 45) to test yaw-aligned grasps")
    ap.add_argument("--yaw-sign", type=float, default=1.0, help="multiply the grasp yaw (use -1 to flip direction)")
    ap.add_argument("--no-yaw-align", action="store_true", help="baseline: ignore object yaw when grasping")
    ap.add_argument("--jitter-cm", type=float, default=0.0,
                    help="shift the object by up to this many cm in x and y each trial (seeded)")
    ap.add_argument("--record-topic", default=None,
                    help="camera topic for --record-dir (default: head camera, wrist camera with --perception); "
                         "/camera_wrist/color/image_raw gives a close-up of the fingers")
    ap.add_argument("--place-dz", type=float, default=0.01, help="release this far above the grasp height (m)")
    ap.add_argument("--record-period", type=float, default=0.5, help="seconds between recorded frames")
    ap.add_argument("--record-frames", type=int, default=12, help="frames kept per trial strip")
    ap.add_argument("--record-dir", default=None,
                    help="save a labelled strip of camera frames for every trial here")
    ap.add_argument("--summarise-csv", default=None,
                    help="just print the pick / place / pick&place table for an existing results CSV")
    ap.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.summarise_csv:
        rows = [r for r in load_rows(args.summarise_csv) if r["trial"]]
        summarise(rows, list(dict.fromkeys(r["gripper"] for r in rows)),
                  list(dict.fromkeys(r["object"] for r in rows)))
        return
    if not args.child:
        return orchestrate(args)

    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    import rclpy
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from ur_llm_planner.motion_executor import MotionExecutor

    out = Path(args.output or REPO / "testing" / f"benchmark_grippers_{datetime.now():%Y%m%d_%H%M%S}.csv")
    (REPO / "logs").mkdir(exist_ok=True)
    rclpy.init()
    global OBJECT, OBJECT_YAW, NO_YAW_ALIGN, YAW_SIGN, PLACE_DZ
    PLACE_DZ = args.place_dz
    OBJECT_YAW = math.radians(args.object_yaw_deg)
    NO_YAW_ALIGN = args.no_yaw_align
    YAW_SIGN = args.yaw_sign
    blank = dict(executed=False, success=False, error_xy_m=float("nan"),
                 error_z_m=float("nan"), perception_error_xy_m=float("nan"), cycle_time_s=0.0,
                 lifted_m=float("nan"), err_dx_m=float("nan"), err_dy_m=float("nan"))
    all_rows = []
    for g in args.grippers:
        for name in args.objects:
            obj = OBJECTS[name]
            OBJECT = obj["model"]
            # A launch sometimes comes up with controllers/move_group not actually serving
            # goals (action servers discovered, but goals time out). Probe with a home move
            # and relaunch from scratch instead of recording a bogus 0%.
            rows_for_cell = None
            for attempt in range(1, args.launch_retries + 1):
                procs = None if args.no_launch else launch_sim(
                    g, obj["world"], args.domain, args.settle, args.perception)
                # Fresh node + MotionExecutor per sim launch: each launch restarts the sim
                # clock, and a TF buffer kept from the previous launch rejects all new
                # transforms as TF_OLD_DATA.
                node = Node("benchmark_grippers")
                executor = SingleThreadedExecutor()
                executor.add_node(node)
                threading.Thread(target=executor.spin, daemon=True).start()
                try:
                    ex = MotionExecutor(node)
                    ex.set_gripper(g)
                    if args.tcp_offset is not None:
                        ex._tcp_offset_z = args.tcp_offset
                    det = Detections(node) if args.perception else None
                    ready = ex.wait_for_servers(timeout=60.0) and bool(
                        ex.execute_task_list([{"action": "move_to_named_pose", "pose_name": "home"}]))
                    if not ready:
                        node.get_logger().error(
                            f"{g}/{name}: sim not serving goals (attempt {attempt}/{args.launch_retries})")
                        continue
                    recorder = Recorder(
                        node, args.record_topic or ("/camera_wrist/color/image_raw" if args.perception
                                                    else "/camera_head/color/image_raw"),
                        args.record_dir, args.record_period, args.record_frames) if args.record_dir else None
                    rows_for_cell = run_trials(g, name, obj["top_z"], args.trials, args.tol, node, ex,
                                               det, args.grasp_depth, obj["height"],
                                               jitter=args.jitter_cm / 100.0, recorder=recorder)
                    break
                finally:
                    stop_sim(procs)
                    executor.shutdown()
                    node.destroy_node()
            if rows_for_cell is None:
                all_rows.append(dict(gripper=g, object=name, trial=0, notes="sim not ready", **blank))
            else:
                all_rows += rows_for_cell

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)
    summarise([r for r in all_rows if r["trial"]], args.grippers, args.objects)
    print(f"\nWrote {out}")
    rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())

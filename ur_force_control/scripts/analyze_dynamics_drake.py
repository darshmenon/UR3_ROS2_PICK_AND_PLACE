#!/usr/bin/env python3
"""Drake reference dynamics for UR3 — independent cross-check of the Pinocchio
gravity/torque math used by joint_impedance_controller.cpp.

Runs outside ROS/Gazebo (CPU only, no launch needed) so it can be used as a
static ground truth: run this, then diff its printed g(q) and torque envelope
against the controller's own `debug_logging_` output (gravity=[...] lines)
captured from a real run, or against /joint_states effort, without needing to
re-launch the sim to iterate.

Loads the resolved UR3 URDF (ur_description/urdf/ur_robot.urdf) into Drake's
MultibodyPlant and computes:
  1. Gravity torque g(q) at the arm's home pose (initial_positions.yaml)
  2. Inverse-dynamics torque envelope tau = M*qdd + C*qd - g(q) along a small
     trajectory around home, checked against the controller's actual effort
     limits (56, 56, 28, 12, 12, 12 N.m from joint_impedance.launch.py)
  3. The controller's own impedance law -- tau = Kp*(q_des-q) + Kd*(0-qdot) +
     g(q) using its actual default gains -- to sanity-check gain headroom
     before touching real hardware/Gazebo.

Note on sign: the controller subtracts g(q) (see joint_impedance_controller.cpp
and the project's `impedance_gravity_sign_fix` note) -- that is an empirically
-fixed Gazebo/Pinocchio effort-interface convention, not something this script
re-derives. This script reports Drake's g(q) in Drake's own convention
(tau = M*qdd + C*qd + g(q) with g(q) = -CalcGravityGeneralizedForces, i.e. the
torque needed to HOLD the pose against gravity) so it can be compared by
magnitude/pattern against the controller's logged gravity(...) values, not
blindly substituted in with the same sign.

Note on geometry: <visual>/<collision>/<transmission> are stripped from the
URDF before parsing (see strip_geometry) -- Drake's mesh loader rejects the
gripper's STL collision meshes and some <transmission> blocks reference
gripper joint names that don't exist as <joint> elements. Dynamics only needs
<inertial>, so nothing this script computes is affected.

Usage
-----
    # Synthetic sinusoid around home (default)
    .venv312/bin/python3 ur_force_control/scripts/analyze_dynamics_drake.py

    # Real recorded pick-place episodes instead of a synthetic trajectory
    .venv312/bin/python3 ur_force_control/scripts/analyze_dynamics_drake.py \
        --dataset datasets/ur3_pickplace_v0

In --dataset mode, qd/qdd come from finite-differencing the recorded 5 Hz
observation.state trajectory, which is coarse and tends to smooth over fast
within-frame motion -- treat the inverse-dynamics numbers there as a lower
bound, not a tight peak. The gravity-hold numbers are exact regardless of
sample rate (they don't depend on qd/qdd at all).
"""

from __future__ import annotations

import argparse
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pydrake.all import AddMultibodyPlantSceneGraph, DiagramBuilder, Parser

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
DEFAULT_URDF = REPO_ROOT / "ur_description" / "urdf" / "ur_robot.urdf"

# Must match joint_impedance_controller.cpp's declared defaults exactly.
JOINT_NAMES = [
    "shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
    "wrist_1_joint", "wrist_2_joint", "wrist_3_joint",
]
STIFFNESS = np.array([80.0, 80.0, 60.0, 15.0, 15.0, 15.0])
DAMPING = np.array([8.0, 8.0, 6.0, 1.5, 1.5, 1.5])
MAX_TAU = np.array([56.0, 56.0, 28.0, 12.0, 12.0, 12.0])

# moveit_config/config/initial_positions.yaml
Q_HOME = np.array([-0.1, -1.6315, 0.0, 1.8251, 0.0, 1.2844])

AMP = np.array([0.15, 0.10, 0.12, 0.20, 0.20, 0.20])
FREQ = np.array([0.25, 0.30, 0.28, 0.35, 0.32, 0.40])
HZ, T = 50.0, 4.0
N = int(T * HZ)


def strip_geometry(urdf_path: Path) -> Path:
    """Drop <visual>/<collision> (mesh files Drake's parser chokes on -- STL
    isn't supported for convex-hull proximity, DAE isn't supported at all).
    Dynamics only needs <inertial>, so this loses nothing we use."""
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    for link in root.findall("link"):
        for tag in ("visual", "collision"):
            for el in link.findall(tag):
                link.remove(el)
    # <transmission> blocks (ros2_control) aren't used for MultibodyPlant
    # dynamics and some reference joint names that don't round-trip cleanly
    # through xacro on the gripper -- drop them too.
    for el in root.findall("transmission"):
        root.remove(el)
    tmp = Path(tempfile.mkstemp(suffix=".urdf")[1])
    tree.write(tmp)
    return tmp


class DrakeArm:
    """Thin wrapper around a Drake MultibodyPlant for the 6 UR3 arm joints."""

    def __init__(self, urdf_path: Path):
        builder = DiagramBuilder()
        self.plant, _ = AddMultibodyPlantSceneGraph(builder, time_step=0.0)
        parser = Parser(self.plant)
        parser.AddModels(str(strip_geometry(urdf_path)))
        self.plant.Finalize()
        diagram = builder.Build()
        context = diagram.CreateDefaultContext()
        self.ctx = self.plant.GetMyContextFromRoot(context)
        self.vel_starts = [self.plant.GetJointByName(n).velocity_start() for n in JOINT_NAMES]
        self.pos_starts = [self.plant.GetJointByName(n).position_start() for n in JOINT_NAMES]

    def set_q(self, q6: np.ndarray):
        q = self.plant.GetPositions(self.ctx).copy()
        for s, qi in zip(self.pos_starts, q6):
            q[s] = qi
        self.plant.SetPositions(self.ctx, q)

    def gravity_hold_torque(self, q6: np.ndarray) -> np.ndarray:
        """tau needed to hold q6 against gravity (Drake sign convention)."""
        self.set_q(q6)
        g = self.plant.CalcGravityGeneralizedForces(self.ctx)
        return -np.array([g[s] for s in self.vel_starts])

    def inverse_dynamics(self, q6, qd6, qdd6) -> np.ndarray:
        """tau = M*qdd + C*qd - g(q), i.e. actuator torque to realize qdd."""
        self.set_q(q6)
        v = np.zeros(self.plant.num_velocities())
        vd = np.zeros(self.plant.num_velocities())
        for s, qdi, qddi in zip(self.vel_starts, qd6, qdd6):
            v[s] = qdi
            vd[s] = qddi
        self.plant.SetVelocities(self.ctx, v)
        M = self.plant.CalcMassMatrix(self.ctx)
        Cv = self.plant.CalcBiasTerm(self.ctx)
        g = self.plant.CalcGravityGeneralizedForces(self.ctx)
        tau_full = M @ vd + Cv - g
        return np.array([tau_full[s] for s in self.vel_starts])


def load_dataset_episodes(dataset_root: Path, episode_indices=None):
    """Read a LeRobotDataset's parquet shards and return {episode_index: (t, q)}
    for the 6 arm joints, in JOINT_NAMES order."""
    import pandas as pd

    info = json.loads((dataset_root / "meta" / "info.json").read_text())
    state_names = info["features"]["observation.state"]["names"][0]
    if state_names[:6] != JOINT_NAMES:
        raise SystemExit(
            f"observation.state joint order {state_names[:6]} doesn't match "
            f"this script's JOINT_NAMES {JOINT_NAMES} -- fix the mapping "
            "before trusting these numbers."
        )

    parquet_files = sorted((dataset_root / "data").glob("chunk-*/*.parquet"))
    if not parquet_files:
        raise SystemExit(f"No parquet files under {dataset_root}/data/")
    df = pd.concat([pd.read_parquet(p) for p in parquet_files], ignore_index=True)

    episodes = {}
    for ep in sorted(df["episode_index"].unique()):
        if episode_indices is not None and ep not in episode_indices:
            continue
        sub = df[df["episode_index"] == ep].sort_values("frame_index")
        t = sub["timestamp"].to_numpy(dtype=float)
        q = np.stack(sub["observation.state"].to_numpy())[:, :6].astype(float)
        episodes[int(ep)] = (t, q)
    return episodes


def run_synthetic(arm: DrakeArm, urdf_path: Path):
    g_home = arm.gravity_hold_torque(Q_HOME)
    print(f"Drake gravity-hold torque @ home: {np.round(g_home, 2)} N.m "
          f"(|g|={np.linalg.norm(g_home):.1f})")

    t = np.arange(N) / HZ
    q = Q_HOME + AMP * np.sin(2 * np.pi * FREQ * t[:, None])
    qd = AMP * (2 * np.pi * FREQ) * np.cos(2 * np.pi * FREQ * t[:, None])
    qdd = -AMP * (2 * np.pi * FREQ) ** 2 * np.sin(2 * np.pi * FREQ * t[:, None])

    tau_id = np.zeros((N, 6))
    tau_ctrl = np.zeros((N, 6))
    for i in range(N):
        tau_id[i] = arm.inverse_dynamics(q[i], qd[i], qdd[i])
        # Controller's own law: track q[i] from Q_HOME with zero qd target.
        g_i = arm.gravity_hold_torque(q[i])
        tau_ctrl[i] = STIFFNESS * (q[i] - Q_HOME) + DAMPING * (0 - qd[i]) + g_i

    peak_id = np.max(np.abs(tau_id), axis=0)
    rms_id = np.sqrt(np.mean(tau_id**2, axis=0))
    peak_ctrl = np.max(np.abs(tau_ctrl), axis=0)

    print("\n-- Inverse-dynamics envelope (independent of controller gains) --")
    print("peak |tau|:", np.round(peak_id, 1))
    print("rms  tau  :", np.round(rms_id, 1))
    print("limits    :", MAX_TAU)
    print("within limits?", bool(np.all(peak_id <= MAX_TAU + 1e-6)))

    print("\n-- Controller law (Kp/Kd + g) with actual launch-file gains --")
    print("peak |tau|:", np.round(peak_ctrl, 1))
    print("limits    :", MAX_TAU)
    margin = MAX_TAU - peak_ctrl
    print("margin    :", np.round(margin, 1))
    if np.any(margin < 0):
        print("WARNING: controller law exceeds effort limits on:",
              [JOINT_NAMES[i] for i in np.where(margin < 0)[0]])
    else:
        print("within limits, all joints")

    report = {
        "backend": "drake",
        "urdf": str(urdf_path),
        "joint_names": JOINT_NAMES,
        "q_home": Q_HOME.tolist(),
        "gravity_hold_home_Nm": g_home.tolist(),
        "id_peak_tau_Nm": peak_id.tolist(),
        "id_rms_tau_Nm": rms_id.tolist(),
        "controller_peak_tau_Nm": peak_ctrl.tolist(),
        "effort_limits_Nm": MAX_TAU.tolist(),
        "stiffness": STIFFNESS.tolist(),
        "damping": DAMPING.tolist(),
        "id_within_limits": bool(np.all(peak_id <= MAX_TAU + 1e-6)),
        "controller_within_limits": bool(np.all(peak_ctrl <= MAX_TAU + 1e-6)),
    }
    with open(OUT_DIR / "drake_dynamics_report.json", "w") as f:
        json.dump(report, f, indent=2)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    fig.suptitle("Drake UR3 reference — gravity / inverse dynamics / controller law")

    ax = axes[0, 0]
    for j, name in enumerate(JOINT_NAMES):
        ax.plot(t, tau_id[:, j], label=name)
    ax.set_title("Inverse-dynamics tau(t)")
    ax.set_ylabel("N.m")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)

    ax = axes[0, 1]
    x = np.arange(6)
    ax.bar(x - 0.2, peak_id, 0.4, label="peak ID")
    ax.bar(x + 0.2, peak_ctrl, 0.4, label="peak controller law")
    ax.plot(x, MAX_TAU, "k--", label="limit")
    ax.set_xticks(x)
    ax.set_xticklabels([f"J{i+1}" for i in range(6)])
    ax.set_title("Torque envelope vs effort limits")
    ax.set_ylabel("N.m")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)

    ax = axes[1, 0]
    ax.bar(np.arange(6), g_home)
    ax.set_xticks(np.arange(6))
    ax.set_xticklabels([f"J{i+1}" for i in range(6)])
    ax.set_title("Gravity-hold torque @ home")
    ax.set_ylabel("N.m")
    ax.grid(True, axis="y", alpha=0.3)

    ax = axes[1, 1]
    for j, name in enumerate(JOINT_NAMES):
        ax.plot(t, tau_ctrl[:, j], label=name)
    ax.set_title("Controller law tau(t) (Kp/Kd + g, launch-file gains)")
    ax.set_ylabel("N.m")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)

    fig.savefig(OUT_DIR / "drake_dynamics_analysis.png", dpi=160)
    print(f"\nSaved {OUT_DIR/'drake_dynamics_analysis.png'}")
    print(f"Saved {OUT_DIR/'drake_dynamics_report.json'}")


def run_dataset(arm: DrakeArm, urdf_path: Path, dataset_root: Path, episode_indices):
    print(f"Loading dataset {dataset_root}")
    episodes = load_dataset_episodes(dataset_root, episode_indices)
    if not episodes:
        raise SystemExit("No matching episodes found.")
    print(f"episodes: {sorted(episodes)}")
    print("NOTE: qd/qdd are finite-differenced from 5 Hz recorded frames -- "
          "coarse, treat inverse-dynamics peaks as a lower bound. Gravity-hold "
          "numbers are exact regardless of sample rate.")

    per_episode = {}
    combined_peak_g = np.zeros(6)
    combined_peak_id = np.zeros(6)

    for ep, (t, q) in episodes.items():
        qd = np.gradient(q, t, axis=0)
        qdd = np.gradient(qd, t, axis=0)

        tau_g = np.array([arm.gravity_hold_torque(qi) for qi in q])
        tau_id = np.array([
            arm.inverse_dynamics(q[i], qd[i], qdd[i]) for i in range(len(t))
        ])

        peak_g = np.max(np.abs(tau_g), axis=0)
        peak_id = np.max(np.abs(tau_id), axis=0)
        combined_peak_g = np.maximum(combined_peak_g, peak_g)
        combined_peak_id = np.maximum(combined_peak_id, peak_id)

        print(f"\n-- episode {ep} ({len(t)} frames, {t[-1]-t[0]:.1f}s) --")
        print("peak gravity-hold |tau|:", np.round(peak_g, 1))
        print("peak ID            |tau|:", np.round(peak_id, 1))

        per_episode[ep] = {
            "n_frames": len(t),
            "duration_s": float(t[-1] - t[0]),
            "peak_gravity_hold_Nm": peak_g.tolist(),
            "peak_id_Nm": peak_id.tolist(),
            "t": t.tolist(),
            "tau_gravity_hold_Nm": tau_g.tolist(),
            "tau_id_Nm": tau_id.tolist(),
        }

    print("\n-- combined worst case across all episodes --")
    print("peak gravity-hold |tau|:", np.round(combined_peak_g, 1))
    print("peak ID            |tau|:", np.round(combined_peak_id, 1))
    print("limits                  :", MAX_TAU)
    margin = MAX_TAU - combined_peak_id
    print("margin                  :", np.round(margin, 1))
    if np.any(margin < 0):
        print("WARNING: real recorded motion exceeds effort limits on:",
              [JOINT_NAMES[i] for i in np.where(margin < 0)[0]])
    else:
        print("within limits, all joints")

    report = {
        "backend": "drake",
        "mode": "dataset",
        "urdf": str(urdf_path),
        "dataset": str(dataset_root),
        "joint_names": JOINT_NAMES,
        "effort_limits_Nm": MAX_TAU.tolist(),
        "combined_peak_gravity_hold_Nm": combined_peak_g.tolist(),
        "combined_peak_id_Nm": combined_peak_id.tolist(),
        "within_limits": bool(np.all(combined_peak_id <= MAX_TAU + 1e-6)),
        "episodes": per_episode,
    }
    with open(OUT_DIR / "drake_dynamics_dataset_report.json", "w") as f:
        json.dump(report, f, indent=2)

    n_ep = len(episodes)
    fig, axes = plt.subplots(n_ep + 1, 1, figsize=(10, 3.2 * (n_ep + 1)),
                              constrained_layout=True)
    if n_ep == 0:
        axes = [axes]
    fig.suptitle("Drake UR3 — real recorded pick-place episodes")

    for row, (ep, (t, q)) in enumerate(episodes.items()):
        ax = axes[row]
        tau_id = np.array(per_episode[ep]["tau_id_Nm"])
        for j, name in enumerate(JOINT_NAMES):
            ax.plot(t, tau_id[:, j], label=name)
        for j in range(6):
            ax.axhline(MAX_TAU[j], color="k", ls="--", lw=0.5, alpha=0.4)
        ax.set_title(f"episode {ep} — inverse-dynamics tau(t)")
        ax.set_ylabel("N.m")
        ax.legend(fontsize=6, ncol=3)
        ax.grid(True, alpha=0.3)

    ax = axes[-1]
    x = np.arange(6)
    ax.bar(x - 0.2, combined_peak_g, 0.4, label="peak gravity-hold")
    ax.bar(x + 0.2, combined_peak_id, 0.4, label="peak ID")
    ax.plot(x, MAX_TAU, "k--", label="limit")
    ax.set_xticks(x)
    ax.set_xticklabels([f"J{i+1}" for i in range(6)])
    ax.set_title("Combined worst case vs effort limits")
    ax.set_ylabel("N.m")
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)

    fig.savefig(OUT_DIR / "drake_dynamics_dataset_analysis.png", dpi=160)
    print(f"\nSaved {OUT_DIR/'drake_dynamics_dataset_analysis.png'}")
    print(f"Saved {OUT_DIR/'drake_dynamics_dataset_report.json'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--urdf", type=Path, default=DEFAULT_URDF)
    ap.add_argument(
        "--dataset", type=Path, default=None,
        help="LeRobotDataset root (e.g. datasets/ur3_pickplace_v0) -- use "
        "real recorded episodes instead of a synthetic trajectory.")
    ap.add_argument(
        "--episode", type=int, action="append", default=None,
        help="Restrict --dataset mode to this episode index (repeatable). "
        "Default: all episodes.")
    args = ap.parse_args()

    if not args.urdf.is_file():
        raise SystemExit(
            f"URDF not found: {args.urdf}\n"
            "Run `colcon build` first (ur_robot.urdf is xacro-generated), "
            "or pass --urdf explicitly."
        )

    print(f"Loading {args.urdf}")
    arm = DrakeArm(args.urdf)
    print("arm joints:", JOINT_NAMES)

    if args.dataset is not None:
        run_dataset(arm, args.urdf, args.dataset, args.episode)
    else:
        run_synthetic(arm, args.urdf)


if __name__ == "__main__":
    main()

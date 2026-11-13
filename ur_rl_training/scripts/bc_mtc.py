"""Behaviour cloning on the MTC pick-and-place demos recorded in Gazebo (testing/benchmark_mtc.py --demo-dir).

Per 0.2 s step: observation = arm joints (6) + gripper joint + object position (Gazebo truth); action = the change in
arm joints and gripper over the next step. Trains on most demos and reports, on the held-out demos, the one-step error
against a "do nothing" baseline and the joint error after a closed-loop rollout from the start pose
(object position and gripper taken from the demo). It cannot run the policy in Gazebo; this is the offline check.

Run from ur_rl_training/:
    python3 scripts/bc_mtc.py --demos ~/ur3_rl_demos/mtc --out ~/ur3_rl_demos/mtc_bc.pt
"""
import argparse
import glob
from pathlib import Path

import numpy as np
import torch

ARM = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
DT = 0.2


def load(path):
    d = np.load(path)
    names = list(d["joints"])
    cols = [names.index(j) for j in ARM + ["finger_joint"]]
    t, q = d["t"], d["q"][:, cols]
    ot, obj = d["obj"][:, 0], d["obj"][:, 1:4]
    grid = np.arange(t[0], t[-1], DT)
    qs = np.stack([np.interp(grid, t, q[:, i]) for i in range(q.shape[1])], 1)
    os_ = np.stack([np.interp(grid, ot, obj[:, i]) for i in range(3)], 1)
    return qs.astype(np.float32), os_.astype(np.float32)


def samples(demos):
    x, y = [], []
    for q, o in demos:
        x.append(np.concatenate([q[:-1], o[:-1]], 1))
        y.append(q[1:] - q[:-1])
    return np.concatenate(x), np.concatenate(y)


def mlp(i, o):
    return torch.nn.Sequential(torch.nn.Linear(i, 256), torch.nn.ReLU(), torch.nn.Linear(256, 256),
                               torch.nn.ReLU(), torch.nn.Linear(256, o))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demos", default=str(Path.home() / "ur3_rl_demos" / "mtc"))
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--holdout", type=float, default=0.2)
    ap.add_argument("--out", default=str(Path.home() / "ur3_rl_demos" / "mtc_bc.pt"))
    args = ap.parse_args()
    torch.set_num_threads(2)
    torch.manual_seed(0)
    files = sorted(glob.glob(str(Path(args.demos).expanduser() / "*.npz")))
    demos = [load(f) for f in files]
    n_val = max(1, int(len(demos) * args.holdout))
    rng = np.random.default_rng(0)
    order = rng.permutation(len(demos))
    val = [demos[i] for i in order[:n_val]]
    tr = [demos[i] for i in order[n_val:]]
    x, y = samples(tr)
    xv, yv = samples(val)
    mean, std = x.mean(0), x.std(0) + 1e-6
    ysd = y.std(0) + 1e-6
    net = mlp(x.shape[1], y.shape[1])
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    X, Y = torch.as_tensor((x - mean) / std), torch.as_tensor(y / ysd)
    for ep in range(args.epochs):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 256):
            idx = perm[i:i + 256]
            loss = torch.nn.functional.mse_loss(net(X[idx]), Y[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
    with torch.no_grad():
        pred = net(torch.as_tensor((xv - mean) / std)).numpy() * ysd
    print(f"{len(files)} demos ({len(tr)} train / {len(val)} held out), {len(x):,} training steps")
    print(f"one-step joint-change MSE on held-out demos: {np.mean((pred - yv) ** 2):.2e} "
          f"(do-nothing baseline {np.mean(yv ** 2):.2e}; ratio {np.mean((pred - yv) ** 2) / np.mean(yv ** 2):.2f})")
    errs = []
    for q, o in val:                                   # closed loop from the start pose, object/gripper from the demo
        cur = q[0].copy()
        for k in range(len(q) - 1):
            a = net(torch.as_tensor((np.concatenate([cur, o[k]]) - mean) / std)[None].float()).detach().numpy()[0] * ysd
            cur = cur + a
            cur[6] = q[k + 1][6]
        errs.append(np.abs(cur[:6] - q[-1][:6]).max())
    print(f"closed-loop final arm-joint error on held-out demos: mean {np.mean(errs):.2f} rad, max {np.max(errs):.2f} rad")
    torch.save({"net": net.state_dict(), "mean": mean, "std": std, "ysd": ysd}, args.out)
    print("saved", args.out)


if __name__ == "__main__":
    main()

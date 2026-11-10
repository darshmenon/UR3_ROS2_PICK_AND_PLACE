"""UR3 peg-in-hole with Cartesian impedance control; plots peg/hole contact forces.

Run with a python that has mujoco + matplotlib:
  python3 scripts/peg_in_hole_impedance.py
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
from ur_force_control.peg_in_hole_env import PegInHole

env = PegInHole()
cases = [(200.0, 0.0004), (800.0, 0.0004), (3000.0, 0.0004), (800.0, 0.0015)]
runs = []
for k, off in cases:
    r = env.run(k_lin=k, lateral_offset=(off, 0.0), t_end=9.0)
    r["label"] = f"K={k:.0f} N/m, offset={off*1e3:.1f} mm"
    runs.append(r)
    print(f"{r['label']}: inserted={r['inserted']} depth={r['depth'].max()*1e3:.1f} mm "
          f"peak wall={r['wall'].max():.1f} N peak axial={r['axial'].max():.1f} N")

fig, ax = plt.subplots(4, 1, figsize=(9, 11), sharex=True)
for r in runs:
    for a, key, sc in zip(ax, ("depth", "axial", "wall", "total"), (1e3, 1, 1, 1)):
        a.plot(r["t"], r[key] * sc, label=r["label"])
for a, y in zip(ax, ["insertion depth (mm)", "axial force on top/floor (N)",
                     "lateral wall force (N)", "total contact force (N)"]):
    a.set_ylabel(y); a.grid(alpha=.3)
ax[0].legend(fontsize=8); ax[3].set_xlabel("time (s)")
fig.suptitle("UR3 peg-in-hole, Cartesian impedance control: contact forces")
fig.tight_layout()
out = os.path.join(here, "peg_in_hole_forces_ur3.png")
fig.savefig(out, dpi=130); print("saved", out)

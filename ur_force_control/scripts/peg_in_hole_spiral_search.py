"""Jammed peg-in-hole: plain impedance descent vs. force-triggered spiral search. Plots contact forces."""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
from ur_force_control.peg_in_hole_env import PegInHole

ARM = "UR3"
env = PegInHole()
cases = [(0.0015, False), (0.0015, True), (0.0025, True), (0.004, True)]
fig, ax = plt.subplots(4, 1, figsize=(9, 11), sharex=True)
for off, se in cases:
    r = env.run(k_lin=800.0, lateral_offset=(off, 0.0), t_end=18.0, search=se, r_max=0.006)
    lab = f"offset={off*1e3:.1f} mm, {'spiral search' if se else 'plain descent'}"
    print(f"{lab}: inserted={r['inserted']} peak axial={r['axial'].max():.1f} N peak wall={r['wall'].max():.1f} N")
    for a, key, sc in zip(ax, ("depth", "axial", "wall", "total"), (1e3, 1, 1, 1)):
        a.plot(r["t"], r[key] * sc, label=lab)
for a, y in zip(ax, ["insertion depth (mm)", "axial force (N)", "lateral wall force (N)", "total contact force (N)"]):
    a.set_ylabel(y); a.grid(alpha=.3)
ax[0].legend(fontsize=8); ax[3].set_xlabel("time (s)")
fig.suptitle(f"{ARM} peg-in-hole: impedance control, plain vs spiral search")
fig.tight_layout()
out = os.path.join(here, "..", "..", "results", "peg_in_hole_spiral_search.png") if ARM == "UR5e" \
    else os.path.join(here, f"peg_in_hole_spiral_search_{ARM.lower()}.png")
fig.savefig(out, dpi=130); print("saved", os.path.abspath(out))

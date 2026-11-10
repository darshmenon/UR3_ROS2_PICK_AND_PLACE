"""UR3 (or any UR) peg-in-hole in MuJoCo with a Cartesian impedance controller.

Torque control: tau = J^T [K (x_des - x) - D xdot] + gravity comp.
Logs peg/hole contact forces split by surface (hole wall vs. fixture top face).
"""
import os
import numpy as np
import mujoco

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_UR5E_XML = os.path.join(_REPO, "ur_rl_training", "models", "ur3", "ur3.xml")  # default arm: UR3

PEG_R = 0.010
PEG_LEN = 0.06
HOLE_HALF = 0.0105          # half-width of the square hole -> 0.5 mm clearance per side
HOLE_DEPTH = 0.03
HOLE_POS = np.array([0.28, 0.14, 0.12])   # top-face centre of the fixture


def build_model(arm_xml=_UR5E_XML, hole_pos=HOLE_POS):
    spec = mujoco.MjSpec.from_file(arm_xml)
    for act in list(spec.actuators):            # torque-controlled via qfrc_applied
        spec.delete(act)
    for key in list(spec.keys):
        spec.delete(key)
    spec.option.timestep = 0.002

    site = [s for s in spec.sites if s.name == "attachment_site"][0]
    # peg is a child of the wrist body so it moves with the flange
    wrist = site.parent
    peg = wrist.add_body(name="peg", pos=site.pos, quat=site.quat)
    g = peg.add_geom(name="peg_geom", type=mujoco.mjtGeom.mjGEOM_CYLINDER,
                     size=[PEG_R, PEG_LEN / 2, 0], pos=[0, 0, PEG_LEN / 2],
                     rgba=[0.9, 0.5, 0.1, 1], mass=0.1, friction=[0.5, 0.005, 0.0001])
    g.contype, g.conaffinity = 1, 1
    peg.add_site(name="peg_tip", pos=[0, 0, PEG_LEN], size=[0.002] * 3)
    for gm in peg.geoms:
        gm.condim = 3

    # peg must only collide with the fixture, never with the arm's own links
    for b in list(spec.bodies):
        if b.name not in ("world", "peg", "fixture"):
            ex = spec.add_exclude()
            ex.bodyname1, ex.bodyname2 = "peg", b.name

    # fixture: four walls forming a square hole, plus a base plate
    fx = spec.worldbody.add_body(name="fixture", pos=list(hole_pos))
    w = 0.02
    t = HOLE_HALF
    walls = {
        "wall_px": ([t + w / 2, 0, -HOLE_DEPTH / 2], [w / 2, t + w, HOLE_DEPTH / 2]),
        "wall_nx": ([-t - w / 2, 0, -HOLE_DEPTH / 2], [w / 2, t + w, HOLE_DEPTH / 2]),
        "wall_py": ([0, t + w / 2, -HOLE_DEPTH / 2], [t, w / 2, HOLE_DEPTH / 2]),
        "wall_ny": ([0, -t - w / 2, -HOLE_DEPTH / 2], [t, w / 2, HOLE_DEPTH / 2]),
        "hole_floor": ([0, 0, -HOLE_DEPTH - 0.005], [t + w, t + w, 0.005]),
    }
    for name, (p, s) in walls.items():
        fx.add_geom(name=name, type=mujoco.mjtGeom.mjGEOM_BOX, pos=p, size=s,
                    rgba=[0.3, 0.4, 0.8, 1], friction=[0.5, 0.005, 0.0001])
    fx.add_geom(name="support", type=mujoco.mjtGeom.mjGEOM_BOX,
                pos=[0, 0, -HOLE_DEPTH - 0.1], size=[0.06, 0.06, 0.09 - 0.0], rgba=[0.5, 0.5, 0.5, 1],
                contype=0, conaffinity=0)
    return spec.compile()


class PegInHole:
    def __init__(self, arm_xml=_UR5E_XML, hole_pos=HOLE_POS):
        self.hole_pos = np.asarray(hole_pos, dtype=float)
        self.m = build_model(arm_xml, self.hole_pos)
        self.d = mujoco.MjData(self.m)
        self.site = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_SITE, "peg_tip")
        self.peg_gid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_GEOM, "peg_geom")
        self.fix_bid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, "fixture")
        self.wall_ids = {mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_GEOM, n)
                         for n in ("wall_px", "wall_nx", "wall_py", "wall_ny")}
        self.floor_id = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_GEOM, "hole_floor")
        self.R_des = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1.0]])  # tool z pointing down
        self.nv = 6
        self.seed_q = self._find_seed()

    def _find_seed(self, tries=300):
        """Collision-free, joint-wrapped, tool-down posture above the hole (closest to elbow-up)."""
        rng = np.random.default_rng(1)
        tgt = self.hole_pos + np.array([0, 0, 0.03])
        nice = np.array([-1.0, -1.6, 1.8, -1.8, -1.57, 0.0])
        best = None
        for _ in range(tries):
            q = np.array([rng.uniform(-3, 0.5), rng.uniform(-2.3, -0.6), rng.uniform(0.6, 2.4),
                          rng.uniform(-3, 0), rng.uniform(-2, -1.2), rng.uniform(-1, 1)])
            mujoco.mj_resetData(self.m, self.d)
            self.d.qpos[:6] = q
            self.ik(tgt)
            qw = (self.d.qpos[:6] + np.pi) % (2 * np.pi) - np.pi
            self.d.qpos[:6] = qw
            mujoco.mj_forward(self.m, self.d)
            err = np.linalg.norm(np.concatenate([tgt - self.tip(), self._rot_err()]))
            if err < 1e-3 and self.d.ncon == 0:
                sc = np.linalg.norm(qw - nice)
                if best is None or sc < best[0]:
                    best = (sc, qw.copy())
        if best is None:
            raise RuntimeError("no collision-free tool-down IK solution; move the hole closer/farther")
        return best[1]

    # ---- kinematics -------------------------------------------------------
    def _jac(self):
        jp = np.zeros((3, self.m.nv)); jr = np.zeros((3, self.m.nv))
        mujoco.mj_jacSite(self.m, self.d, jp, jr, self.site)
        return np.vstack([jp, jr])[:, :self.nv]

    def tip(self):
        return self.d.site_xpos[self.site].copy()

    def ik(self, pos, iters=400):
        for _ in range(iters):
            mujoco.mj_forward(self.m, self.d)
            e = np.concatenate([pos - self.tip(), self._rot_err()])
            if np.linalg.norm(e) < 1e-5:
                break
            J = self._jac()
            dq = J.T @ np.linalg.solve(J @ J.T + 1e-4 * np.eye(6), e)
            self.d.qpos[:self.nv] += 0.5 * dq
        mujoco.mj_forward(self.m, self.d)

    def _rot_err(self):
        R = self.d.site_xmat[self.site].reshape(3, 3)
        Re = self.R_des @ R.T
        return 0.5 * np.array([Re[2, 1] - Re[1, 2], Re[0, 2] - Re[2, 0], Re[1, 0] - Re[0, 1]])

    # ---- contact forces ---------------------------------------------------
    def contact_forces(self):
        """Return (wall_lateral_N, axial_N, total_N) peg-vs-fixture."""
        f6 = np.zeros(6)
        wall = axial = 0.0
        for i in range(self.d.ncon):
            c = self.d.contact[i]
            if self.peg_gid not in (c.geom1, c.geom2):
                continue
            other = c.geom2 if c.geom1 == self.peg_gid else c.geom1
            if self.m.geom_bodyid[other] != self.fix_bid:
                continue
            mujoco.mj_contactForce(self.m, self.d, i, f6)
            frame = c.frame.reshape(3, 3)
            fw = frame.T @ f6[:3]                      # world-frame force on geom2
            if c.geom1 != self.peg_gid:                # sign so force acts on the peg
                fw = -fw
            if other in self.wall_ids:
                wall += np.linalg.norm(fw[:2])
            axial += abs(fw[2])
        return wall, axial, float(np.hypot(wall, axial))

    # ---- one insertion trial ---------------------------------------------
    def run(self, k_lin=500.0, k_rot=30.0, lateral_offset=(0.0, 0.0), speed=0.01,
            t_end=7.0, z_hover=0.03, search=False, f_press=4.0, pitch=0.0004,
            spiral_hz=1.0, r_max=0.003):
        """search=True: when the peg lands on the top face (axial force) press with f_press and
        spiral the commanded xy outward (Archimedean) until the peg drops into the hole."""
        mujoco.mj_resetData(self.m, self.d)
        goal_xy = self.hole_pos[:2] + np.array(lateral_offset)   # commanded xy (misaligned if offset != 0)
        start = np.array([goal_xy[0], goal_xy[1], self.hole_pos[2] + z_hover + PEG_LEN])
        # tip position: site is the peg tip, so target tip height = hole top + hover
        start[2] = self.hole_pos[2] + z_hover
        self.d.qpos[:6] = self.seed_q
        self.ik(start)
        self.d.qvel[:] = 0
        z_floor = self.hole_pos[2] - HOLE_DEPTH + 0.002          # target slightly below floor contact
        d_lin = 2 * np.sqrt(k_lin * 1.0); d_rot = 2 * np.sqrt(k_rot * 0.01)

        log = {k: [] for k in ("t", "tip", "wall", "axial", "total", "fz_cmd", "k", "mode")}
        mode, t_s, z_c, xy_hold, z_i, t_i = 0, 0.0, 0.0, goal_xy.copy(), 0.0, 0.0   # 0 descend 1 search 2 insert
        wall = axial = 0.0
        steps = int(t_end / self.m.opt.timestep)
        for s in range(steps):
            t = s * self.m.opt.timestep
            # settle 0.5 s, then descend at `speed`
            z_cmd = max(z_floor, start[2] - speed * max(0.0, t - 0.5))
            xy_cmd = goal_xy
            if search:
                wall, axial, _ = self.contact_forces()
                depth_now = self.hole_pos[2] - self.tip()[2]
                if mode == 0 and axial > 2.0 and depth_now < 0.002:
                    mode, t_s, z_c = 1, t, self.tip()[2]
                if mode == 1:
                    th = 2 * np.pi * spiral_hz * (t - t_s)
                    r = min(r_max, pitch * th / (2 * np.pi))
                    xy_cmd = goal_xy + r * np.array([np.cos(th), np.sin(th)])
                    z_cmd = z_c - f_press / k_lin                      # constant light press
                    if depth_now > 0.004:                              # dropped into the hole
                        mode, xy_hold, z_i, t_i = 2, self.tip()[:2].copy(), self.tip()[2], t
                if mode == 2:
                    xy_cmd = xy_hold
                    z_cmd = max(z_floor, z_i - speed * (t - t_i))
            x_des = np.array([xy_cmd[0], xy_cmd[1], z_cmd])
            J = self._jac()
            v = J @ self.d.qvel[:6]
            wrench = np.concatenate([k_lin * (x_des - self.tip()) - d_lin * v[:3],
                                     k_rot * self._rot_err() - d_rot * v[3:]])
            # gravity comp + cancel the model's viscous joint damping (feedforward), then add our own
            tau = J.T @ wrench + self.d.qfrc_bias[:6] \
                + self.m.dof_damping[:6] * self.d.qvel[:6] - 2.0 * self.d.qvel[:6]
            self.d.qfrc_applied[:6] = tau
            mujoco.mj_step(self.m, self.d)
            if s % 5 == 0:
                w, a, tot = self.contact_forces()
                for k, val in zip(log, (t, self.tip(), w, a, tot, k_lin * (x_des[2] - self.tip()[2]), k_lin, mode)):
                    log[k].append(val)
        out = {k: np.array(v) for k, v in log.items()}
        out["depth"] = self.hole_pos[2] - out["tip"][:, 2]
        out["inserted"] = bool(out["depth"].max() > 0.9 * HOLE_DEPTH)
        return out

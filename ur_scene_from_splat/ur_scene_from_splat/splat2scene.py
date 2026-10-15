#!/usr/bin/env python3
"""
splat2scene.py — turn a Gaussian-splat point cloud (.npz with xyz/rgb/opacity,
see rosnav's gs_splat_to_pointcloud.py) into a Gazebo scene: a support surface
plus one rigid object per cluster, each with a mesh, collision, mass and inertia.

  python3 -m ur_scene_from_splat.splat2scene --npz cafe_points_final.npz \\
      --roi -1.5 -2.3 -0.9  0.9 -0.7 0.2 --out scenes/cafe_table

Writes <out>/models/<obj>/{model.sdf,mesh.obj}, <out>/world.sdf and
<out>/scene.json. Launch with ur.gazebo.launch.py world_file:=<abs world.sdf>
(the robot is spawned by the launch file, not the world).
"""
import argparse
import json
import os
import re

import numpy as np
import open3d as o3d
import trimesh

HEADER_WORLD = os.path.join(os.path.dirname(__file__), '..', '..', 'ur_gazebo',
                            'worlds', 'empty.world')
FRICTION = '<surface><friction><ode><mu>0.9</mu><mu2>0.9</mu2></ode></friction></surface>'
MARKER = '<!-- Matches the GUI'
CLEARANCE = 0.002  # spawn height above the support so hulls don't start interpenetrating
# empty.world pulls the Sun from Fuel (needs internet); swap in an inline light so scenes load offline.
SUN_INCLUDE = re.compile(r'<include>\s*<uri>\s*https://fuel\.gazebosim\.org/[^<]*?/Sun\s*</uri>\s*</include>')
SUN_LIGHT = '''<light type="directional" name="sun">
      <cast_shadows>true</cast_shadows><pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse><specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>'''


UP_ROT = {  # rotation taking the splat's up axis to +z
    'z': np.eye(3),
    '-z': np.diag([1, -1, -1.0]),
    'y': np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0.0]]),
    '-y': np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.0]]),
    'x': np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0.0]]),
    '-x': np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0.0]]),
}


def load(npz, roi, min_opacity, up='z', scale=1.0):
    d = np.load(npz)
    xyz, rgb, op = d['xyz'].astype(np.float64), d['rgb'], d['opacity']
    keep = op >= min_opacity
    if roi:
        lo, hi = np.array(roi[:3]), np.array(roi[3:])
        keep &= np.all((xyz >= lo) & (xyz <= hi), axis=1)
    pc = o3d.geometry.PointCloud()
    pc.points = o3d.utility.Vector3dVector((xyz[keep] @ UP_ROT[up].T) * scale)
    pc.colors = o3d.utility.Vector3dVector(rgb[keep] / 255.0)
    return pc


def find_support(pc, tol):
    """Largest near-horizontal plane; returns (z, inlier_idx)."""
    best = None
    rest = np.arange(len(pc.points))
    for _ in range(4):
        sub = pc.select_by_index(rest)
        if len(sub.points) < 100:
            break
        plane, inl = sub.segment_plane(tol, 3, 2000)
        if abs(plane[2]) > 0.95:
            return -plane[3] / plane[2], rest[inl]
        rest = np.delete(rest, inl)
    return best, None


def cluster_objects(pc, support_z, args, support_box=None):
    P, C = np.asarray(pc.points), np.asarray(pc.colors)
    h = P[:, 2] - support_z
    m = (h > args.clear) & (h < args.max_height)
    obj = o3d.geometry.PointCloud()
    obj.points = o3d.utility.Vector3dVector(P[m])
    obj.colors = o3d.utility.Vector3dVector(C[m])
    lab = np.array(obj.cluster_dbscan(args.eps, args.min_pts))
    out = []
    for k in range(lab.max() + 1 if len(lab) else 0):
        sel = lab == k
        pts, col = np.asarray(obj.points)[sel], np.asarray(obj.colors)[sel]
        ext = pts.max(0) - pts.min(0)
        if ext.max() > args.max_size or ext[:2].max() < args.min_size:
            continue
        if not args.keep_tall and pts[:, 2].max() - support_z >= args.max_height - 0.01:
            continue  # ran into the height cap: background structure, not an object
        if support_box is not None and args.edge_margin > 0:
            lo, hi = support_box
            cxy = (pts.min(0)[:2] + pts.max(0)[:2]) / 2
            if np.any(cxy < lo[:2] + args.edge_margin) or np.any(cxy > hi[:2] - args.edge_margin):
                continue  # on the rim of the crop: likely a cut-off wall/shelf item, not a tabletop object
        out.append((pts, col))
    out.sort(key=lambda t: -len(t[0]))
    return out[:args.max_objects]


COLORS = {'red': (.8, .1, .1), 'green': (.1, .6, .2), 'blue': (.15, .25, .8), 'yellow': (.85, .8, .15),
          'orange': (.9, .5, .1), 'white': (.9, .9, .9), 'black': (.08, .08, .08), 'gray': (.5, .5, .5),
          'brown': (.45, .3, .15)}


def label_for(rgb, extents):
    c = min(COLORS, key=lambda k: np.sum((np.array(COLORS[k]) - rgb) ** 2))
    shape = 'flat' if extents[2] < 0.5 * extents[:2].max() else 'tall' if extents[2] > 1.5 * extents[:2].max() else 'chunky'
    return f'{c}_{shape}'


def build_object(i, pts, col, support_z, models_dir, density, fill, decompose=False, mass_override=None):
    # Convex hull of the splat points: robust to the holes/blur on unseen sides.
    # Sit the hull on the support surface so unseen undersides don't float.
    pts = pts.copy()
    pts[:, 2] = np.maximum(pts[:, 2], support_z)
    hull = trimesh.convex.convex_hull(
        np.vstack([pts, pts * [1, 1, 0] + [0, 0, support_z]]))
    com0 = hull.center_mass
    hull.apply_translation(-com0)
    mass = float(max(0.02, density * hull.volume * fill))
    rgb = np.clip(col.mean(0), 0, 1)
    inertia = hull.moment_inertia / hull.volume * mass  # scale unit-density tensor
    label = label_for(rgb, hull.extents)
    name = f'{label}_{i:02d}'
    if mass_override and name in mass_override:
        mass = mass_override[name]
        inertia = hull.moment_inertia / hull.volume * mass
    d = os.path.join(models_dir, name)
    os.makedirs(d, exist_ok=True)
    hull.export(os.path.join(d, 'mesh.obj'))
    uri = 'file://' + os.path.abspath(os.path.join(d, 'mesh.obj'))
    col_geoms = f'<collision name="collision"><geometry><mesh><uri>{uri}</uri></mesh></geometry>{FRICTION}</collision>'
    if decompose:
        import coacd
        parts = coacd.run_coacd(coacd.Mesh(hull.vertices, hull.faces), threshold=0.05)
        col_geoms = ''
        for j, (v, f) in enumerate(parts):
            pf = os.path.join(d, f'col_{j}.obj')
            trimesh.Trimesh(v, f).export(pf)
            col_geoms += (f'<collision name="collision_{j}"><geometry><mesh><uri>file://{os.path.abspath(pf)}'
                          f'</uri></mesh></geometry>{FRICTION}</collision>\n      ')
    r, g, b = rgb
    I = inertia
    sdf = f'''<?xml version="1.0"?>
<sdf version="1.7">
  <model name="{name}">
    <link name="link">
      <inertial>
        <mass>{mass:.4f}</mass>
        <inertia><ixx>{I[0,0]:.6g}</ixx><ixy>{I[0,1]:.6g}</ixy><ixz>{I[0,2]:.6g}</ixz><iyy>{I[1,1]:.6g}</iyy><iyz>{I[1,2]:.6g}</iyz><izz>{I[2,2]:.6g}</izz></inertia>
      </inertial>
      {col_geoms}
      <visual name="visual">
        <geometry><mesh><uri>{uri}</uri></mesh></geometry>
        <material><ambient>{r:.3f} {g:.3f} {b:.3f} 1</ambient><diffuse>{r:.3f} {g:.3f} {b:.3f} 1</diffuse></material>
      </visual>
    </link>
  </model>
</sdf>
'''
    with open(os.path.join(d, 'model.sdf'), 'w') as f:
        f.write(sdf)
    return name, com0, mass, hull.extents, label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--npz', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--roi', type=float, nargs=6, metavar=('X0', 'Y0', 'Z0', 'X1', 'Y1', 'Z1'))
    ap.add_argument('--voxel', type=float, default=0.01)
    ap.add_argument('--min-opacity', type=float, default=0.5)
    ap.add_argument('--plane-tol', type=float, default=0.012)
    ap.add_argument('--clear', type=float, default=0.015, help='drop points this close above the surface')
    ap.add_argument('--max-height', type=float, default=0.4)
    ap.add_argument('--eps', type=float, default=0.03)
    ap.add_argument('--min-pts', type=int, default=25)
    ap.add_argument('--min-size', type=float, default=0.03)
    ap.add_argument('--max-size', type=float, default=0.4)
    ap.add_argument('--max-objects', type=int, default=8)
    ap.add_argument('--table-z', type=float, default=0.0, help='world z of the support surface (splat frame is shifted to match)')
    ap.add_argument('--seed', type=int, default=0, help='RNG seed so the same input gives the same scene')
    ap.add_argument('--up', choices=sorted(UP_ROT), default='z', help="splat's up axis")
    ap.add_argument('--scale', type=float, default=1.0, help='metric scale factor for the splat')
    ap.add_argument('--support-length', type=float, help='true length (m) of the support surface long edge; sets scale')
    ap.add_argument('--mass', action='append', default=[], metavar='NAME=KG', help='override an object mass (repeatable)')
    ap.add_argument('--table-center', type=float, nargs=2, metavar=('X', 'Y'),
                    help='world XY for the support surface centre (default: keep the splat frame); put it within arm reach')
    ap.add_argument('--edge-margin', type=float, default=0.1,
                    help='drop clusters whose centre is within this many m of the support edge (0 keeps all)')
    ap.add_argument('--keep-tall', action='store_true', help='keep clusters that hit --max-height')
    ap.add_argument('--decompose', action='store_true', help='CoACD convex decomposition for collision (needs coacd)')
    ap.add_argument('--density', type=float, default=600.0, help='kg/m^3')
    ap.add_argument('--fill', type=float, default=0.5, help='hollowness factor on volume')
    args = ap.parse_args()

    np.random.seed(args.seed)
    o3d.utility.random.seed(args.seed)
    mass_override = {k: float(v) for k, v in (m.split('=') for m in args.mass)}
    pc = load(args.npz, args.roi, args.min_opacity, args.up, args.scale).voxel_down_sample(args.voxel)
    print(f'{len(pc.points)} points after crop/downsample')
    z, inl = find_support(pc, args.plane_tol)
    if inl is None:
        raise SystemExit('no horizontal support plane found; adjust --roi')
    sp = np.asarray(pc.points)[inl]
    print(f'support plane z={z:.3f}, {len(inl)} pts, extent {np.ptp(sp[:, :2], axis=0)}')

    if args.support_length:
        k = args.support_length / float(np.ptp(sp[:, :2], axis=0).max())
        print(f'rescaling by {k:.4f} to make the support {args.support_length} m long')
        pc = o3d.geometry.PointCloud(pc)
        pc.points = o3d.utility.Vector3dVector(np.asarray(pc.points) * k)
        z, sp = z * k, sp * k
    objs = cluster_objects(pc, z, args, (sp.min(0), sp.max(0)))
    print(f'{len(objs)} object clusters')

    dz = args.table_z - z  # splat frame has arbitrary height; put the surface at --table-z
    sc = (sp.min(0) + sp.max(0)) / 2
    shift = np.array([args.table_center[0] - sc[0], args.table_center[1] - sc[1], dz]) if args.table_center else np.array([0, 0, dz])
    models_dir = os.path.join(args.out, 'models')
    os.makedirs(models_dir, exist_ok=True)
    includes, meta = [], []
    names = set()
    for i, (pts, col) in enumerate(objs):
        name, com, mass, ext, label = build_object(i, pts, col, z, models_dir, args.density, args.fill, args.decompose, mass_override)
        print(f'  {name}: n={len(pts)} mass={mass:.3f}kg extents={np.round(ext, 3)} at {np.round(com, 3)}')
        pose = com + shift + [0, 0, CLEARANCE]
        body = open(os.path.join(models_dir, name, 'model.sdf')).read()
        body = body.split('?>', 1)[1].split('<sdf version="1.7">')[1].rsplit('</sdf>', 1)[0]
        body = body.replace(f'<model name="{name}">',
                            f'<model name="{name}">\n      <pose>{pose[0]:.4f} {pose[1]:.4f} {pose[2]:.4f} 0 0 0</pose>', 1)
        names.add(name)
        includes.append(body.rstrip())
        meta.append({'name': name, 'label': label, 'pose': pose.tolist(), 'mass': mass, 'extents': ext.tolist()})

    for k in mass_override.keys() - names:
        print(f'warning: --mass {k} matches no object (have: {", ".join(sorted(names))})')

    lo, hi = sp.min(0), sp.max(0)
    c, s = (lo + hi) / 2 + shift * [1, 1, 0], hi - lo
    c[2] = args.table_z
    s[2] = 0.02
    table = f'''    <model name="support_surface">
      <static>true</static>
      <pose>{c[0]:.4f} {c[1]:.4f} {args.table_z - 0.01:.4f} 0 0 0</pose>
      <link name="link">
        <collision name="collision"><geometry><box><size>{s[0]:.3f} {s[1]:.3f} 0.02</size></box></geometry></collision>
        <visual name="visual"><geometry><box><size>{s[0]:.3f} {s[1]:.3f} 0.02</size></box></geometry>
          <material><ambient>0.55 0.4 0.3 1</ambient><diffuse>0.55 0.4 0.3 1</diffuse></material></visual>
      </link>
    </model>'''

    with open(HEADER_WORLD) as f:
        world = f.read()
    world = SUN_INCLUDE.sub(SUN_LIGHT, world, count=1)
    world = world.replace(MARKER, table + '\n' + '\n'.join(includes) + '\n\n    ' + MARKER, 1)
    with open(os.path.join(args.out, 'world.sdf'), 'w') as f:
        f.write(world)
    with open(os.path.join(args.out, 'scene.json'), 'w') as f:
        json.dump({'support_z': args.table_z, 'splat_support_z': z, 'support_center': c.tolist(), 'support_size': s.tolist(),
                   'objects': meta}, f, indent=2)
    print('wrote', os.path.join(args.out, 'world.sdf'))


if __name__ == '__main__':
    main()

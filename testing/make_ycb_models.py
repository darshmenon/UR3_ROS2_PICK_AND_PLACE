#!/usr/bin/env python3
"""Build Gazebo models from downloaded YCB google_16k meshes (visual = the real textured mesh, collision = a primitive).

    python3 testing/make_ycb_models.py --ycb-dir ~/ur3_third_party/ycb_data

Writes ur_gazebo/models/ycb_<name>/{model.config,model.sdf,meshes/...}. The model origin is the object's footprint
centre on the table (z = 0 at the bottom), so a world can place it like the coloured primitives. No code from the
download is run: only the .ply (bounds), .obj/.mtl/.png (copied) and tar contents are used.
"""
import argparse
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path.home() / ".local/lib/python3.10/site-packages"))
import open3d as o3d  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
# name -> (collision primitive, mass kg). Primitives keep the physics stable; the mesh is only for the look.
OBJECTS = {
    "005_tomato_soup_can": ("cylinder", 0.15),
    "013_apple": ("sphere", 0.10),
    "011_banana": ("box", 0.10),
    "025_mug": ("cylinder", 0.15),
    "010_potted_meat_can": ("box", 0.20),
}

RADIUS = {"025_mug": 0.040}

CONFIG = """<?xml version="1.0"?>
<model>
  <name>{name}</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>YCB {raw} (google_16k mesh, primitive collision)</description>
</model>
"""

SDF = """<?xml version="1.0"?>
<sdf version="1.9">
  <model name="{name}">
    <link name="link">
      <inertial>
        <pose>0 0 {hz:.4f} 0 0 0</pose>
        <mass>{mass}</mass>
        <inertia><ixx>{i:.6f}</ixx><ixy>0</ixy><ixz>0</ixz><iyy>{i:.6f}</iyy><iyz>0</iyz><izz>{i:.6f}</izz></inertia>
      </inertial>
      <collision name="collision">
        <pose>0 0 {hz:.4f} 0 0 0</pose>
        <geometry>{geom}</geometry>
        <surface><friction><ode><mu>1.5</mu><mu2>1.5</mu2></ode></friction></surface>
      </collision>
      <visual name="visual">
        <pose>{vx:.4f} {vy:.4f} 0 0 0 0</pose>
        <geometry><mesh><uri>model://{name}/meshes/textured.dae</uri></mesh></geometry>
      </visual>
    </link>
  </model>
</sdf>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ycb-dir", default="~/ur3_third_party/ycb_data")
    args = ap.parse_args()
    root = Path(args.ycb_dir).expanduser()
    for raw, (kind, mass) in OBJECTS.items():
        src = root / raw / raw / "google_16k"
        mesh = o3d.io.read_triangle_mesh(str(src / "nontextured.ply"))
        v = np.asarray(mesh.vertices)
        mn, mx = v.min(0), v.max(0)
        size = mx - mn
        cx, cy = v[:, 0].mean(), v[:, 1].mean()          # footprint centre of the mass of the surface
        if kind == "cylinder":
            radius = RADIUS.get(raw, min(size[0], size[1]) / 2)     # the mug's handle widens its bounding box
            geom = f"<cylinder><radius>{radius:.4f}</radius><length>{size[2]:.4f}</length></cylinder>"
        elif kind == "sphere":
            geom = f"<sphere><radius>{size.mean() / 2:.4f}</radius></sphere>"
        else:
            # curved objects: the bounding box overstates them, so shrink the short side a little
            geom = f"<box><size>{size[0] * 0.8:.4f} {size[1] * 0.8:.4f} {size[2]:.4f}</size></box>"
        name = f"ycb_{raw}"
        out = REPO / "ur_gazebo" / "models" / name
        (out / "meshes").mkdir(parents=True, exist_ok=True)
        # .dae, not .obj: Gazebo flips the .obj texture coordinates and shows the wrong part of the YCB texture atlas.
        # Every YCB texture is called texture_map.png and Gazebo caches textures by file name, so all objects would
        # show the first one loaded; give each model its own file name and point the mesh at it.
        tex = f"{raw}_texture.png"
        shutil.copy(src / "texture_map.png", out / "meshes" / tex)
        dae = (src / "textured.dae").read_text().replace("texture_map.png", tex)
        (out / "meshes" / "textured.dae").write_text(dae)
        for stale in ("textured.obj", "textured.mtl", "texture_map.png"):
            (out / "meshes" / stale).unlink(missing_ok=True)
        i = mass * (size.max() ** 2) / 12
        (out / "model.config").write_text(CONFIG.format(name=name, raw=raw))
        (out / "model.sdf").write_text(SDF.format(name=name, mass=mass, i=i, hz=size[2] / 2, geom=geom,
                                                  vx=-cx, vy=-cy))
        print(f"{name}: size {np.round(size * 100, 1)} cm, collision {kind}, mesh offset ({-cx:.3f}, {-cy:.3f})")


if __name__ == "__main__":
    main()

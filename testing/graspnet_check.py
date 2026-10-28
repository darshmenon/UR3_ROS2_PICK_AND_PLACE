#!/usr/bin/env python3
"""Contact-GraspNet (PyTorch port) on a simulated head-camera view, scored against Gazebo truth.

Two steps, because the sim needs ROS and Contact-GraspNet needs only torch:

    python3 testing/graspnet_check.py capture --object cylinder_5cm --domain 79 --out testing/_out/gn_cyl.npz
    python3 testing/graspnet_check.py run --npz testing/_out/gn_cyl.npz [--graspnet-dir ~/ur3_third_party/contact_graspnet_pytorch]

capture saves depth (m), colour, K, a red-object segmap, the camera->base_link transform and the true object
position. run predicts grasps on the red segment and reports where the best grasp is relative to the truth
(xy error of the grasp centre, approach direction, score), for comparison with the colour+depth detector and
the VLM.
"""
import argparse
import math
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402


def capture(args):
    obj = bench.OBJECTS[args.object]
    bench.OBJECT = obj["model"]
    (bench.REPO / "logs").mkdir(exist_ok=True)
    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    sim = None
    try:
        sim, _ = bench.launch_sim(args.gripper, obj["world"], args.domain, args.settle)
        import cv2
        import rclpy
        import tf2_ros
        from rclpy.node import Node
        from sensor_msgs.msg import CameraInfo, Image
        sys.path.insert(0, str(bench.REPO / "ur_perception"))
        from ur_perception.image_convert import NumpyBridge
        rclpy.init()
        node = Node("graspnet_capture")
        buf = {}
        br = NumpyBridge()
        node.create_subscription(Image, "/camera_head/color/image_raw", lambda m: buf.__setitem__("c", m), 10)
        node.create_subscription(Image, "/camera_head/depth/image_rect_raw", lambda m: buf.__setitem__("d", m), 10)
        node.create_subscription(CameraInfo, "/camera_head/camera_info", lambda m: buf.__setitem__("k", m), 10)
        tfb = tf2_ros.Buffer()
        tf2_ros.TransformListener(tfb, node)
        end = time.time() + 60
        while time.time() < end and not all(k in buf for k in "cdk"):
            rclpy.spin_once(node, timeout_sec=0.2)
        if not all(k in buf for k in "cdk"):
            sys.exit("no camera data")
        for _ in range(20):
            rclpy.spin_once(node, timeout_sec=0.1)
        bgr = br.imgmsg_to_cv2(buf["c"], desired_encoding="bgr8")
        depth = br.imgmsg_to_cv2(buf["d"], desired_encoding="passthrough").astype(np.float32)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        red = cv2.inRange(hsv, (0, 120, 80), (10, 255, 255)) | cv2.inRange(hsv, (170, 120, 80), (180, 255, 255))
        segmap = (red > 0).astype(np.uint8)
        tf = tfb.lookup_transform("base_link", buf["d"].header.frame_id, rclpy.time.Time(),
                                  timeout=rclpy.duration.Duration(seconds=2.0))
        t, q = tf.transform.translation, tf.transform.rotation
        x, y, z, w = q.x, q.y, q.z, q.w
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = [t.x, t.y, t.z]
        truth = bench.object_pose()
        np.savez(args.out, depth=depth, rgb=bgr[:, :, ::-1], K=np.array(buf["k"].k).reshape(3, 3),
                 segmap=segmap, T_base_cam=T, truth=np.array(truth), red_pixels=int(segmap.sum()))
        print(f"saved {args.out}: depth {depth.shape}, red pixels {int(segmap.sum())}, truth {truth}")
        rclpy.shutdown()
    finally:
        bench.stop_sim([sim])


def run(args):
    gdir = Path(args.graspnet_dir).expanduser()
    sys.path.insert(0, str(gdir))
    sys.path.insert(0, str(gdir / "contact_graspnet_pytorch"))
    import torch
    # the checkpoint holds numpy scalars; allow just those instead of turning weights_only off
    torch.serialization.add_safe_globals([np.core.multiarray.scalar, np.dtype, type(np.dtype('float64'))])
    from contact_graspnet_pytorch import config_utils
    from contact_graspnet_pytorch.checkpoints import CheckpointIO
    from contact_graspnet_pytorch.contact_grasp_estimator import GraspEstimator

    d = np.load(args.npz)
    depth, K, segmap, T, truth = d["depth"], d["K"], d["segmap"], d["T_base_cam"], d["truth"]
    ckpt = gdir / "checkpoints" / "contact_graspnet"
    cfg = config_utils.load_config(str(ckpt), batch_size=1, arg_configs=[])
    est = GraspEstimator(cfg)
    CheckpointIO(checkpoint_dir=str(ckpt / "checkpoints"), model=est.model).load("model.pt")
    pc_full, pc_segments, _ = est.extract_point_clouds(depth, K, segmap=segmap.astype(np.int32), rgb=d["rgb"],
                                                       skip_border_objects=False, z_range=[0.1, 2.0])
    print(f"scene points {pc_full.shape[0]}, segments {[ (k, v.shape[0]) for k, v in pc_segments.items() ]}")
    t0 = time.time()
    grasps, scores, contacts, _ = est.predict_scene_grasps(pc_full, pc_segments=pc_segments, local_regions=True,
                                                           filter_grasps=True, forward_passes=args.passes)
    print(f"inference {time.time() - t0:.1f}s on {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}")
    g = grasps.get(1) if isinstance(grasps, dict) else grasps
    s = scores.get(1) if isinstance(scores, dict) else scores
    if g is None or len(g) == 0:
        print("no grasps predicted for the red segment")
        return
    best = int(np.argmax(s))
    Tg = T @ g[best]                       # grasp pose in base_link
    pos, approach = Tg[:3, 3], Tg[:3, 2]   # Contact-GraspNet: z axis = approach direction
    err_xy = math.hypot(pos[0] - truth[0], pos[1] - truth[1]) * 1000
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, -approach[2]))))
    print(f"{len(g)} grasps, best score {s[best]:.2f}")
    print(f"best grasp centre base_link ({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}); truth ({truth[0]:.3f}, "
          f"{truth[1]:.3f}, {truth[2]:.3f}) -> xy err {err_xy:.0f} mm")
    print(f"approach direction {np.round(approach, 2)} ({tilt:.0f} deg from straight down)")
    order = np.argsort(-s)[:5]
    for i in order:
        p = (T @ g[i])[:3, 3]
        print(f"  score {s[i]:.2f}  xy err {math.hypot(p[0] - truth[0], p[1] - truth[1]) * 1000:.0f} mm  z {p[2]:.3f}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--gripper", default="robotiq_2f_85")
    c.add_argument("--object", default="cylinder_5cm", choices=list(bench.OBJECTS))
    c.add_argument("--domain", type=int, default=79)
    c.add_argument("--settle", type=float, default=45.0)
    c.add_argument("--out", required=True)
    r = sub.add_parser("run")
    r.add_argument("--npz", required=True)
    r.add_argument("--graspnet-dir", default="~/ur3_third_party/contact_graspnet_pytorch")
    r.add_argument("--passes", type=int, default=3)
    args = ap.parse_args()
    (capture if args.cmd == "capture" else run)(args)


if __name__ == "__main__":
    main()

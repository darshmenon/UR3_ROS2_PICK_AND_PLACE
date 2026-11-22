"""Unit tests for ur_perception color_detector and image_convert (no ROS graph)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ur_perception"))
np = pytest.importorskip("numpy")
cv2 = pytest.importorskip("cv2")
cd = pytest.importorskip("ur_perception.color_detector")
pytest.importorskip("rclpy")
pytest.importorskip("sensor_msgs.msg")
ic = pytest.importorskip("ur_perception.image_convert")

BGR = {"red": (0, 0, 255), "green": (0, 255, 0), "blue": (255, 0, 0),
       "yellow": (0, 255, 255), "orange": (0, 165, 255)}


def _img(color, rect=(40, 30, 100, 80), shape="rect"):
    img = np.zeros((200, 300, 3), np.uint8)
    x, y, w, h = rect
    if shape == "rect":
        cv2.rectangle(img, (x, y), (x + w, y + h), BGR[color], -1)
    else:
        cv2.circle(img, (x + w // 2, y + h // 2), 40, BGR[color], -1)
    return img


@pytest.mark.parametrize("color", list(BGR))
def test_detects_each_color(color):
    dets = cd.ColorDetector().detect(_img(color))
    assert [d["label"] for d in dets] == [color]
    d = dets[0]
    assert d["shape"] == "box"
    cx, cy = d["centroid_px"]
    assert abs(cx - 90) <= 3 and abs(cy - 70) <= 3
    assert 0 < d["confidence"] <= 1.0
    assert d["mask"].shape == (200, 300)


def test_cylinder_shape():
    d = cd.ColorDetector(["red"]).detect(_img("red", shape="circle"))[0]
    assert d["shape"] == "cylinder"


def test_target_colors_filter_and_validation():
    assert cd.ColorDetector(["blue"]).detect(_img("red")) == []
    with pytest.raises(ValueError):
        cd.ColorDetector(["purple"])


def test_min_area_filters_small_blob():
    img = _img("green", rect=(10, 10, 12, 12))
    assert cd.ColorDetector(min_area=500).detect(img) == []
    assert len(cd.ColorDetector(min_area=50).detect(img)) == 1


def test_empty_inputs():
    d = cd.ColorDetector()
    assert d.detect(None) == []
    assert d.detect(np.zeros((0, 0, 3), np.uint8)) == []
    assert d.detect(np.zeros((50, 50, 3), np.uint8)) == []


def test_two_blobs_and_draw_does_not_mutate():
    img = _img("red")
    cv2.rectangle(img, (200, 100), (260, 160), BGR["blue"], -1)
    det = cd.ColorDetector()
    dets = det.detect(img)
    assert sorted(x["label"] for x in dets) == ["blue", "red"]
    before = img.copy()
    vis = det.draw_detections(img, dets)
    assert np.array_equal(img, before) and not np.array_equal(vis, img)


def test_yaw_in_range():
    img = np.zeros((200, 300, 3), np.uint8)
    pts = cv2.boxPoints(((150, 100), (80, 50), 20)).astype(np.int32)
    cv2.fillPoly(img, [pts], BGR["red"])
    yaw = cd.ColorDetector(["red"]).detect(img)[0]["yaw_px"]
    assert -np.pi / 4 <= yaw < np.pi / 4


# ---- image_convert ----
def _msg(enc, arr, step=None):
    from sensor_msgs.msg import Image
    m = Image()
    m.height, m.width = arr.shape[:2]
    m.encoding = enc
    m.step = step or arr.strides[0]
    m.data = arr.tobytes()
    return m


def test_bridge_roundtrip_bgr8():
    arr = np.random.randint(0, 255, (4, 5, 3), np.uint8)
    b = ic.NumpyBridge()
    msg = b.cv2_to_imgmsg(arr, "bgr8")
    assert (msg.height, msg.width, msg.step, msg.encoding) == (4, 5, 15, "bgr8")
    assert np.array_equal(b.imgmsg_to_cv2(msg), arr)


def test_bridge_rgb_to_bgr_conversion():
    arr = np.zeros((2, 2, 3), np.uint8); arr[..., 0] = 255  # red in rgb8
    out = ic.NumpyBridge().imgmsg_to_cv2(_msg("rgb8", arr), "bgr8")
    assert tuple(out[0, 0]) == (0, 0, 255)


def test_bridge_depth_and_mono_dtypes():
    f = np.arange(6, dtype=np.float32).reshape(2, 3)
    out = ic.NumpyBridge().imgmsg_to_cv2(_msg("32FC1", f))
    assert out.dtype == np.float32 and np.array_equal(out, f)
    u = np.arange(6, dtype=np.uint16).reshape(2, 3)
    assert np.array_equal(ic.NumpyBridge().imgmsg_to_cv2(_msg("16UC1", u)), u)


def test_bridge_handles_row_padding():
    padded = np.zeros((2, 8), np.uint8); padded[:, :3] = [[1, 2, 3], [4, 5, 6]]
    m = _msg("mono8", padded); m.width = 3
    assert np.array_equal(ic.NumpyBridge().imgmsg_to_cv2(m), [[1, 2, 3], [4, 5, 6]])


def test_bridge_errors():
    b = ic.NumpyBridge()
    with pytest.raises(ic.CvBridgeError):
        b.imgmsg_to_cv2(_msg("bayer_rggb8", np.zeros((2, 2), np.uint8)))
    with pytest.raises(ic.CvBridgeError):
        b.cv2_to_imgmsg(np.zeros((2, 2), np.uint8), "nope")
    with pytest.raises(ic.CvBridgeError):
        b.imgmsg_to_cv2(_msg("mono16", np.zeros((2, 2), np.uint16)), "bgr8")

"""NumPy-only replacement for the parts of cv_bridge this package uses.

The ROS Humble cv_bridge is compiled against NumPy 1.x; with NumPy 2.x installed every
imgmsg_to_cv2 call dies with "AttributeError: _ARRAY_API not found", which silently
stopped the detector from ever producing a detection. This converts sensor_msgs/Image
to and from numpy arrays directly and keeps the cv_bridge method names.
"""
import numpy as np
from sensor_msgs.msg import Image


class CvBridgeError(Exception):
    pass


_DTYPES = {
    'rgb8': (np.uint8, 3), 'bgr8': (np.uint8, 3), 'rgba8': (np.uint8, 4), 'bgra8': (np.uint8, 4),
    'mono8': (np.uint8, 1), '8UC1': (np.uint8, 1), '8UC3': (np.uint8, 3),
    'mono16': (np.uint16, 1), '16UC1': (np.uint16, 1), '32FC1': (np.float32, 1),
}


class NumpyBridge:
    """Drop-in for the CvBridge methods used here (imgmsg_to_cv2, cv2_to_imgmsg)."""

    def imgmsg_to_cv2(self, msg, desired_encoding='passthrough'):
        if msg.encoding not in _DTYPES:
            raise CvBridgeError(f"unsupported image encoding {msg.encoding!r}")
        dtype, ch = _DTYPES[msg.encoding]
        itemsize = np.dtype(dtype).itemsize
        row = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.step)
        arr = row[:, :msg.width * ch * itemsize].copy().view(dtype)
        arr = arr.reshape(msg.height, msg.width, ch) if ch > 1 else arr.reshape(msg.height, msg.width)
        if msg.is_bigendian and itemsize > 1:
            arr = arr.byteswap()
        if desired_encoding in ('passthrough', msg.encoding):
            return arr
        import cv2
        pair = (msg.encoding, desired_encoding)
        codes = {
            ('rgb8', 'bgr8'): cv2.COLOR_RGB2BGR, ('bgr8', 'rgb8'): cv2.COLOR_BGR2RGB,
            ('rgba8', 'bgr8'): cv2.COLOR_RGBA2BGR, ('bgra8', 'bgr8'): cv2.COLOR_BGRA2BGR,
            ('rgba8', 'rgb8'): cv2.COLOR_RGBA2RGB, ('bgra8', 'rgb8'): cv2.COLOR_BGRA2RGB,
            ('mono8', 'bgr8'): cv2.COLOR_GRAY2BGR, ('mono8', 'rgb8'): cv2.COLOR_GRAY2RGB,
        }
        if pair not in codes:
            raise CvBridgeError(f"cannot convert {msg.encoding} to {desired_encoding}")
        return cv2.cvtColor(arr, codes[pair])

    def cv2_to_imgmsg(self, img, encoding='bgr8', header=None):
        if encoding not in _DTYPES:
            raise CvBridgeError(f"unsupported image encoding {encoding!r}")
        img = np.ascontiguousarray(img)
        msg = Image()
        if header is not None:
            msg.header = header
        msg.height, msg.width = img.shape[:2]
        msg.encoding = encoding
        msg.is_bigendian = 0
        msg.step = img.strides[0]
        msg.data = img.tobytes()
        return msg

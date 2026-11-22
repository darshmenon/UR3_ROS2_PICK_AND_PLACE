"""Grasp-stall check. No ROS: the Hand-E joint decreases as it closes."""
from ur_visual_servo.servo_node import grasp_stalled


def test_two_finger_stalls_short_of_closed():
    assert grasp_stalled(0.40, closed=0.8, open_pos=0.0, margin=0.05)
    assert not grasp_stalled(0.80, closed=0.8, open_pos=0.0, margin=0.05)


def test_hande_stalls_above_zero():
    assert grasp_stalled(0.012, closed=0.0, open_pos=0.025, margin=0.05)
    assert not grasp_stalled(0.0, closed=0.0, open_pos=0.025, margin=0.05)

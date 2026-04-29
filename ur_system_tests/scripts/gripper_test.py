#!/usr/bin/env python3
"""Open/close stress-test for any gripper connected to /gripper_controller."""

import sys
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import GripperCommand


OPEN  = 0.0
CLOSE = 0.8   # finger_joint for Robotiq; gripper_joint for OnRobot use 1.3
EFFORT = 50.0
PAUSE  = 1.5  # seconds between open and close


class GripperTester(Node):
    def __init__(self, cycles: int):
        super().__init__('gripper_tester')
        self._client = ActionClient(self, GripperCommand, '/gripper_controller/gripper_cmd')
        self._cycles = cycles

    def _send(self, position: float, label: str) -> bool:
        self.get_logger().info(f'{label} → position={position}')
        if not self._client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Action server not available')
            return False
        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = EFFORT
        future = self._client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        result_future = future.result().get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        res = result_future.result().result
        ok = res.reached_goal
        self.get_logger().info(
            f'  → pos={res.position:.3f}  reached_goal={ok}  stalled={res.stalled}'
        )
        return ok

    def run(self):
        self._client.wait_for_server()
        for i in range(1, self._cycles + 1):
            self.get_logger().info(f'--- Cycle {i}/{self._cycles} ---')
            self._send(CLOSE, 'CLOSE')
            time.sleep(PAUSE)
            self._send(OPEN, 'OPEN')
            time.sleep(PAUSE)
        self.get_logger().info('Done.')


def main():
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    rclpy.init()
    node = GripperTester(cycles)
    node.run()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

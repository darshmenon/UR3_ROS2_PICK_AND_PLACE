#!/usr/bin/env python3
"""
Auto-collect behavior-cloning demonstrations without teleoperation.

Repeatedly triggers the existing autonomous MTC pick-and-place attempt
(the `run_pick_place` service served by ur_mtc_pick_place_demo's mtc_node)
while ur_data_collector's DataCollectorNode records each attempt, then sorts
the resulting HDF5 episode by whether that attempt succeeded.

Prerequisites (must already be running):
    ros2 launch ur_gazebo ur.gazebo.launch.py
    ros2 launch ur_perception perception.launch.py
    ros2 launch ur_bt_planner mtc_retry.launch.py auto_run_on_startup:=false
    ros2 run ur_data_collector collector_node   (or via a launch file)

Usage:
    python3 auto_collect_demos.py --trials 100 --target_successes 50

Notes:
    - Only successful attempts are kept as demos by default (BC/flow-matching
      training wants clean successful trajectories) — pass --keep_failures to
      sort failed episodes into output_dir/failed/ instead of deleting them.
    - The pick target's world pose is currently static (colored_blocks.world
      has no object-randomization service), so repeated episodes will look
      very similar. Fine for a first proof-of-concept dataset, but a real
      training set will want scene variation added on top of this script.
"""

import argparse
import csv
import glob
import os
import time
from datetime import datetime

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class AutoCollectorNode(Node):
    def __init__(self):
        super().__init__('auto_collect_demos_node')
        self.start_recording_client = self.create_client(Trigger, '/data_collector/start_recording')
        self.stop_recording_client = self.create_client(Trigger, '/data_collector/stop_recording')
        self.run_pick_place_client = self.create_client(Trigger, '/run_pick_place')

    def wait_for_services(self, timeout_sec: float = 30.0) -> bool:
        ok = True
        for name, client in [
            ('/data_collector/start_recording', self.start_recording_client),
            ('/data_collector/stop_recording', self.stop_recording_client),
            ('/run_pick_place', self.run_pick_place_client),
        ]:
            if not client.wait_for_service(timeout_sec=timeout_sec):
                self.get_logger().error(f'Service {name} not available after {timeout_sec}s')
                ok = False
        return ok

    def call(self, client, timeout_sec: float):
        future = client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_sec)
        if not future.done():
            return False, f'timed out after {timeout_sec}s'
        result = future.result()
        if result is None:
            return False, 'service call failed (no response)'
        return result.success, result.message


def latest_h5(output_dir: str, prefix: str, after_ts: float):
    """Finds the newest *.h5 file in output_dir modified after after_ts,
    polling briefly since DataCollectorNode saves on a background thread."""
    pattern = os.path.join(output_dir, f'{prefix}_*.h5')
    deadline = time.time() + 15.0
    while time.time() < deadline:
        candidates = [f for f in glob.glob(pattern) if os.path.getmtime(f) >= after_ts]
        if candidates:
            return max(candidates, key=os.path.getmtime)
        time.sleep(0.5)
    return None


def run(args):
    output_dir = os.path.expanduser(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    success_dir = os.path.join(output_dir, 'success')
    failed_dir = os.path.join(output_dir, 'failed')
    os.makedirs(success_dir, exist_ok=True)
    if args.keep_failures:
        os.makedirs(failed_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, f'auto_collect_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    csv_file = open(csv_path, 'w', newline='')
    writer = csv.writer(csv_file)
    writer.writerow(['trial', 'success', 'duration_s', 'episode_file', 'message'])

    rclpy.init()
    node = AutoCollectorNode()

    if not node.wait_for_services(timeout_sec=args.service_timeout):
        node.get_logger().error(
            'Required services not available — is ur.gazebo.launch.py, '
            'ur_perception, ur_bt_planner (mtc_retry.launch.py '
            'auto_run_on_startup:=false), and the DataCollectorNode all running?'
        )
        node.destroy_node()
        rclpy.shutdown()
        csv_file.close()
        return

    successes = 0
    trials_run = 0
    for trial in range(1, args.trials + 1):
        trials_run = trial
        if args.target_successes and successes >= args.target_successes:
            node.get_logger().info(f'Reached target of {args.target_successes} successes — stopping.')
            break

        node.get_logger().info(f'--- Trial {trial}/{args.trials} ---')
        t0 = time.time()

        ok, msg = node.call(node.start_recording_client, timeout_sec=10.0)
        if not ok:
            node.get_logger().error(f'start_recording failed: {msg}')
            writer.writerow([trial, False, 0.0, '', f'start_recording failed: {msg}'])
            csv_file.flush()
            continue

        attempt_start = time.time()
        success, message = node.call(node.run_pick_place_client, timeout_sec=args.attempt_timeout)
        duration = time.time() - attempt_start

        stop_ok, stop_msg = node.call(node.stop_recording_client, timeout_sec=10.0)
        if not stop_ok:
            node.get_logger().warn(f'stop_recording reported failure: {stop_msg}')

        episode_file = latest_h5(output_dir, args.episode_name_prefix, t0)
        dest = ''
        if episode_file is not None:
            if success:
                dest = os.path.join(success_dir, os.path.basename(episode_file))
                os.replace(episode_file, dest)
                successes += 1
            elif args.keep_failures:
                dest = os.path.join(failed_dir, os.path.basename(episode_file))
                os.replace(episode_file, dest)
            else:
                os.remove(episode_file)
                dest = '(discarded)'
        else:
            node.get_logger().warn('No new episode .h5 file found after stop_recording.')

        node.get_logger().info(
            f'Trial {trial}: {"SUCCESS" if success else "FAILURE"} '
            f'({duration:.1f}s) -> {dest}'
        )
        writer.writerow([trial, success, round(duration, 2), dest, message])
        csv_file.flush()

    node.get_logger().info(
        f'Done. {successes}/{trials_run} successful episodes saved to {success_dir}'
    )
    node.destroy_node()
    rclpy.shutdown()
    csv_file.close()
    print(f'\nResults CSV: {csv_path}')
    print(f'Successful episodes: {successes}')
    print(f'Demo directory: {success_dir}')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Auto-collect BC/flow-matching demos by scripting the existing MTC pick-place attempts.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--trials', type=int, default=50, help='Maximum number of attempts to run.')
    parser.add_argument('--target_successes', type=int, default=0,
                         help='Stop early once this many successful episodes are collected (0 = disabled, run all --trials).')
    parser.add_argument('--output_dir', type=str, default='~/ur3_demos')
    parser.add_argument('--episode_name_prefix', type=str, default='demo',
                         help='Must match the DataCollectorNode\'s episode_name_prefix parameter.')
    parser.add_argument('--attempt_timeout', type=float, default=90.0,
                         help='Max seconds to wait for one run_pick_place attempt to finish.')
    parser.add_argument('--service_timeout', type=float, default=30.0,
                         help='Max seconds to wait for required services to appear at startup.')
    parser.add_argument('--keep_failures', action='store_true',
                         help='Sort failed episodes into output_dir/failed/ instead of deleting them.')
    return parser.parse_args()


if __name__ == '__main__':
    run(parse_args())

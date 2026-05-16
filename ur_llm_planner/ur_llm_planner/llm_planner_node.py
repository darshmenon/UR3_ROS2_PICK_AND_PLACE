#!/usr/bin/env python3
"""
LLM Planner Node — main ROS 2 entry point for the ur_llm_planner package.

Accepts natural language robot commands, queries a local Ollama LLM to produce a
structured task plan, and executes that plan on the UR3 arm.

Usage (topic):
    ros2 topic pub --once /llm_planner/command std_msgs/msg/String \
        "{data: 'pick up the red object and place it to the left'}"

Usage (launch with auto-demo):
    ros2 launch ur_llm_planner llm_planner.launch.py auto_demo:=true
"""

import os
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from std_msgs.msg import String

from ur_interfaces.msg import DetectedObjectArray

from ur_llm_planner.ollama_client import OllamaClient
from ur_llm_planner.motion_executor import MotionExecutor


# Named arm poses available for move_to_named_pose action
NAMED_POSES = ["home", "ready"]

# QoS profile for sensor data (best-effort, keep last 1)
SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)


class LLMPlannerNode(Node):
    """
    ROS 2 node that bridges natural language commands to robot motion.

    Subscriptions:
        /detected_objects  (ur_interfaces/msg/DetectedObjectArray)
        /llm_planner/command (std_msgs/msg/String)

    Parameters:
        ollama_model       (str)  – Ollama model tag (e.g. llama3.2:3b).
        ollama_base_url    (str)  – Ollama server URL.
        auto_demo          (bool) – Run demo command automatically after startup.
        auto_demo_command  (str)  – Natural language command for auto-demo.
    """

    def __init__(self):
        super().__init__("llm_planner_node")

        # ── Parameters ────────────────────────────────────────────────
        self.declare_parameter("ollama_model",    "llama2:latest")
        self.declare_parameter("ollama_base_url", "http://localhost:11434")
        self.declare_parameter("auto_demo",       False)
        self.declare_parameter(
            "auto_demo_command",
            "pick up the red object and place it to the left of the robot",
        )

        model    = self.get_parameter("ollama_model").get_parameter_value().string_value
        base_url = self.get_parameter("ollama_base_url").get_parameter_value().string_value
        self._auto_demo = self.get_parameter("auto_demo").get_parameter_value().bool_value
        self._auto_demo_command = (
            self.get_parameter("auto_demo_command").get_parameter_value().string_value
        )

        # ── Sub-components ─────────────────────────────────────────────
        self._llm = OllamaClient(model=model, base_url=base_url)
        if not self._llm.is_available():
            self.get_logger().warn(
                f"Ollama not reachable at {base_url}. "
                "Start it with: ollama serve   and pull a model: ollama pull llama3.2:3b"
            )
        else:
            self.get_logger().info(f"Ollama available at {base_url}, model={model}")
        self._executor = MotionExecutor(self)

        # ── State ─────────────────────────────────────────────────────
        self._latest_objects: list[dict] = []
        self._is_executing = False

        # ── Subscriptions ─────────────────────────────────────────────
        self._objects_sub = self.create_subscription(
            DetectedObjectArray,
            "/detected_objects",
            self._objects_callback,
            SENSOR_QOS,
        )

        self._command_sub = self.create_subscription(
            String,
            "/llm_planner/command",
            self._command_callback,
            10,
        )

        # ── Startup ───────────────────────────────────────────────────
        self.get_logger().info(
            f"LLMPlannerNode started. Model: {model}. "
            f"Waiting for action servers..."
        )
        self._executor.wait_for_servers(timeout=5.0)
        self.get_logger().info(
            "LLMPlannerNode ready. "
            "Publish to /llm_planner/command (std_msgs/String) to execute a task."
        )

        # Auto-demo timer (fires once after 5 s if enabled)
        if self._auto_demo:
            self.get_logger().info(
                f"Auto-demo enabled. Will run in 5 seconds: '{self._auto_demo_command}'"
            )
            self._auto_demo_timer = self.create_timer(5.0, self._auto_demo_callback)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _objects_callback(self, msg: DetectedObjectArray) -> None:
        """Cache the latest detected objects from the perception pipeline."""
        self._latest_objects = [
            {
                "id": obj.id,
                "label": obj.label,
                "position": {
                    "x": obj.position.x,
                    "y": obj.position.y,
                    "z": obj.position.z,
                },
                "dimensions": {
                    "x": obj.dimensions.x,
                    "y": obj.dimensions.y,
                    "z": obj.dimensions.z,
                },
                "confidence": obj.confidence,
            }
            for obj in msg.objects
        ]

    def _command_callback(self, msg: String) -> None:
        """Handle an incoming natural language command."""
        command = msg.data.strip()
        if not command:
            self.get_logger().warn("Received empty command — ignoring.")
            return

        if self._is_executing:
            self.get_logger().warn(
                f"Still executing a previous task — ignoring command: '{command}'"
            )
            return

        self.get_logger().info(f"Received command: '{command}'")
        self._run_plan_and_execute(command)

    def _auto_demo_callback(self) -> None:
        """One-shot timer callback to run the auto-demo command."""
        self.destroy_timer(self._auto_demo_timer)  # fire only once
        self.get_logger().info(
            f"[AutoDemo] Running demo command: '{self._auto_demo_command}'"
        )
        self._run_plan_and_execute(self._auto_demo_command)

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    def _run_plan_and_execute(self, command: str) -> None:
        """
        Full pipeline: LLM planning → motion execution, run in a background thread.

        rclpy.spin_until_future_complete must NOT be called from inside a spin
        callback — doing so deadlocks the executor. We offload to a thread so the
        main spin loop stays unblocked while action calls complete.
        """
        self._is_executing = True
        thread = threading.Thread(
            target=self._threaded_plan_and_execute,
            args=(command,),
            daemon=True,
        )
        thread.start()

    def _threaded_plan_and_execute(self, command: str) -> None:
        try:
            self._do_plan_and_execute(command)
        finally:
            self._is_executing = False

    _MAX_RETRIES = 2

    def _do_plan_and_execute(self, command: str, _retry: int = 0) -> None:
        detected_objects = list(self._latest_objects)  # snapshot

        self.get_logger().info(
            f"Planning for command: '{command}' "
            f"[attempt {_retry + 1}/{self._MAX_RETRIES + 1}] "
            f"with {len(detected_objects)} detected object(s)."
        )

        # ── Step 1: Query LLM ─────────────────────────────────────────
        self.get_logger().info("Querying Ollama LLM...")
        plan = self._llm.plan_task(
            command=command,
            detected_objects=detected_objects,
            named_poses=NAMED_POSES,
        )

        explanation = plan.get("explanation", "(no explanation)")
        tasks = plan.get("tasks", [])

        self.get_logger().info(f"LLM explanation: {explanation}")

        if not tasks:
            self.get_logger().warn("LLM returned an empty task list — nothing to execute.")
            return

        self.get_logger().info(f"LLM produced {len(tasks)} task(s):")
        for i, task in enumerate(tasks):
            self.get_logger().info(f"  [{i + 1}] {task}")

        # ── Step 2: Execute ────────────────────────────────────────────
        self.get_logger().info("Executing task list...")
        success = self._executor.execute_task_list(tasks)

        if success:
            self.get_logger().info("Task list executed successfully.")
        elif _retry < self._MAX_RETRIES:
            self.get_logger().warn(
                f"Execution failed (attempt {_retry + 1}/{self._MAX_RETRIES + 1}). "
                "Re-planning with failure context..."
            )
            recovery_command = (
                f"{command}. "
                f"NOTE: a previous {len(tasks)}-step plan failed. "
                "Generate a simpler, more conservative plan with fewer steps."
            )
            self._do_plan_and_execute(recovery_command, _retry=_retry + 1)
        else:
            self.get_logger().error(
                f"Task execution failed after {self._MAX_RETRIES + 1} attempts — giving up."
            )


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)
    node = LLMPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("LLMPlannerNode shutting down (KeyboardInterrupt).")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

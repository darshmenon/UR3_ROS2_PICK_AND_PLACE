#!/usr/bin/env python3
"""
Claude API client for LLM-driven robot task planning.

Converts natural language commands into structured robot action sequences
for the UR3 arm with Robotiq 2F-85 gripper.
"""

import json
import re

import anthropic


SYSTEM_PROMPT = """\
You are a task planner for a UR3 robot arm equipped with a Robotiq 2F-85 gripper.
Your role is to convert natural language commands into a structured sequence of robot actions.

ROBOT CAPABILITIES
==================
Robot: Universal Robots UR3 arm
Gripper: Robotiq 2F-85 (parallel jaw, 0–85 mm opening)
Base frame: base_link (right-hand coordinate system)
  - X: forward (away from mounting surface)
  - Y: left
  - Z: up

NAMED POSES
-----------
- home      : Safe retracted position, arm folded above base
- ready     : Arm extended forward at mid-height, ready to pick

AVAILABLE ACTIONS
-----------------
Each action is a JSON object. Supported action types:

1. Move to a named pose:
   {"action": "move_to_named_pose", "pose_name": "<home|ready>"}

2. Pick an object (arm moves above object, descends, closes gripper):
   {"action": "pick", "object_id": "<id>", "object_x": <float>, "object_y": <float>, "object_z": <float>}

3. Place at a Cartesian position (arm moves to position, opens gripper):
   {"action": "place", "x": <float>, "y": <float>, "z": <float>}

4. Open gripper fully:
   {"action": "open_gripper"}

5. Close gripper fully:
   {"action": "close_gripper"}

RESPONSE FORMAT
===============
Respond ONLY with a single valid JSON object — no markdown, no code fences, no commentary outside the JSON.

{
  "explanation": "<brief human-readable description of the plan>",
  "tasks": [
    <action object>,
    ...
  ]
}

PLANNING RULES
--------------
- Always start with "move_to_named_pose" (home or ready) unless picking immediately.
- Always open the gripper before a pick sequence.
- A pick sequence is: open_gripper → move_to_named_pose(ready) → pick → (lift handled internally).
- A place sequence is: place → open_gripper → move_to_named_pose(home).
- If no objects are detected and the command requires picking, explain that in "explanation" and return an empty "tasks" list.
- If a command is ambiguous, make a reasonable assumption and state it in "explanation".
- Positions are in metres relative to base_link.
- "to the left" means positive Y direction; "to the right" means negative Y.
- "in front" means positive X direction; "behind" means negative X.
- Place height (z) should be 0.05 m above the table surface unless told otherwise.
"""


class ClaudeClient:
    """Wraps the Anthropic Messages API to produce robot task plans."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        """
        Initialise the Claude client.

        Args:
            api_key: Anthropic API key.
            model:   Claude model identifier to use for planning.
        """
        self._model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def plan_task(
        self,
        command: str,
        detected_objects: list[dict],
        named_poses: list[str] | None = None,
    ) -> dict:
        """
        Send a natural language command to Claude and get a structured task plan.

        Args:
            command:          Natural language instruction (e.g. "pick the red box").
            detected_objects: List of dicts, each with keys:
                                id (str), label (str),
                                position (dict with x, y, z floats),
                                dimensions (dict with x, y, z floats),
                                confidence (float).
            named_poses:      List of available named pose strings (informational).

        Returns:
            dict with keys:
                "explanation" (str)  – Claude's description of the plan.
                "tasks"       (list) – Ordered list of action dicts.
        """
        if named_poses is None:
            named_poses = ["home", "ready"]

        # Build the user message content
        objects_description = self._format_objects(detected_objects)
        user_message = (
            f"COMMAND: {command}\n\n"
            f"CURRENTLY DETECTED OBJECTS ({len(detected_objects)} total):\n"
            f"{objects_description}\n\n"
            f"AVAILABLE NAMED POSES: {', '.join(named_poses)}\n\n"
            "Please produce the action plan as a JSON object."
        )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_message},
                ],
            )
        except anthropic.APIConnectionError as exc:
            return {
                "explanation": f"Failed to connect to Claude API: {exc}",
                "tasks": [],
            }
        except anthropic.AuthenticationError:
            return {
                "explanation": "Claude API authentication failed — check ANTHROPIC_API_KEY.",
                "tasks": [],
            }
        except anthropic.RateLimitError:
            return {
                "explanation": "Claude API rate limit exceeded. Please retry later.",
                "tasks": [],
            }
        except anthropic.APIStatusError as exc:
            return {
                "explanation": f"Claude API error {exc.status_code}: {exc.message}",
                "tasks": [],
            }

        raw_text = response.content[0].text.strip()
        return self._parse_response(raw_text)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_objects(detected_objects: list[dict]) -> str:
        """Return a human-readable summary of detected objects for the prompt."""
        if not detected_objects:
            return "  (none)"
        lines = []
        for obj in detected_objects:
            pos = obj.get("position", {})
            dims = obj.get("dimensions", {})
            lines.append(
                f"  - id={obj.get('id', '?')}  label=\"{obj.get('label', '?')}\"  "
                f"position=({pos.get('x', 0.0):.3f}, {pos.get('y', 0.0):.3f}, {pos.get('z', 0.0):.3f}) m  "
                f"dims=({dims.get('x', 0.0):.3f}x{dims.get('y', 0.0):.3f}x{dims.get('z', 0.0):.3f}) m  "
                f"confidence={obj.get('confidence', 0.0):.2f}"
            )
        return "\n".join(lines)

    @staticmethod
    def _parse_response(raw_text: str) -> dict:
        """
        Parse Claude's response text into a task plan dict.

        Handles cases where Claude wraps the JSON in a markdown code fence.
        """
        # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            return {
                "explanation": (
                    f"Claude returned a response that could not be parsed as JSON: {exc}\n"
                    f"Raw response:\n{raw_text}"
                ),
                "tasks": [],
            }

        if not isinstance(data, dict):
            return {
                "explanation": "Claude returned unexpected JSON structure (not an object).",
                "tasks": [],
            }

        explanation = data.get("explanation", "No explanation provided.")
        tasks = data.get("tasks", [])

        if not isinstance(tasks, list):
            return {
                "explanation": f"Claude 'tasks' field is not a list. Explanation: {explanation}",
                "tasks": [],
            }

        return {"explanation": explanation, "tasks": tasks}

#!/usr/bin/env python3
"""
Ollama HTTP client for LLM-driven robot task planning.

Uses a locally-running Ollama instance (https://ollama.ai) — no API key,
no cloud dependency. Supports any model Ollama has pulled:

    ollama pull llama3.2:3b      # fast, good for structured JSON
    ollama pull phi3:mini         # very fast, low RAM
    ollama pull mistral:7b        # better reasoning, needs ~8 GB RAM
    ollama pull llama3.1:8b       # best of the small models

Start server:   ollama serve
Pull a model:   ollama pull llama3.2:3b
"""

import json
import re
import urllib.request
import urllib.error


SYSTEM_PROMPT = """\
You are a task planner for a UR3 robot arm with a Robotiq 2F-85 gripper.
Convert natural language commands into a structured sequence of robot actions.

ROBOT SETUP
-----------
Robot: Universal Robots UR3 (6-DOF arm)
Gripper: Robotiq 2F-85 parallel jaw gripper
Base frame: base_link (right-hand coordinate system)
  X = forward, Y = left, Z = up

NAMED POSES
-----------
- home  : safe retracted position
- ready : arm extended forward at mid-height, ready to pick

AVAILABLE ACTIONS
-----------------
{"action": "move_to_named_pose", "pose_name": "home|ready"}
{"action": "pick", "object_id": "<id>", "object_x": <m>, "object_y": <m>, "object_z": <m>}
{"action": "place", "x": <m>, "y": <m>, "z": <m>}
{"action": "move_relative", "dx": <metres, signed float>, "dy": <metres, signed float>, "dz": <metres, signed float>}
{"action": "open_gripper"}
{"action": "close_gripper"}

RESPONSE FORMAT — return ONLY this JSON, no markdown, no extra text:
{
  "explanation": "<one sentence describing the plan>",
  "tasks": [<action>, ...]
}

RULES
-----
- Always start with move_to_named_pose(ready) before picking.
- A pick: open_gripper → move_to_named_pose(ready) → pick
- A place: place → open_gripper → move_to_named_pose(home)
- "left" = positive Y; "right" = negative Y; "forward" = positive X
- Place z = 0.05 m above table unless told otherwise
- If no objects detected and pick required: empty tasks list, explain why
- For "move up/down/left/right/forward/back [by N cm]" with no target object
  or coordinates given: use move_relative, NOT place. move_relative offsets
  from wherever the gripper currently is (you do not need to know that
  position) — up=+dz, down=-dz, forward=+dx, back=-dx, left=+dy, right=-dy.
  Default distance 0.10 m if not specified. Never guess an absolute
  place/pick coordinate for a relative instruction like this.
- move_relative's dx/dy/dz are ALWAYS in metres. If the command gives
  centimetres, DIVIDE by 100 before writing the number — never write the
  centimetre value directly. Worked example:
    Command: "move up by 10 centimeters"
    10 cm = 0.10 m, and "up" is +dz, so:
    {"action": "move_relative", "dx": 0.0, "dy": 0.0, "dz": 0.10}
  NOT {"dz": -10} and NOT {"dz": 10} — both of those are wrong (wrong sign,
  wrong units respectively).
"""


class OllamaClient:
    """
    Calls a local Ollama instance to produce robot task plans.

    No API key required. Ollama must be running and have the model pulled.
    """

    def __init__(
        self,
        model: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        self._model = model
        self._url = f"{base_url.rstrip('/')}/api/chat"
        self._timeout = timeout

    def plan_task(
        self,
        command: str,
        detected_objects: list,
        named_poses: list | None = None,
    ) -> dict:
        """
        Send a natural language command to Ollama and get a structured task plan.

        Args:
            command:          Natural language instruction.
            detected_objects: List of dicts with id, label, position, dimensions, confidence.
            named_poses:      Available named poses (informational).

        Returns:
            dict with "explanation" (str) and "tasks" (list).
        """
        if named_poses is None:
            named_poses = ["home", "ready"]

        objects_text = self._format_objects(detected_objects)
        user_message = (
            f"COMMAND: {command}\n\n"
            f"DETECTED OBJECTS ({len(detected_objects)}):\n{objects_text}\n\n"
            f"AVAILABLE NAMED POSES: {', '.join(named_poses)}\n\n"
            "Respond with the JSON plan only."
        )

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            "stream": False,
            "format": "json",      # Ollama forces JSON output mode
            "options": {
                "temperature": 0.1,   # low temperature → deterministic structured output
                "num_predict": 256,
            },
        }

        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                self._url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = json.loads(resp.read().decode())
        except urllib.error.URLError as exc:
            return {
                "explanation": (
                    f"Cannot reach Ollama at {self._url}: {exc}. "
                    "Is Ollama running? Run: ollama serve"
                ),
                "tasks": [],
            }
        except Exception as exc:
            return {"explanation": f"Ollama request failed: {exc}", "tasks": []}

        content = raw.get("message", {}).get("content", "")
        return self._parse_response(content)

    def is_available(self) -> bool:
        """Return True if Ollama server is reachable."""
        try:
            url = self._url.replace("/api/chat", "/api/version")
            with urllib.request.urlopen(url, timeout=3.0):
                return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_objects(detected_objects: list) -> str:
        if not detected_objects:
            return "  (none)"
        lines = []
        for obj in detected_objects:
            pos = obj.get("position", {})
            dims = obj.get("dimensions", {})
            lines.append(
                f"  id={obj.get('id','?')}  label=\"{obj.get('label','?')}\"  "
                f"pos=({pos.get('x',0):.3f}, {pos.get('y',0):.3f}, {pos.get('z',0):.3f})m  "
                f"dims=({dims.get('x',0):.3f}x{dims.get('y',0):.3f}x{dims.get('z',0):.3f})m  "
                f"conf={obj.get('confidence',0):.2f}"
            )
        return "\n".join(lines)

    @staticmethod
    def _parse_response(raw_text: str) -> dict:
        """Parse Ollama's JSON response, stripping any markdown fences."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            return {
                "explanation": f"LLM returned unparseable JSON: {exc}\nRaw: {raw_text[:300]}",
                "tasks": [],
            }

        if not isinstance(data, dict):
            return {"explanation": "LLM returned unexpected structure.", "tasks": []}

        tasks = data.get("tasks", [])
        if not isinstance(tasks, list):
            tasks = []

        return {
            "explanation": data.get("explanation", "No explanation."),
            "tasks": tasks,
        }

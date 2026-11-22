"""Offline tests for the VLM hint the LLM planner adds to the object list."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ur_llm_planner"))

from ur_llm_planner.ollama_client import apply_vlm_target


def _obj(oid, x=0.0):
    return {"id": oid, "label": oid, "position": {"x": x, "y": 0.0, "z": 0.1},
            "dimensions": {"x": 0.05, "y": 0.05, "z": 0.05}, "confidence": 0.5}


def test_no_hint_leaves_the_list_unchanged():
    objects = [_obj("a", 0.1), _obj("b", 0.2)]
    out = apply_vlm_target(objects, "", None)
    assert [o["id"] for o in out] == ["a", "b"]
    assert "vlm_target" not in out[0]
    assert objects[0]["position"]["x"] == 0.1


def test_matching_id_moves_to_front_and_pose_replaces_position():
    out = apply_vlm_target([_obj("a", 0.1), _obj("b", 0.2)], "b", (0.3, 0.4, 0.5))
    assert [o["id"] for o in out] == ["b", "a"]
    assert out[0]["vlm_target"] is True
    assert out[0]["position"] == {"x": 0.3, "y": 0.4, "z": 0.5}


def test_unknown_id_with_pose_is_added():
    out = apply_vlm_target([_obj("a")], "mug", (0.2, -0.1, 0.08))
    assert out[0]["id"] == "mug" and out[0]["vlm_target"] is True
    assert out[1]["id"] == "a"


def test_unknown_id_without_pose_does_nothing():
    out = apply_vlm_target([_obj("a")], "missing", None)
    assert [o["id"] for o in out] == ["a"]
    assert "vlm_target" not in out[0]

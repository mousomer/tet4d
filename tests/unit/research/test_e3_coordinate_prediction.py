"""Independent reference calculation for the draft E3 instrument fixtures."""

import json
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "e3_coordinate_prediction_v1.json"


def _rotate(item, direction):
    point = item["point"].copy()
    pivot = item["pivot"]
    axis_a, axis_b = item["plane"]
    offset_a = point[axis_a] - pivot[axis_a]
    offset_b = point[axis_b] - pivot[axis_b]
    assert (offset_a, offset_b) != (0, 0)
    point[axis_a] = pivot[axis_a] - direction * offset_b
    point[axis_b] = pivot[axis_b] + direction * offset_a
    return point


def _score(item, slot):
    response = slot["response"]
    if slot["status"] in {"interrupted", "unpresented"}:
        assert response is None
        return None, slot["status"]

    assert slot["status"] == "submitted"
    if (
        not isinstance(response, list)
        or len(response) != 4
        or any(type(coordinate) is not int for coordinate in response)
    ):
        return None, "invalid"
    if response == _rotate(item, item["turn"]):
        return 1, "correct"
    if response == item["point"]:
        return 0, "unchanged"
    if response == _rotate(item, -item["turn"]):
        return 0, "opposite_turn"
    return 0, "other_coordinate_error"


def test_e3_scored_fixtures_and_form_totals():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["scoring_version"] == 1
    for run in fixture["runs"]:
        slots = run["slots"]
        item_ids = fixture["forms"][run["form"]]["items"]
        scores = []
        for item_id, slot in zip(item_ids, slots, strict=True):
            score, outcome = _score(fixture["items"][item_id], slot)
            assert [score, outcome] == slot["expected"]
            if score is not None:
                scores.append(score)
        assert {
            "assigned": len(item_ids),
            "presented": sum(slot["status"] != "unpresented" for slot in slots),
            "valid": len(scores),
            "correct": sum(scores),
            "accuracy": sum(scores) / len(scores) if scores else None,
        } == run["expected"]


def test_e3_forms_have_disjoint_items_and_frozen_stimuli():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    item_ids = [
        item_id for form in fixture["forms"].values() for item_id in form["items"]
    ]
    assert len(set(item_ids)) == len(item_ids)
    stimuli = [
        json.dumps(fixture["items"][item_id], sort_keys=True) for item_id in item_ids
    ]
    assert len(set(stimuli)) == len(stimuli)

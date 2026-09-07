from __future__ import annotations

import json
from pathlib import Path

from tools.ui_export.exporter import export, load_runtime_screens, semantic_payload
from tools.ui_export.semantic_design import extract, node_count


def _write_probes(root: Path) -> Path:
    for implementation in ("python", "godot"):
        for mode in ("2d", "3d", "4d"):
            probe = {
                "probe": "fixture_v2",
                "implementation": implementation,
                "mode": mode,
                "capture_state": "plain_initial",
                "source": "unit fixture",
                "viewport": [100, 80],
                "root": {
                    "semantic_id": "game_screen",
                    "kind": "screen",
                    "bounds": [0, 0, 100, 80],
                    "visible": True,
                    "children": [
                        {"semantic_id": "board", "kind": "viewport", "semantic_role": "gameplay_viewport", "bounds": [0, 0, 60, 80], "visible": True},
                        {"semantic_id": "piece_controls", "kind": "frame", "semantic_role": "piece_controls", "bounds": [60, 0, 40, 80], "visible": True, "children": [{"semantic_id": "action", "kind": "text", "semantic_role": "action_button", "bounds": [60, 0, 40, 20], "visible": True, "text": "Line one\nLine two"}]},
                    ],
                },
            }
            probe["root"]["children"].extend(
                {
                    "semantic_id": f"generated_margin_{index}",
                    "kind": "frame",
                    "bounds": [0, 0, 1, 1],
                    "visible": True,
                }
                for index in range(50)
            )
            target = root / implementation / f"game_{mode}.probe.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n")
    return root


def test_exports_all_canonical_screens_deterministically(tmp_path):
    probes = _write_probes(tmp_path / "probes")
    first = export(tmp_path / "one", commit="test-commit", probes=probes)
    second = export(tmp_path / "two", commit="test-commit", probes=probes)
    assert first == second
    assert {(s["provenance"]["implementation"], s["provenance"]["mode"]) for s in first} == {
        (implementation, mode)
        for implementation in ("python", "godot")
        for mode in ("2d", "3d", "4d")
    }
    assert all("/" + "Users/" not in json.dumps(screen) for screen in first)


def test_semantic_payload_keeps_semantic_layers_and_provenance(tmp_path):
    screens = export(tmp_path, commit="test-commit", probes=_write_probes(tmp_path / "probes"))
    payload = semantic_payload(screens)
    assert payload["format"] == "tet4d.semantic-export.v1"
    assert len(payload["screens"]) == 6
    def descendants(node):
        for child in node.get("children", []):
            yield child
            yield from descendants(child)

    assert any(child["kind"] == "text" for child in descendants(payload["screens"][0]["root"]))
    assert all(child["provenance"]["runtime_ids"] for child in descendants(payload["screens"][1]["root"]))


def test_runtime_probes_are_the_layout_authority(tmp_path):
    probes = _write_probes(tmp_path / "probes")
    screens = load_runtime_screens(probes=probes, commit="test-commit")
    assert len(screens) == 6
    assert all(screen["root"]["bounds"] == {"x": 0, "y": 0, **screen["provenance"]["resolution"]} for screen in screens)
    assert all(screen["provenance"]["probe"].endswith("_v2") for screen in screens)
    assert all((probes / screen["provenance"]["implementation"] / f"game_{screen['provenance']['mode']}.probe.json").is_file() for screen in screens)
    payload = semantic_payload(export(tmp_path / "output", commit="test-commit", probes=probes))
    assert len(payload["screens"]) == 6


def test_semantic_projection_is_deterministic_and_materially_compact(tmp_path):
    raw = export(tmp_path, commit="test-commit", probes=_write_probes(tmp_path / "probes"))
    first = extract(raw)
    second = extract(raw)
    assert first == second
    assert node_count(first) < node_count(raw) // 10
    assert node_count(first) < 1_000
    godot = [screen for screen in first if screen["provenance"]["implementation"] == "godot"]
    assert all(3 <= node_count([screen]) <= 200 for screen in godot)


def test_semantic_projection_preserves_regions_controls_and_provenance(tmp_path):
    semantic = extract(export(tmp_path, commit="test-commit", probes=_write_probes(tmp_path / "probes")))
    def walk(node):
        yield node
        for child in node.get("children", []):
            yield from walk(child)
    nodes = [node for screen in semantic for node in walk(screen["root"])]
    roles = {node["role"] for node in nodes}
    assert {"gameplay_viewport", "piece_controls", "action_button"} <= roles
    assert all(node["provenance"]["runtime_ids"] for node in nodes)
    assert not any("generated_margin" in node["semantic_id"] for node in nodes)


def test_multiline_text_round_trips_as_real_newlines(tmp_path):
    """Guard the escaping bug where a lost backslash left literal ``u000a``.

    Rewriting serialized JSON text cannot see escape boundaries, so any such
    pass corrupts multi-line labels.  Assert on the bytes and on the reparsed
    values for the probes and the semantic export.
    """
    probes = _write_probes(tmp_path / "probes")
    export(tmp_path / "output", commit="test-commit", probes=probes)
    generated = sorted((tmp_path / "output").rglob("*.json"))
    assert generated
    sources = [*generated, *sorted(probes.rglob("*.probe.json"))]
    for path in sources:
        raw = path.read_text()
        assert "u000a" not in raw, f"corrupted newline escape in {path}"
        assert chr(92) + "u003a" not in raw, f"needlessly escaped colon in {path}"

    def strings(node):
        if isinstance(node, dict):
            for value in node.values():
                yield from strings(value)
        elif isinstance(node, list):
            for value in node:
                yield from strings(value)
        elif isinstance(node, str):
            yield node

    values = [text for path in sources for text in strings(json.loads(path.read_text()))]
    assert any(chr(10) in text for text in values), "expected multi-line label text"
    assert not any(chr(92) + "n" in text for text in values), "literal backslash-n in text"

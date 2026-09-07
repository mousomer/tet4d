"""Normalize Stage 55 runtime probe records into a semantic export.

Runtime probes are the only authority for hierarchy, geometry, text,
visibility, and semantic placement. Screenshots are never exporter inputs.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ui_export.semantic_design import extract, inventory

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "tet4d.ui-bootstrap.v2"
PROBES = ROOT / "design/bootstrap/probes"


def _commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def _bounds(value: list[int] | dict[str, int]) -> dict[str, int]:
    if isinstance(value, dict):
        return {key: int(value[key]) for key in ("x", "y", "width", "height")}
    if len(value) == 2:
        return {"x": 0, "y": 0, "width": int(value[0]), "height": int(value[1])}
    return dict(zip(("x", "y", "width", "height"), map(int, value), strict=True))


def _json(value: Any) -> str:
    """Serialize with standard JSON escapes.

    Rewriting the *serialized* text with str.replace cannot see escape
    boundaries: it rewrites the trailing backslash of an escaped backslash and
    corrupts the value.  Escaping belongs to the serializer alone.
    """
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _normalize_node(node: dict[str, Any]) -> dict[str, Any]:
    result = {
        "semantic_id": str(node["semantic_id"]),
        "kind": str(node.get("kind", "frame")),
        "bounds": _bounds(node["bounds"]),
        "visible": bool(node.get("visible", True)),
        "semantic_role": str(node.get("semantic_role", node.get("kind", "frame"))),
    }
    for key in ("text", "style", "provenance"):
        if key in node:
            result[key] = node[key]
    children = [_normalize_node(child) for child in node.get("children", [])]
    if children:
        result["children"] = children
    return result


def _screen_from_probe(path: Path, commit: str) -> dict[str, Any]:
    probe = json.loads(path.read_text())
    root = _normalize_node(probe["root"])
    viewport = _bounds(probe["viewport"])
    if root["bounds"] != viewport:
        raise ValueError(f"probe root does not match viewport: {path}")
    return {
        "schema_version": SCHEMA_VERSION,
        "provenance": {
            "implementation": str(probe["implementation"]),
            "mode": str(probe["mode"]),
            "source_commit": commit,
            "probe": probe["probe"],
            "capture_state": probe["capture_state"],
            "resolution": {"width": viewport["width"], "height": viewport["height"]},
            "source": probe["source"],
        },
        "root": root,
    }


def load_runtime_screens(
    probes: Path = PROBES, commit: str | None = None
) -> list[dict[str, Any]]:
    commit = commit or _commit()
    return [
        _screen_from_probe(probes / implementation / f"game_{mode}.probe.json", commit)
        for implementation in ("python", "godot")
        for mode in ("2d", "3d", "4d")
    ]


def semantic_payload(
    screens: list[dict[str, Any]], projection: str = "semantic"
) -> dict[str, Any]:
    """Create a neutral semantic or runtime-node export.

    This artifact is an on-demand inspection aid. It does not establish a
    design-tool workflow or become a runtime/layout authority.
    """
    if projection == "semantic":
        screens = extract(screens)
    elif projection != "runtime":
        raise ValueError(f"unknown projection: {projection}")
    return {
        "format": "tet4d.semantic-export.v1",
        "projection": projection,
        "name": "Tet4D semantic UI export" if projection == "semantic" else "Tet4D runtime UI export",
        "design_inventory": inventory(screens) if projection == "semantic" else {},
        "screens": screens,
    }


def export(
    output: Path,
    commit: str | None = None,
    probes: Path = PROBES,
    projection: str = "semantic",
) -> list[dict[str, Any]]:
    screens = load_runtime_screens(probes, commit)
    name = "semantic_ui.json" if projection == "semantic" else "runtime_ui.json"
    artifact = output / projection / name
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(_json(semantic_payload(screens, projection)))
    return screens


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "design/bootstrap")
    parser.add_argument("--probes", type=Path, default=PROBES)
    parser.add_argument(
        "--projection", choices=("semantic", "runtime"), default="semantic"
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp)
            expected = args.output
            name = "semantic_ui.json" if args.projection == "semantic" else "runtime_ui.json"
            expected_artifact = expected / args.projection / name
            payload = json.loads(expected_artifact.read_text())
            captured_commit = payload["screens"][0]["provenance"]["source_commit"]
            export(
                generated,
                commit=captured_commit,
                probes=args.probes,
                projection=args.projection,
            )
            relative = Path(args.projection) / name
            if (generated / relative).read_bytes() != expected_artifact.read_bytes():
                raise SystemExit(f"UI export drift: {relative}")
        return
    export(args.output, projection=args.projection)


if __name__ == "__main__":
    main()

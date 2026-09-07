"""Derived, non-authoritative semantic projection for runtime UI probes.

The rules in this module classify evidence already present in a runtime probe.
They intentionally contain neither screen coordinates nor per-screen trees.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

GENERIC_ROLES = {"", "frame", "container", "text", "screen"}


def _walk(node: dict[str, Any]):
    yield node
    for child in node.get("children", []):
        yield from _walk(child)


def _meaningful(node: dict[str, Any]) -> bool:
    """Keep runtime-declared regions and controls; discard implementation plumbing."""
    if not node.get("visible", True):
        return False
    role = str(node.get("semantic_role", ""))
    # `generated` is reported by the probe, which knows the runtime node's real
    # identity. It is deliberately the only signal used here: `semantic_id` is a
    # full ancestor path, so any pattern match against it also matches every
    # descendant and would discard real controls nested under a generated
    # wrapper.
    if bool(node.get("generated", False)):
        return False
    if node.get("kind") == "viewport" or role not in GENERIC_ROLES:
        return True
    # A named runtime control remains independently editable.  Generated labels
    # and containers are represented by their nearest meaningful ancestor.
    return bool(node.get("text"))


def _name(node: dict[str, Any]) -> str:
    text = str(node.get("text", "")).strip().split("\n", 1)[0]
    if text and len(text) <= 48:
        return text
    source = str(node["semantic_id"]).split("__")[-1]
    source = source or str(node.get("semantic_role", "region"))
    return source.replace("_", " ").title()


def _style(node: dict[str, Any]) -> dict[str, Any]:
    return dict(node.get("style", {}))


def _semantic_kind(node: dict[str, Any]) -> str:
    kind = str(node.get("kind", "container"))
    return kind if kind in {"screen", "viewport", "text"} else "container"


def _semantic_role(node: dict[str, Any]) -> str:
    role = str(node.get("semantic_role", node.get("kind", "container")))
    return "container" if role == "frame" else role


def _semantic_id(node: dict[str, Any]) -> str:
    # Runtime identity is retained as provenance; this stable, readable ID is
    # only the derived design object's identity.
    name = re.sub(r"[^a-z0-9]+", "_", _name(node).lower()).strip("_")
    return f"design_{name or 'region'}_{str(node['semantic_id']).rsplit('__', 1)[-1][-12:]}"


def _retained_nodes(
    root: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    retained: dict[str, dict[str, Any]] = {root["semantic_id"]: root}
    parent: dict[str, str] = {}

    def visit(node: dict[str, Any], retained_parent: dict[str, Any]) -> None:
        keep = _meaningful(node)
        current_parent = retained_parent
        if keep:
            retained[node["semantic_id"]] = node
            parent[node["semantic_id"]] = retained_parent["semantic_id"]
            current_parent = node
        for child in node.get("children", []):
            visit(child, current_parent)

    for child in root.get("children", []):
        visit(child, root)
    return retained, parent


def extract_screen(screen: dict[str, Any]) -> dict[str, Any]:
    """Compress one normalized runtime screen into a provenance-complete tree."""
    root = screen["root"]
    retained, parent = _retained_nodes(root)

    evidence: dict[str, list[str]] = {key: [key] for key in retained}
    for node in _walk(root):
        source = node["semantic_id"]
        if source in retained:
            continue
        # The traversal parent map is constructed from retained nodes, so find
        # the closest retained identity by path-prefix, not layout assumptions.
        candidates = [key for key in retained if source.startswith(key + "__")]
        target = max(candidates, key=len) if candidates else root["semantic_id"]
        evidence[target].append(source)

    models: dict[str, dict[str, Any]] = {}
    for source, node in retained.items():
        models[source] = {
            "semantic_id": _semantic_id(node)
            if source != root["semantic_id"]
            else "design_game_screen",
            "name": _name(node)
            if source != root["semantic_id"]
            else f"{screen['provenance']['mode'].upper()} Game",
            "role": _semantic_role(node),
            "kind": _semantic_kind(node),
            "bounds": node["bounds"],
            "visible": node.get("visible", True),
            "style": _style(node),
            "provenance": {
                "runtime_ids": sorted(evidence[source]),
                "probe": screen["provenance"]["probe"],
            },
            "children": [],
        }
        if node.get("text"):
            models[source]["text"] = node["text"]
    for source, model in models.items():
        if source != root["semantic_id"]:
            models[parent[source]]["children"].append(model)
    return {
        "schema_version": "tet4d.semantic-projection.v1",
        "provenance": screen["provenance"],
        "root": models[root["semantic_id"]],
    }


def extract(screens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [extract_screen(screen) for screen in screens]


def node_count(screens: list[dict[str, Any]]) -> int:
    return sum(1 for screen in screens for _ in _walk(screen["root"]))


def inventory(screens: list[dict[str, Any]]) -> dict[str, int]:
    return dict(
        sorted(
            Counter(
                node["role"] for screen in screens for node in _walk(screen["root"])
            ).items()
        )
    )

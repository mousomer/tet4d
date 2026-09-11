"""Reject consumed-field declarations with no observable implementation effect."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.unit.workspace_governance.support import PACK, ROOT, write
from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators import core

LOCAL = {
    "schema_version": 1,
    "interpreter": sys.executable,
    "tool_paths": {"godot": sys.executable},
}


def _leaves(node: dict, candidates: list, label: str):
    if "properties" in node:
        for name, child in node["properties"].items():
            yield from _leaves(
                child,
                [(v[name], (*p, name)) for v, p in candidates if name in v],
                label + "." + name,
            )
    elif "properties" in node.get("items", {}):
        yield from _leaves(
            node["items"],
            [
                (item, (*p, i))
                for values, p in candidates
                for i, item in enumerate(values)
            ],
            label + "[]",
        )
    elif (
        isinstance(node.get("additionalProperties"), dict)
        and "properties" in node["additionalProperties"]
    ):
        yield from _leaves(
            node["additionalProperties"],
            [(item, (*p, k)) for values, p in candidates for k, item in values.items()],
            label + ".*",
        )
    elif node.get("x-governance-use") == "consumed":
        # New optional fields need an actual representative value, not only a tag.
        assert candidates, f"Consumed field has no behavioral fixture: {label}"
        yield label, candidates[0][1]


def _cases():
    for layer, rel, data in (
        (
            "workspace",
            "workspace",
            json.loads((ROOT / ".governance/workspace.json").read_text()),
        ),
        (
            "project",
            "project",
            json.loads((ROOT / "config/governance/project.json").read_text()),
        ),
        ("local", "workspace-local", LOCAL),
    ):
        schema = json.loads((PACK / "schemas" / (rel + ".schema.json")).read_text())
        for label, path in _leaves(schema, [(data, ())], layer):
            yield label, layer, path


def _mutate(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, str):
        return value + "__changed"
    if isinstance(value, list):
        return [_mutate(value[0]), *value[1:]] if value else ["changed"]
    if isinstance(value, dict):
        key = next(iter(value))
        return {**value, key: _mutate(value[key])}
    raise AssertionError(f"Add a meaningful mutation for {value!r}")


def _observe(root: Path, calls: list) -> str:
    calls.clear()
    observed = []
    try:
        resolver = GovernanceResolver.for_root(root)
        workspace, project, local = resolver.load()
        # Deliberately bypass schema validation: an invalid-type/enum rejection
        # alone cannot prove that a field is consumed by implementation.
        for task in [None, *[" ".join(s["match_all"]) for s in BASE_SCENARIOS]]:
            for mode in ("LOCAL_FIX", "FEATURE", "STRUCTURAL_CHANGE"):
                observed.append(resolver.resolve(mode=mode, task=task))
        for authority in project["authorities"]:
            observed.append(resolver.explain("authority:" + authority["authority_id"]))
        observed.extend(
            i.to_dict()
            for i in core._semantic_manifest_issues(root, workspace, project)
        )
        observed.extend(
            i.to_dict() for i in core._authority_graph_issues(root, project)
        )
        observed.extend(i.to_dict() for i in core.validate_pack(root, workspace))
        for overlay in (None, local):
            for env in (
                {},
                {"TET4D_PYTHON": sys.executable, "GODOT_BIN": sys.executable},
            ):
                data, issues = core.doctor(
                    root, project, overlay, env, route="godot_product_shell"
                )
                observed.append([data, [i.to_dict() for i in issues]])
        # A transform selector must also affect validation when its input drifts.
        policy_path = root / "config/project/policy_pack.json"
        original = policy_path.read_text()
        try:
            policy = json.loads(original)
            policy["codex_routing"]["routes"] = {}
            write(policy_path, policy)
            observed.extend(
                i.to_dict() for i in core._generated_surface_issues(root, project)
            )
        finally:
            policy_path.write_text(original)
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        observed.append([type(exc).__name__, str(exc)])
    return json.dumps([observed, calls], sort_keys=True)


BASE_SCENARIOS = json.loads((ROOT / "config/governance/project.json").read_text())[
    "execution"
]["representative_scenarios"]


@pytest.mark.parametrize("label,layer,path", list(_cases()), ids=lambda item: str(item))
def test_every_consumed_leaf_changes_execution(
    checkout: Path, monkeypatch: pytest.MonkeyPatch, label: str, layer: str, path: tuple
) -> None:
    calls = []

    def probe(command, **kwargs):
        calls.append(command)
        if "from packaging.specifiers" in command[-1]:
            stdout = "3.14.0"
        elif "import importlib,json" in command[-1]:
            stdout = json.dumps(
                {
                    "version": "3.14.0",
                    "package": str((checkout / "src/tet4d/__init__.py").resolve()),
                    "critical_packages": [],
                }
            )
        else:
            stdout = "tool-version"
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(core.subprocess, "run", probe)
    monkeypatch.setattr(core.shutil, "which", lambda value: "/resolved/" + value)
    monkeypatch.setattr(GovernanceResolver, "check", lambda self: [])
    preferred = checkout / ".venv/bin/python"
    preferred.parent.mkdir(parents=True)
    preferred.write_text("#!/bin/sh\nexit 0\n")
    preferred.chmod(0o755)
    local_path = checkout / ".governance/workspace.local.json"
    write(local_path, LOCAL)
    before = _observe(checkout, calls)
    paths = {
        "workspace": checkout / ".governance/workspace.json",
        "project": checkout / "config/governance/project.json",
        "local": local_path,
    }
    payload = json.loads(paths[layer].read_text())
    parent = payload
    for token in path[:-1]:
        parent = parent[token]
    parent[path[-1]] = _mutate(copy.deepcopy(parent[path[-1]]))
    write(paths[layer], payload)
    assert _observe(checkout, calls) != before, (
        f"Consumed declaration has no observed effect: {label}"
    )

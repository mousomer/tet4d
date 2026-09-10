from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.workspace_governance.validators.core import (
    Diagnostic,
    load_manifest_json,
    validate_manifests,
    validate_pack,
)


class GovernanceError(ValueError):
    def __init__(self, diagnostics: list[Diagnostic]):
        super().__init__(diagnostics[0].reason if diagnostics else "governance error")
        self.diagnostics = diagnostics


@dataclass(frozen=True)
class GovernanceResolver:
    root: Path
    workspace_path: Path
    project_path: Path
    local_path: Path | None

    @classmethod
    def for_root(cls, root: Path) -> GovernanceResolver:
        local = root / ".governance/workspace.local.json"
        return cls(
            root.resolve(),
            root / ".governance/workspace.json",
            root / "config/governance/project.json",
            local if local.exists() else None,
        )

    def load(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
        return (
            load_manifest_json(self.workspace_path),
            load_manifest_json(self.project_path),
            load_manifest_json(self.local_path) if self.local_path else None,
        )

    def check(self) -> list[Diagnostic]:
        try:
            workspace, project, local = self.load()
        except (OSError, ValueError) as exc:
            return [
                Diagnostic(
                    "BROKEN_REFERENCE",
                    "manifest",
                    "workspace/project",
                    (str(self.workspace_path), str(self.project_path)),
                    str(exc),
                    "restore valid strict JSON manifests",
                )
            ]
        return validate_manifests(self.root, workspace, project, local) + validate_pack(
            self.root, workspace
        )

    def resolve(  # noqa: C901 - resolution retains one provenance transaction
        self, *, task: str | None = None, mode: str | None = None
    ) -> dict[str, Any]:
        issues = self.check()
        if issues:
            raise GovernanceError(issues)
        workspace, project, local = self.load()
        profiles = project["execution"]["profiles"]
        selected = mode or project["execution"]["default_mode"]
        matched_scenario = None
        scenario_routes = None
        if task:
            task_lower = task.lower()
            for scenario in project["execution"].get("representative_scenarios", []):
                if all(
                    token.lower() in task_lower
                    for token in scenario.get("match_all", [])
                ):
                    selected = scenario["mode"]
                    matched_scenario = scenario["id"]
                    scenario_routes = scenario.get("routes")
                    break
        if selected not in profiles:
            raise GovernanceError(
                [
                    Diagnostic(
                        "BROKEN_REFERENCE",
                        "execution.mode",
                        "project",
                        ("config/governance/project.json",),
                        f"unknown execution mode {selected}",
                        "select a declared execution profile",
                    )
                ]
            )
        authority_map = {a["authority_id"]: a for a in project["authorities"]}
        route_ids = scenario_routes or profiles[selected]["routes"]
        routes = {route_id: project["routes"][route_id] for route_id in route_ids}
        authority_ids = sorted(
            {aid for route in routes.values() for aid in route["authority_refs"]}
        )

        def sourced(value: Any, owner: str, source: str) -> dict[str, Any]:
            return {"value": value, "owner": owner, "source": source}

        def referenced_fact(spec: object) -> dict[str, Any]:
            if not isinstance(spec, dict):
                return sourced(spec, "project", "config/governance/project.json")
            authority_id = spec.get("authority_ref")
            pointer = spec.get("json_pointer")
            authority = authority_map.get(authority_id)
            if (
                not authority
                or not isinstance(pointer, str)
                or not pointer.startswith("/")
            ):
                raise GovernanceError(
                    [
                        Diagnostic(
                            "BROKEN_REFERENCE",
                            "verification",
                            "project",
                            ("config/governance/project.json",),
                            "verification fact has an invalid authority reference",
                            "reference a declared JSON authority and valid JSON pointer",
                        )
                    ]
                )
            value: Any = load_manifest_json(self.root / authority["source"])
            try:
                for token in pointer.removeprefix("/").split("/"):
                    value = value[token.replace("~1", "/").replace("~0", "~")]
            except (KeyError, TypeError) as exc:
                raise GovernanceError(
                    [
                        Diagnostic(
                            "BROKEN_REFERENCE",
                            pointer,
                            str(authority_id),
                            (authority["source"],),
                            f"authority JSON pointer does not resolve: {exc}",
                            "repair the reference or restore the authority field",
                        )
                    ]
                ) from exc
            return sourced(value, str(authority_id), f"{authority['source']}#{pointer}")

        return {
            "schema_version": 1,
            "project": sourced(
                project["project"]["id"], "project", "config/governance/project.json"
            ),
            "workspace": sourced(
                workspace["workspace_id"], "workspace", ".governance/workspace.json"
            ),
            "execution.mode": sourced(
                selected, "project", "config/governance/project.json"
            ),
            "execution.exploration": sourced(
                profiles[selected]["exploration"],
                "project",
                "config/governance/project.json",
            ),
            "verification.full": referenced_fact(project["verification"]["full"]),
            "verification.rule": sourced(
                "task + authority + actual diff + risk",
                "project",
                "config/governance/project.json",
            ),
            "routes": sourced(route_ids, "project", "config/governance/project.json"),
            "authorities": sourced(
                [
                    {
                        **authority_map[aid],
                        "ownership_layer": "human"
                        if authority_map[aid]["authority_type"] == "human"
                        else "project",
                    }
                    for aid in authority_ids
                ],
                "project references",
                "config/governance/project.json",
            ),
            "matched_scenario": sourced(
                matched_scenario, "project", "config/governance/project.json"
            )
            if matched_scenario
            else None,
            "local_overlay": sourced(
                str(self.local_path.relative_to(self.root)),
                "local",
                str(self.local_path.relative_to(self.root)),
            )
            if local
            else None,
        }

    def explain(
        self, query: str | None = None, *, task: str | None = None
    ) -> dict[str, Any]:
        resolved = self.resolve(task=task)
        if task:
            return resolved
        if query and query.startswith("authority:"):
            authority_id = query.split(":", 1)[1]
            _, project, _ = self.load()
            values = project["authorities"]
            for value in values:
                if value["authority_id"] == authority_id:
                    return {
                        "query": query,
                        "resolved": value,
                        "execution_mode": resolved["execution.mode"],
                        "verification": resolved["verification.rule"],
                    }
            raise GovernanceError(
                [
                    Diagnostic(
                        "BROKEN_REFERENCE",
                        query,
                        "project",
                        ("config/governance/project.json",),
                        "unknown authority ID",
                        "use a declared stable authority ID",
                    )
                ]
            )
        if query not in resolved:
            raise GovernanceError(
                [
                    Diagnostic(
                        "BROKEN_REFERENCE",
                        query or "query",
                        "resolved",
                        ("ephemeral resolution",),
                        "unknown resolved key",
                        "request a key emitted by gov resolve",
                    )
                ]
            )
        return {
            "query": query,
            "resolved": resolved[query],
            "execution_mode": resolved["execution.mode"],
            "verification": resolved["verification.rule"],
        }


__all__ = ["Diagnostic", "GovernanceError", "GovernanceResolver"]

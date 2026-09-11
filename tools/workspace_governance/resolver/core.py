from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.workspace_governance.validators.core import (
    Diagnostic,
    load_manifest_json,
    validate_manifests,
    validate_pack,
)

USER_OVERLAY_DIR = "workspace-governance"
# A workspace id becomes a filename, so it may not contain anything that could
# address a different directory. The shell bootstrap resolver applies the same
# rule; both derive one path and must agree on what is addressable.
SAFE_WORKSPACE_ID = re.compile(r"^[A-Za-z0-9._-]+$")


def user_overlay_path(
    workspace_id: str, environ: dict[str, str] | None = None
) -> Path | None:
    """Locate the machine-wide overlay shared by every checkout of a workspace.

    Keyed by workspace identity rather than checkout path so a worktree
    inherits it wherever it lives, and honouring XDG_CONFIG_HOME so a test or
    an operator can substitute an isolated configuration root. Returns None for
    an identity that cannot safely become a filename.
    """
    if not SAFE_WORKSPACE_ID.match(workspace_id):
        return None
    env = os.environ if environ is None else environ
    base = env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base).expanduser() / USER_OVERLAY_DIR / f"{workspace_id}.local.json"


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
    user_local_path: Path | None = None

    @classmethod
    def for_root(cls, root: Path) -> GovernanceResolver:
        root = root.resolve()
        workspace_path = root / ".governance/workspace.json"
        project_path = root / "config/governance/project.json"
        user_local: Path | None = None
        try:
            workspace = load_manifest_json(workspace_path)
            default_id = workspace["defaults"]["project"]
            members = [
                item for item in workspace["projects"] if item["id"] == default_id
            ]
            if len(members) == 1:
                project_path = root / members[0]["repository"] / members[0]["manifest"]
            inherited = user_overlay_path(str(workspace["workspace_id"]))
            if inherited is not None and inherited.is_file():
                user_local = inherited
        except (OSError, ValueError, TypeError, KeyError):
            # check() owns the bounded diagnostic; construction remains total.
            pass
        local = root / ".governance/workspace.local.json"
        return cls(
            root,
            workspace_path,
            project_path,
            local if local.exists() else None,
            user_local,
        )

    def local_documents(self) -> list[tuple[dict[str, Any], str, str]]:
        """Return overlays lowest-precedence first as (payload, tier, source)."""
        documents: list[tuple[dict[str, Any], str, str]] = []
        for path, tier in (
            (self.user_local_path, "workspace"),
            (self.local_path, "local"),
        ):
            if path is not None:
                documents.append((load_manifest_json(path), tier, self._source(path)))
        return documents

    def local_overlay(self) -> tuple[dict[str, Any] | None, dict[str, str]]:
        """Layer overlays per key so a repository setting overrides an inherited one.

        Merging by key rather than by document keeps a repository overlay that
        names only `tool_paths` from silently discarding the inherited
        interpreter.
        """
        merged: dict[str, Any] = {}
        tiers: dict[str, str] = {}
        for payload, tier, _ in self.local_documents():
            for key, value in payload.items():
                merged[key], tiers[key] = value, tier
        return (merged or None), tiers

    def load(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
        return (
            load_manifest_json(self.workspace_path),
            load_manifest_json(self.project_path),
            self.local_overlay()[0],
        )

    def _source(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def check(self) -> list[Diagnostic]:
        try:
            documents = self.local_documents()
        except (OSError, ValueError, TypeError, KeyError) as exc:
            # Name the overlays themselves: a malformed inherited overlay must
            # not be reported against the tracked workspace manifests.
            return [
                Diagnostic(
                    "BROKEN_REFERENCE",
                    "manifest",
                    "local",
                    tuple(
                        self._source(path)
                        for path in (self.user_local_path, self.local_path)
                        if path is not None
                    ),
                    str(exc),
                    "restore valid strict JSON in the local interpreter overlays",
                )
            ]
        try:
            workspace, project, local = self.load()
            lock = load_manifest_json(self.root / workspace["governance_pack"]["lock"])
            pack_root = self.root / lock["pack_path"]
        except (OSError, ValueError, TypeError, KeyError) as exc:
            return [
                Diagnostic(
                    "BROKEN_REFERENCE",
                    "manifest",
                    "workspace/project",
                    (
                        self._source(self.workspace_path),
                        self._source(self.project_path),
                    ),
                    str(exc),
                    "restore valid strict JSON manifests and a resolvable pack lock",
                )
            ]
        return validate_manifests(
            self.root,
            workspace,
            project,
            local,
            pack_root=pack_root,
            local_documents=[(payload, source) for payload, _, source in documents],
        ) + validate_pack(self.root, workspace)

    def resolve(
        self, *, task: str | None = None, mode: str | None = None
    ) -> dict[str, Any]:
        issues = self.check()
        if issues:
            raise GovernanceError(issues)
        workspace, project, local = self.load()
        project_source = self._source(self.project_path)
        workspace_source = self._source(self.workspace_path)
        profiles = project["execution"]["profiles"]
        selected = mode or project["execution"]["default_mode"]
        matched_scenario: str | None = None
        scenario_routes: list[str] | None = None
        if task:
            task_lower = task.lower()
            for scenario in project["execution"]["representative_scenarios"]:
                if all(token.lower() in task_lower for token in scenario["match_all"]):
                    selected, matched_scenario, scenario_routes = (
                        scenario["mode"],
                        scenario["id"],
                        scenario["routes"],
                    )
                    break
        if selected not in profiles:
            raise GovernanceError(
                [
                    Diagnostic(
                        "BROKEN_REFERENCE",
                        "execution.mode",
                        "project",
                        (project_source,),
                        f"unknown execution mode {selected}",
                        "select a declared execution profile",
                    )
                ]
            )

        authority_map = {item["authority_id"]: item for item in project["authorities"]}
        route_ids = scenario_routes or profiles[selected]["routes"]
        routes = {route_id: project["routes"][route_id] for route_id in route_ids}
        authority_ids = sorted(
            {item for route in routes.values() for item in route["authority_refs"]}
        )

        def entry(value: Any, owner: str, source: str) -> dict[str, Any]:
            return {"value": value, "owner": owner, "source": source}

        def referenced_fact(spec: dict[str, Any]) -> dict[str, Any]:
            authority_id, pointer = spec["authority_ref"], spec["json_pointer"]
            authority = authority_map[authority_id]
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
                            authority_id,
                            (authority["source"],),
                            f"authority JSON pointer does not resolve: {exc}",
                            "repair the reference or restore the authority field",
                        )
                    ]
                ) from exc
            return entry(value, authority_id, f"{authority['source']}#{pointer}")

        entries = {
            "workspace.id": entry(
                workspace["workspace_id"], "workspace", workspace_source
            ),
            "project.id": entry(project["project"]["id"], "project", project_source),
            "project.name": entry(
                project["project"]["name"], "project", project_source
            ),
            "execution.mode": entry(
                selected, "project", f"{project_source}#/execution"
            ),
            "execution.exploration": entry(
                profiles[selected]["exploration"],
                "project",
                f"{project_source}#/execution/profiles/{selected}",
            ),
            "execution.final_evidence_rule": entry(
                profiles[selected]["final_evidence_rule"],
                "project",
                f"{project_source}#/execution/profiles/{selected}",
            ),
            "verification.canonical": referenced_fact(
                project["verification"]["canonical"]
            ),
            "verification.full": referenced_fact(project["verification"]["full"]),
            "verification.targeted": entry(
                project["verification"]["targeted"],
                "project",
                f"{project_source}#/verification/targeted",
            ),
            "verification.rule": entry(
                project["verification"]["rule"],
                "project",
                f"{project_source}#/verification/rule",
            ),
            "routes": entry(routes, "project", f"{project_source}#/routes"),
            "authorities": entry(
                [authority_map[item] for item in authority_ids],
                "project",
                f"{project_source}#/authorities",
            ),
            "matched_scenario": entry(
                matched_scenario,
                "project",
                f"{project_source}#/execution/representative_scenarios",
            ),
            "local_overlay": entry(
                self._source(self.local_path) if local and self.local_path else None,
                "local",
                self._source(self.local_path)
                if self.local_path
                else ".governance/workspace.local.json",
            ),
        }
        return {"schema_version": 1, "entries": entries}

    def explain(
        self, query: str | None = None, *, task: str | None = None
    ) -> dict[str, Any]:
        resolved = self.resolve(task=task)
        if task:
            return resolved
        if query is None:
            raise ValueError("explain requires a key or --task")
        if query.startswith("authority:"):
            authority_id = query.split(":", 1)[1]
            _, project, _ = self.load()
            for value in project["authorities"]:
                if value["authority_id"] == authority_id:
                    source = self._source(self.project_path)
                    return {
                        "schema_version": 1,
                        "entries": {
                            query: {
                                "value": value,
                                "owner": "project",
                                "source": f"{source}#/authorities",
                            }
                        },
                    }
            raise GovernanceError(
                [
                    Diagnostic(
                        "BROKEN_REFERENCE",
                        query,
                        "project",
                        (self._source(self.project_path),),
                        "unknown authority ID",
                        "use a declared stable authority ID",
                    )
                ]
            )
        if query not in resolved["entries"]:
            raise GovernanceError(
                [
                    Diagnostic(
                        "BROKEN_REFERENCE",
                        query,
                        "resolved",
                        ("ephemeral resolution",),
                        "unknown resolved key",
                        "request a key emitted by gov resolve",
                    )
                ]
            )
        return {"schema_version": 1, "entries": {query: resolved["entries"][query]}}


__all__ = ["Diagnostic", "GovernanceError", "GovernanceResolver"]

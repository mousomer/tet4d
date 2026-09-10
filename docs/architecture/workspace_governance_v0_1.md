# Workspace governance v0.1

Status: implemented architecture contract for the first bounded extraction,
including the v0.1 integrity repair.

## Ownership model

The vendored pack at `tools/workspace_governance/` owns generic schema,
resolution, diagnostics, pack-integrity, and environment-inspection mechanisms.
It contains no Tet4D semantic values. `.governance/workspace.json` owns only
membership, relationships, workspace defaults, and the pack-lock reference.
`config/governance/project.json` owns Tet4D executable governance facts added by
this extraction and stable references to human authorities. Human RDS,
architecture, and governance documents remain semantic truth. Machine-specific
locations may appear only in the ignored `.governance/workspace.local.json`.
Copy `.governance/workspace.local.example.json` to that ignored path when a
machine needs an approved interpreter or route-tool override. Its checkout and
cache maps are explicitly reserved and must remain empty in v0.1.

`config/project/policy_pack.json` remains authoritative for facts not migrated
in v0.1. Routes are the one exception: `config/governance/project.json` is their
canonical owner and `policy_pack.json:codex_routing.routes` is a mechanically
parity-validated compatibility facade. No product authority transfer occurs.

## Resolution and contradiction behavior

`gov resolve` composes the pack, workspace index, project references, and only
the permitted local execution overlay into an ephemeral, provenance-bearing
view. `gov explain` returns one resolved value or stable authority identity.
Exclusive-scope collisions fail as `AMBIGUOUS_AUTHORITY`; no discovery-order or
generic layer precedence exists.

`gov check` loads the versioned JSON schemas as structural authority, then
extends them with stable-ID uniqueness, authority reachability, route-facade
parity, generated relationships, path sanitation, field-use classification,
and pinned-pack checks.

## Environment contract

The Python constraint and dependencies are owned by `pyproject.toml`. The one
semantic priority is `TET4D_PYTHON`, then the approved local-overlay interpreter,
then repository `.venv`, else `ENVIRONMENT_INVALID`. `PYTHON_BIN` is output
compatibility state only. `GOVERNANCE_PYTHON` selects only the CLI bootstrap and
cannot affect certification. `resolve_python_env.sh` delegates to `gov doctor`.

`gov doctor` verifies interpreter/version selection, import and editable-install
origin, dependency authority, and reports `ENVIRONMENT_INVALID` via
`ENVIRONMENT_MISMATCH` diagnostics. Godot inspection remains route-specific and
with existing Tet4D tooling; v0.1 does not duplicate its platform contract.

## Execution modes and verification

`LOCAL_FIX`, `FEATURE`, and `STRUCTURAL_CHANGE` bound discovery breadth. They do
not select or waive final evidence: the task, referenced authority, actual diff,
claims, and risk still determine verification. The representative scenarios in
the project manifest exercise this separation. Automatic general-purpose prompt
classification is intentionally out of scope.

## Pack updates and sanitation

`VERSION`, `MANIFEST.json`, and `config/governance/workspace.lock.json` identify
the vendored v0.1 bytes. Hashing consumes the manifest-declared algorithm and
exclusions; sync copies manifest version/revision into the lock.
`gov sync` is the explicit local acceptance operation;
ordinary checks report `PACK_DRIFT`. Generic path checks complement, rather than
replace, Tet4D's existing bounded secret scanner and sanitation entrypoint.

## Deferred

The compatibility policy pack, route semantics, product/platform matrix, exact
CI lanes, release rules, Godot/native parity, generalized orchestration,
automatic classification, and planner/runner redesign remain local to existing
Tet4D authorities and outside this extraction.

Workspace `relationships` and local `checkout_locations`/`cache_locations` are
reserved in v0.1. Workspace project membership/defaults and local interpreter/
tool paths are consumed. v0.1 selects the declared default project and its
repository/manifest path; it does not claim general task routing across several
projects. Schema annotations classify every declared field.

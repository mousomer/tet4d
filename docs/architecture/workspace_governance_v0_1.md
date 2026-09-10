# Workspace governance v0.1

Status: implemented architecture contract for the first bounded extraction.

## Ownership model

The vendored pack at `tools/workspace_governance/` owns generic schema,
resolution, diagnostics, pack-integrity, and environment-inspection mechanisms.
It contains no Tet4D semantic values. `.governance/workspace.json` owns only
membership, relationships, workspace defaults, and the pack-lock reference.
`config/governance/project.json` owns Tet4D executable governance facts added by
this extraction and stable references to human authorities. Human RDS,
architecture, and governance documents remain semantic truth. Machine-specific
locations may appear only in the ignored `.governance/workspace.local.json`.

`config/project/policy_pack.json` remains the compatibility authority for facts
not migrated in v0.1, including product/platform, release, exact lane, and
specialized validator policy. The project manifest labels this boundary; it
does not copy those values. No authority transfer is performed.

## Resolution and contradiction behavior

`gov resolve` composes the pack, workspace index, project references, and only
the permitted local execution overlay into an ephemeral, provenance-bearing
view. `gov explain` returns one resolved value or stable authority identity.
Exclusive-scope collisions fail as `AMBIGUOUS_AUTHORITY`; no discovery-order or
generic layer precedence exists.

`gov check` validates strict top-level ownership, required fields, stable ID
uniqueness, route references, generated-source relationships, tracked machine
paths, and the pinned pack hash. Diagnostics use stable classes and include the
fact, owner, sources, reason, and legitimate repair class. Human authorities are
never automatically overwritten.

## Environment contract

Project Python is 3.11 or newer, dependencies are owned by `pyproject.toml`, and
`.venv/bin/python` is the preferred development interpreter. `TET4D_PYTHON` is
the explicit approved override; `PYTHON_BIN` remains a temporary compatibility
input for existing callers. `scripts/resolve_python_env.sh` resolves once and
verification propagates the absolute interpreter to subprocesses. It does not
fall back to arbitrary system Python for project checks.

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
the vendored v0.1 bytes. `gov sync` is the explicit local acceptance operation;
ordinary checks report `PACK_DRIFT`. Generic path checks complement, rather than
replace, Tet4D's existing bounded secret scanner and sanitation entrypoint.

## Deferred

The compatibility policy pack, route semantics, product/platform matrix, exact
CI lanes, release rules, Godot/native parity, generalized orchestration,
automatic classification, and planner/runner redesign remain local to existing
Tet4D authorities and outside this extraction.

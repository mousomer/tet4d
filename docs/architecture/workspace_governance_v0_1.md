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
extends them with stable-ID uniqueness, authority reachability, route
reachability, route-facade parity, generated relationships, path sanitation,
field-use classification, and pinned-pack checks.

Reachability is enforced in both directions. An authority that no route
references, and a route that no execution profile or representative scenario
can select, are both `BROKEN_REFERENCE`: a declared fact nothing can reach is
unowned rather than merely unused, and its `consumed` classification cannot be
demonstrated.

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

## Round 2 integrity contracts

The shell launcher selects bootstrap plumbing from `GOVERNANCE_PYTHON`, an
executable local `.venv`, then discoverable `python3`/`python`. Bootstrap only
runs standard-library governance code; its early capability check reads the
lower bound from `[project].requires-python` before importing `tomllib`.
`bootstrap_env.sh` and `verify_local.sh` invoke the same early check before
creating or replacing an environment. It does not certify that interpreter for
project execution. `check`, `resolve`,
and `explain` need no third-party libraries. `doctor` resolves the approved
project interpreter even when bootstrap used system Python, returning
`ENVIRONMENT_INVALID` with `ENVIRONMENT_MISMATCH` when it is unavailable.
The selected project interpreter evaluates the full Python specifier using
`packaging`, explicitly declared in `pyproject.toml`. Missing packages and broken
metadata produce diagnostics, not forwarded subprocess tracebacks.

`resolve_python_env.sh` prints only the approved interpreter and rejects all
arguments. Execute a script with `"$(./scripts/resolve_python_env.sh)" script.py`.
`PYTHON_BIN` remains an output alias, never an independent selection input.

`canonical_owner_set` references the existing compatibility authority's
`authority_model.canonical_human_owners`. Graph validation requires exactly one
exclusive human file authority flagged `canonical_governance` for each owner,
with existing route reachability still required. Tet4D's existing surface
validator protects the six-domain owner set. ENGINEERING and VERIFICATION cover
Python engineering and verification; NATIVE_AND_PLATFORM and VERIFICATION cover
Godot, native, and parity. CONFIG_AND_GENERATED_DATA and SECURITY_AND_SANITATION
retain their respective owners; CHANGE_GOVERNANCE covers change discipline.
No separate Python, Godot, or parity governance documents are invented.

Authority sources explicitly distinguish files, directories, aliases, and JSON
pointers. An alias must reference a non-alias with the same source and cannot
claim exclusive or canonical ownership. Two exclusive identities cannot share
one source. Route `authority_refs` have set semantics; facade comparison sorts
both sides. Serialization order does not establish authority precedence.

Schema field-use annotations reference `field-usage.json` behavior families.
Each family identifies an implementation path and an executable mutation test.
Validation-only families use schema or sanitation validators; reserved arrays
and objects must be constrained empty. Tests execute the registry and the
contradiction catalog, including actual emissions for every advertised code.
The registry is a coverage index, not proof by declaration.

Generic generated surfaces in v0.1 support compatibility facades only. Drift
emits `CONFLICTING_VALUE`; `STALE_GENERATED_SURFACE` is not a public capability.
CONFIGURATION_REFERENCE and USER_SETTINGS_REFERENCE remain solely checked by
`generate_configuration_reference.py --check`. PROJECT_STRUCTURE and
CURRENT_STATE generated blocks remain solely checked by
`generate_maintenance_docs.py --check`. Broader generated-artifact migration is
deferred. The configuration reference covers `config/**`; workspace membership
at `.governance/workspace.json` is explicitly outside its scope and checked by
`gov check`.

`verification.canonical` is the unqualified repository gate (`verify.sh`), whose
normal mode uses the standard stability repeats. `verification.full` is the
existing agent invocation (`CODEX_MODE=1 ./scripts/verify.sh`), retaining all
verification families while reducing stability repeats. `targeted` is the
bounded focus gate, not a completion substitute. The `godot_toolchain` pointer
for the full repository invocation remains legacy compatibility debt; that
namespace does not describe the gate's ownership. No further policy family is
extracted here. Pack hashing ignores platform `.DS_Store` files through the
manifest exclusion mechanism, alongside bytecode caches.

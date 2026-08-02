# Topology Persistence and Recovery

Status: Stage 53D persistence authority

Semantic authority: Python strict topology domain objects

Canonical contract authority: `contracts/topology_contract_v1.json`

## Format ownership

Topology persistence has its own version. The existing top-level `version: 1`
marker remains the topology persistence version; it is not the canonical
topology contract version. The current writer emits only version 1.

| Source format | Version marker | Strictness | Adapter | Output |
| --- | --- | --- | --- | --- |
| Explorer topology persistence | exact integer `1` | exact current fields and scalar types | strict v1 loader | strict domain profile |
| Legacy explorer persistence | marker absent | source-specific migration | unversioned-v0 adapter | migrated strict profile |
| Editor draft state | separately owned scene state | editor-specific | editor draft adapter, not this loader | draft or domain result |
| Unknown persistence version | any other marker | unsupported | none | diagnostic no-gluing fallback for a trusted caller rank |

The v0 classification is based on the historical explorer reader accepting the
same profile collection without consulting a version marker. A document is not
classified as legacy merely because permissive parsing would make it pass.
Explicit `version: 0` and unknown future versions are unsupported because no
historical writer or fixture establishes them.

An absent explorer persistence file is normal first-run state: it produces the
trusted-rank no-gluing profile with no migration or fallback diagnostic. An
unreadable or malformed existing file is a profile fallback and is diagnostic.

## Current version 1

The document fields are exactly `version` and
`explorer_topology_profiles`. Profile fields are exactly `dimension` and
`gluings`. A seam requires `id`, `enabled`, `source`, `target`, and
`transform`; boundary and transform objects likewise reject unknown fields.
Profile slots are limited to `2d`, `3d`, and `4d`.

Integers must be JSON integers and must not be booleans. Booleans must be JSON
booleans. Strings must be strings before trimming and case normalization. Axis
values retain the historically supported exact integer index or string label;
the writer emits normalized labels. Transform arrays must have the exact
tangent rank and contain a complete integer permutation and signs `-1` or `1`.

## Loader architecture

Current v1 and legacy v0 use one structural parsing engine but select distinct
immutable format policies through explicitly named adapters.

`CURRENT_V1_POLICY` and `LEGACY_V0_POLICY` declare only genuine representation
differences: source/migration metadata, Boolean representation, missing
`enabled`, missing profile dimension, allowed fields, and the ordered set of
known obsolete fields. Named `_load_current_topology_profile_v1` and
`_load_legacy_topology_profile_v0` adapters select those policies before calling
the shared `_load_profile_document` parser. The policy behavior fields use
closed literal states; they are not permissive Boolean switches.

Exact decoded-JSON container and scalar checks come from
`topology_explorer.contract_validation`. Axis bounds, side normalization,
signed-permutation validity, gluing construction, canonical direction, and
geometry keys come from the strict Stage 53C domain model. Persistence adds
only format policy, stable diagnostic translation, and recovery behavior.
Policies cannot weaken those invariants or enable lossy coercion.

The shared parser requires an explicit policy and has no implicit legacy or
current default. File I/O, missing-file handling, JSON decoding, warning
emission, trusted-rank selection, and all-profile normalization remain in the
storage wrappers rather than the semantic parser.

## Legacy unversioned v0

The named v0 adapter shares strict structural primitives with v1 but owns all
leniency explicitly:

- Boolean strings whose trimmed, case-insensitive value is `true` or `false`
  migrate with `legacy_boolean_alias`.
- Missing profile `dimension` uses the trusted `2d`, `3d`, or `4d` storage slot,
  and missing seam `enabled` uses the historical `true` default. Both produce
  `missing_optional_field_defaulted`.
- The known non-semantic `metadata` and profile `name` fields are discarded
  with `unknown_field_ignored`.
- Integer axes remain supported. Other integer fields remain exact integers.

Numeric booleans are rejected. Although the old reader's generic truthiness
accepted them, the historical writer emitted real booleans and no fixture or
format authority proves numeric booleans were intentional persisted data.
Numeric strings and integer-valued floats are likewise rejected. No legacy
transform alternative is evidenced: omitted, padded, truncated, or malformed
transforms are never converted to identity.

| Input | Current v1 | Unversioned v0 |
| --- | ---: | ---: |
| `true`, `false` as Boolean | accept | accept |
| `"true"`, `"FALSE"` as Boolean | reject seam | migrate with diagnostic |
| `1`, `0` as Boolean | reject seam | reject seam; no historical writer evidence |
| `1.0`, `0.0` as Boolean | reject seam | reject seam |
| `"1"`, `"0"` as Boolean | reject seam | reject seam |
| `3` as integer | accept when in field range | accept when in field range |
| `"3"`, `3.0`, `3.9` as integer | reject seam/profile | reject seam/profile |

## Recovery granularity

Malformed seam-local data discards that seam and leaves its boundaries
unglued. The specific field diagnostic precedes
`malformed_seam_discarded`. Document container, version, profile collection,
trusted-slot dimension, or required profile-field failures use an empty
no-gluing profile of the already validated caller-supplied dimension and emit
`malformed_profile_fallback`. No rank is inferred from malformed data.

Exact and reversed semantic duplicate rows are deduplicated; input order does
not choose topology meaning. If active rows reuse a boundary, or enabled and
disabled rows describe the same seam, every conflicting row is discarded.
Reuse of one seam ID for different geometry likewise discards every row with
that conflict. Different IDs do not make semantically duplicate geometry
distinct.
Canonical seam ordering remains canonicalization's responsibility.

Current semantic objects reject unknown fields. Legacy v0 ignores only the
listed obsolete non-semantic fields. There is no generic extension bucket and
no arbitrary unknown-field acceptance.

## Structured evidence

`TopologyProfileLoadResult` is immutable and exposes the strict profile,
source version, migration, recovery and fallback flags, plus an ordered tuple
of `PersistenceDiagnostic`. Diagnostics expose severity, stable code, precise
JSON path, explanatory message, optional original value, and recovery action.

Diagnostics are deterministic: document/version findings first, then
profile-level findings in policy order, seam findings in source-array order,
then duplicate/conflict findings in source-array order. Callers and tests use
codes and paths rather than parsing prose.

Owned codes are:

`missing_version`, `unsupported_version`, `wrong_type`,
`missing_required_field`, `unknown_field`, `unknown_field_ignored`,
`legacy_boolean_alias`,
`missing_optional_field_defaulted`, `malformed_json`, `malformed_seam`,
`malformed_seam_discarded`, `duplicate_seam_deduplicated`,
`conflicting_seam_discarded`, `malformed_profile_fallback`,
`invalid_dimension`, `invalid_axis`, `invalid_side`, `invalid_permutation`,
`invalid_sign`, and `invalid_enabled`.

## Identity and adapter boundaries

Only the resulting strict profile may enter canonicalization. Raw persistence,
discarded seams, diagnostics, migration metadata, and fallback metadata have no
topology identity. The v1 writer serializes only strict profiles and never
preserves a legacy alias or malformed raw value. Canonical contract v1, its
fingerprint, Stage 53B transport DTOs, resolver behavior, gameplay/replay
hashes, and Python semantic authority are unchanged.

Interactive editor text parsing is not persistence parsing. It remains owned
by an editor adapter that must validate draft text before constructing strict
domain objects.

## Downstream governance

Stage 53E must inventory remaining coercion boundaries across canonical and
state-hash inputs, public constructors, persistence, transports, editor/CLI
input, numerical internals, migration tools, and active or retirement-candidate
Python paths. Stage 53F owns targeted corrections and drift prevention from
that inventory. Stage 53D does not close repository-wide governance.

Stage 53D encountered, but deliberately did not change, these Stage 53E inputs:

- `runtime/topology_profile_store.py` and
  `gameplay/topology_designer.py` own the separate normal/explorer workspace
  profile format and its fallback behavior;
- topology-lab scene/draft adapters normalize interactive coordinates,
  transforms, settings, and widget text before domain construction;
- topology preview and experiment exporters convert internal and report
  payload values and need classification as trusted internals versus imported
  data;
- topology-lab CLI dimension parsing is a human-input adapter;
- general settings readers have independent legacy Boolean/index policies and
  must not inherit topology persistence rules;
- replay, trace, canonical identity, and state-hash inputs still require the
  repository-wide boundary inventory promised by Stage 53E.

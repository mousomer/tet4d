# Explorer topology T2 transfer preparation

Role: bounded nonterminal transfer candidate; T1 design evidence
Status: preparatory prose only; no active transfer row or runtime authority change
Owners: `docs/architecture/authority_transfer_protocol.md`,
`docs/architecture/authority_map.md`, `docs/rds/RDS_EXPLORER_TOPOLOGIES.md`

## 1. Candidate boundary

T2A's bounded/cylinder/torus native candidate implementation and executable preservation
harness are described in [native T2A transport](explorer_topology_t2a_native_transport.md).
This is a partial provider slice; the complete T2 transfer conditions below
remain required. No Godot integration or runtime authority promotion is implied.

Subsystem: **single-domain 2D Explorer deterministic topology transport and queries**.
Current authority is inherited Python topology/canonical contracts, with the
approved Explorer RDS governing intentional forward requirement changes.
Candidate deterministic owner is the existing native C++ query/transport family.
Data authority is canonical topology v1 plus the separate T1 piece/catalog and
fixture contracts. Godot retains presentation/control/camera authority.

Normative design:

- `docs/architecture/explorer_topology_piece_transport_contract.md`
- `docs/architecture/explorer_topology_catalog_certification_contract.md`
- `docs/architecture/canonical_topology_contract.md`
- `docs/architecture/native_topology_transport.md` for the checked boundary

Included observable scope: strict profile interpretation and normalization;
boundary-pair/seam preview, directed cell-neighbor/frame and topology adjacency
queries; persistent cell identity/orientation; one selected translation or
supported rotation; proposal/classification/atomic application; recorded inverse,
revision invalidation, Retry and strict serialization of the new Explorer state.
The provider must preserve count, correspondence, unique occupancy, frames,
exact inverse and complete-envelope no-op on any rejection.

Reuse `native/tet4d_core/include/tet4d_core/query.hpp` and its `src/core/query.cpp`
implementation: `resolve_topology_cell_step_query`, `topology_neighbor_query`,
seam inversion/frame helpers and `piece_pose_legal_query`. Extend the existing
`topology_transport.cpp` decoder and `topology_transport_variant.cpp` adapter,
with checked `tet4d_core_api.cpp` entry/result conversion. Reuse geometry/pivot
helpers with stable IDs and the Explorer-specific lowest-ID centroid tie-break
(piece contract §9), preserving ordinary native pivot behavior. Carry the
four-turn/fresh-opposite identities, quotient-aware classification (§7), and
2×3 torus rotation-collision witness into native conformance. Do not implement a second resolver or certify a
mathematical class inside transport. `practice_explorer.gd` and the current
bridge/control-frame mapping remain consumers, not validity owners.

## 2. Comparison dispositions

| Existing evidence/behavior | T2 disposition and comparison |
| --- | --- |
| Python `resolve_cell_step` paired boundary maps | Preserved unchanged; exact canonical target, coordinate-map and piece-frame parity |
| Python `resolve_piece_step` classification | Historical comparison only where persistent frames/new invariants change the result; conforming cases retain comparison |
| Duplicate-target successful deformation | Intentionally superseded for forward Explorer: E6 is `blocked/destination_collision`; retain old golden assertion separately |
| Legacy rigid-mode veto | Superseded only for new Explorer's valid injective deformation; not a catalog-wide transport veto |
| Ordinary Play gravity/drop/lock/score/queue | Outside transfer; unchanged Python/native compatibility tests |
| Python Playground sandbox policy/UI | Historical independent behavior; no new shell or runtime fallback |
| Native single-cell parity | Preserved; necessary provider evidence, insufficient whole-piece conformance |
| Native one-crossing frames | Preserved low-level semantics; add accumulated-frame/inverse conformance from Session 2 |
| Canonical v1 identity | Preserved byte/digest/normalization fixtures; catalog prefix cannot change suffix |
| Godot bounded 3D/4D Explorer | Outside new transport scope; retain movement/rotation/view/Retry/isolation regressions |
| New state IDs, inverses, revision/trace transaction and defined rotation scope | Missing native conformance; compare to reviewed T1 fixture specifications, not a new Python oracle |

The fixture package keeps `native_result`/`godot_result=not_run`. T2 must
produce a separate result artifact bound to fixture-content digest, runtime
commit, command/toolchain and comparison mode. Never overwrite the expected
fixture with measured output or reinterpret historical replay/goldens.

## 3. Fixture owners and command plan

Data owners under `tests/fixtures/explorer_topology/`:

- `catalog_v1.json`: seven nonselectable representative entries and exact identity vectors.
- `quotients_v1.json`: square incidence/link/orientation proof evidence and comparison constructions.
- `transport_v1.json`: E1–E10, cylinder/interior/self-neighbor companions, failure mutations,
  ordered inverse sequences and finite five-core boundary enumeration.

Current executable **design/reference** checks (exist now):

```sh
PYTHONPATH=src python -m tools.migration.explorer_topology_contracts
./scripts/verify_focus.sh --docs tools/migration/explorer_topology_contracts.py tools/migration/square_quotient_evidence.py tests/unit/migration/test_explorer_topology_contracts.py --pytest tests/unit/migration/test_explorer_topology_contracts.py tests/unit/engine/test_canonical_topology_contract.py tests/unit/engine/test_explorer_transport_resolver.py
./scripts/test_godot_tet4d_core.sh
./scripts/verify_focus.sh --pytest tests/unit/migration/test_cpp_query_parity.py tests/unit/migration/test_cpp_geometry_parity.py tests/unit/migration/test_topology_transport_parity.py
CODEX_MODE=1 ./scripts/verify.sh
```

Use the `gov env`-selected interpreter; `python` above denotes that interpreter,
not an unverified PATH choice. The explicit `PYTHONPATH=src` command is for
the verified source-checkout mode; otherwise use the binding emitted by `gov env`. Build native test binaries before migration parity;
skips due to absent binaries are not evidence. The full gate discovers the new
specification tests through pytest; no governance family or waiver is added.

**Complete T2 implementation and commands (partially implemented by T2A):** extend
`native/tet4d_core/tests/query_core_tests.cpp` and `topology_transport_tests.cpp`
to consume the reviewed fixture format. Add an explicit `--explorer-piece-conformance`
mode to their existing test/export family and route it through
`scripts/test_godot_tet4d_core.sh`; T2A implements this mode in the separate
`explorer_piece_tests.cpp` suite for bounded/cylinder/torus translations. The remaining
T2 surfaces still require implementation. Its output compares full expanded semantic states, per-ID witnesses,
frames, reasons, descriptor recovery, revisions and retained-state assertions.
Use `preserved_unchanged`, `historical_comparison_only`,
`superseded_forward_explorer`, `missing_new_conformance`, `outside_t2_scope`
exactly as the package's comparison dispositions; do not use blind Python parity
for E6 or newly established behavior.

Extend the existing Godot `tests/test_topology_transport_boundary.gd` and
`tests/test_practice_explorer.gd`, with `tests/run_practice_explorer.gd` for focused
integration. Existing build/full-shell commands are
`./scripts/build_godot_tet4d_core.sh` and `./scripts/verify_godot_4_7.sh`.
These run future cases only after those cases are implemented and registered.
Godot must test strict Variant failures, stale/tampered candidates, new 2D routing,
Retry identity and live Play/hash/queue/RNG isolation, while camera/slice changes
leave identical native requests/results. Human review separately checks novice
preset discovery and comprehension of separated cells and seam reversals.

## 4. Evidence and terminal conditions

T2 cannot reach terminal transfer merely by compiling or loading the five labels.
Require all of the following, with exact executed commands and source identities:

1. Independent review/reconciliation and explicit T1 acceptance; schemas,
   profile IDs, mathematical proof references and fixture digests are stable.
2. Native implementation of this bounded contract, strict normalized profile
   identity parity, all five-core finite-direction/extent/frame cases, whole-piece
   positive/negative/rotation/inverse/lifecycle conformance and mutation regressions.
3. Unchanged Python/native parity and historical golden readability; explicit
   new-RDS comparisons for intentional differences. No unexplained mismatch/skip.
4. Checked Godot adapter and Explorer integration/isolation tests, five working
   presets and product review. Runtime conformance cannot substitute for proof review.
5. Independently accepted mathematical construction evidence for the five core
   catalog claims. Optional projective/sphere-like claims remain gated independently.
6. Complete substantive transfer record under the existing protocol: current and
   candidate owner, exact scope, fixture owners/digests, comparisons, exclusions,
   safe failure/rollback, map update and validation. Only then status `transferred`.
7. In the same accepted transition, narrowly exclude **this single-domain 2D
   Explorer scope** from the inherited topology row and record its native owner
   with terminal record reference. Preserve Play, Python legacy, 3D/4D and Godot
   presentation rows. No such active record/map change is made by T1.

## 5. Exclusions and fallback

Excluded: ordinary 2D Play; gravity, drop, lock, score, queue/RNG; general gameplay
legality; Python Playground UI/policy; 3D/4D topology (T4); camera, projection,
slices and presentation; builder editing (T3+); multi-domain/genuine sphere
runtime (T6); historical replay/trace reinterpretation; universal manifold
classification. Mathematical evidence checking does not own movement.

Before promotion, preserve the bounded Explorer and keep the unaccepted native
2D feature unavailable. Missing/malformed/failing provider results cause an
atomic failure/unavailable state, never silent fallback to historical Python
piece classification. An experimental entry must satisfy exactly the same
injectivity, inverse and atomicity requirements as an implemented entry.

After promotion, rollback is one reviewed product/authority operation: disable
new 2D topology selection, restore the bounded-only product, revert the scoped
terminal record and authority-map exclusion consistently, and preserve the
versioned catalog/state readers or report unsupported versions without mutation.
Do not rewrite old save meaning, pretend deformed framed states are old bounded
poses, or restore conflicting Python fallback. Keep failed result artifacts and
fixture versions as evidence. New availability/certification status changes
must point to the reviewed rollback decision; unrelated authority stays intact.

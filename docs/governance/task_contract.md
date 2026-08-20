# Task Contract — Pre-54F NEXT Geometry Fidelity

## Objective

Make every production Live 3D and Live 4D NEXT thumbnail a faithful
presentation of the authoritative queued piece. Correct the earliest faulty
presentation transform, add exhaustive production-registry coverage, and keep
queue, RNG, gameplay, and native piece definitions unchanged.

## Classification

- Primary task type: `godot_product_shell`.
- Workflow modifier: `cross_layer` because the exhaustive Godot oracle consumes
  a read-only native production-catalogue diagnostic.
- Affected layers: native diagnostic boundary, Godot thumbnail model/renderer,
  tests, documentation, and visible product.
- Required evidence: `documentation`, `godot`, `native`,
  `parity_or_conformance`, `integration`, and `human_visual`.
- Full repository gate: required because the change extends the NEXT authority,
  touches the shared GDExtension boundary, and makes an exhaustive production
  claim.

## Current Authority and Finding

- The inherited deterministic queue owner selects the next piece.
- Native production catalogues own the queued piece identity, dimensional
  embedding, colour ID, and canonical occupied cells.
- `docs/architecture/next_piece_preview.md` owns the one-piece query and shared
  thumbnail presentation contract.
- Godot owns only validation, whole-piece presentation normalization, W-slice
  decomposition, drawing, HUD placement, and readability.
- The current native payload and `PieceThumbnailModel` preserve exact cells.
  The renderer then derives bounds, scale, and origin independently for every
  4D W group, destroying their shared XYZ placement. This is a cross-group
  presentation-normalization defect, not an authoritative geometry defect.

Authority effect: reuse the existing boundary. No gameplay authority transfer
or establishment occurs.

## Allowed Systems and Paths

- native production-catalogue registry declarations, exact read-only
  GDExtension transport, and native completeness tests;
- Godot NEXT bridge, shared thumbnail renderer/planning seam, and focused
  model/renderer/queue integration tests; and
- the existing NEXT architecture authority, task contract, professional
  programme, backlog, and current-state handoff records.

## Scope Matrix

| Layer | Allowed change | Required evidence |
| --- | --- | --- |
| Native/GDExtension | Read-only enumeration of supported production piece sets and their canonical definitions | Native build/tests and exact adapter transport |
| Godot model/renderer | Exact reconstruction, shared whole-piece projection fit, W grouping, renderer plan | Exhaustive structural and renderer tests |
| Integration | Production registry and queued preview feed the same thumbnail builder | Queue identity/update and catalogue-to-model coverage |
| Documentation | Extend the existing NEXT authority and update active programme/handoff state | Governance/documentation checks |
| Visible product | Focused 3D/4D NEXT inspection, explicitly including FORK4 | Real-window evidence |

## Required Changes

1. Document the only permitted geometry transform: no rotation, reflection,
   axis permutation, or per-group normalization; exact canonical cells are
   retained, and drawing may apply one shared uniform scale plus translation.
2. Preserve one shared XYZ projection scale and origin across every W pane;
   only the pane anchor and explicit W label may differ.
3. Expose a read-only diagnostic derived from native production registries so
   tests never duplicate the piece library or infer geometry from names.
4. Enumerate every production 3D/4D piece set from the live registries and pass
   every canonical definition through the actual thumbnail model and renderer
   plan.
5. Compare exact cells, counts, uniqueness, extents, embeddings, W membership,
   and face-adjacency edges. Prove renderer cell/group completeness.
6. Add named FORK4 and independent-W-recentering regressions plus queued-piece
   identity/update coverage.

## Forbidden Changes

- #74 relative-control semantics or Stage 54E-4 lifecycle behavior;
- production piece definitions, gameplay embedding rules, movement, rotation,
  collision, gravity, drop, lock, scoring, RNG, bag, queue, snapshots, hashes,
  replay, trace, setup, or persistence;
- Hold, Stage 54E-5 cockpit consolidation, #69 board spacing, #70 grid
  hierarchy, general 54F polish, topology, Explorer, campaign, or simulation;
- a second hand-authored preview catalogue, name-based reconstruction, Python
  mirror, or FORK4-specific production rendering path; and
- push or pull-request creation.

## Acceptance Criteria

1. Every production Live 3D and Live 4D piece/piece-set variant is enumerated
   from registries and accepted by the actual thumbnail model.
2. Model geometry equals canonical geometry exactly; cell count, uniqueness,
   extents, embedding, W membership, and face adjacency are unchanged.
3. All W panes use one whole-piece XYZ projection frame, preserving cross-W
   offsets and the visual alignment that encodes cross-W face adjacency.
4. Renderer plans contain exactly one cell instance per model cell and one
   pane per occupied W coordinate.
5. FORK4 retains its three-cell X bar in W=0 and its offset Y/Z branch in W=1
   without independently re-centering either pane.
6. NEXT identity equals the authoritative queue head, updates after spawn, and
   does not change RNG or queue semantics.
7. Focused native/Godot checks, pinned Godot verification, sanitation,
   governance/documentation checks, and the full repository gate pass.
8. Real-window inspection is reported truthfully and is not inferred from
   headless structural evidence.

## Automated Verification

- focused native catalogue/GDExtension tests;
- focused Godot NEXT model, renderer, registry, and queue integration tests;
- `git diff --check`;
- `./scripts/check_git_sanitation_repo.sh`;
- routed governance/documentation checks;
- `GODOT_BIN=/Applications/Godot.app/Contents/MacOS/Godot
  ./scripts/verify_godot_4_7.sh`;
- `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

- In a real Godot window, inspect representative elongated, planar,
  volumetric, branched, embedded, single-W, multi-W, and cross-W pieces.
- Explicitly compare FORK4 NEXT with its subsequent active spawn.
- Automated completion alone advances only to
  `IMPLEMENTED / AUTOMATED GREEN / HUMAN VISIBLE REVIEW PENDING`.

## Documentation Updates

- extend `docs/architecture/next_piece_preview.md` with the exact transform and
  shared-W-frame invariant;
- record the root cause and exhaustive coverage in the professional programme;
- update `docs/BACKLOG.md` and `CURRENT_STATE.md` proportionally; and
- leave the authority map unchanged unless ownership actually changes.

## Explicit Deferrals

- all forbidden adjacent programme work listed above;
- optional piece sets that are not admitted by current production registries;
- general thumbnail redesign beyond geometry readability; and
- integrated Stage 54F acceptance.

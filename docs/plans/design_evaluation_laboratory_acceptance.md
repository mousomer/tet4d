# Design Evaluation Laboratory Acceptance

Status: AUTOMATED LOCAL ACCEPTANCE GREEN / HUMAN DESIGN AND CLEAN-WINDOWS ACCEPTANCE PENDING

Date: 2026-08-29

Authority: maintenance acceptance record for Stage 54F-5. The durable behavior
and promotion boundary are owned by
`docs/architecture/design_evaluation_laboratory.md`.

## Automated acceptance scope

Automation must be green before a person records design judgments. The accepted
matrix covers:

- the six immutable built-in styles and detached mutable user candidates;
- all ten shipped scenarios, including 2D/3D/4D, sparse/dense,
  NEXT/HOLD/Ghost, and sphere-like topology presentation;
- repeat load after camera/basis disturbance and the full preset-by-scenario
  apply/render/reset matrix;
- exact A/B snapshots, `A -> B -> A`, repeated switching, deterministic blind
  labels, and fail-closed non-style drift detection;
- replacement-safe profile and evaluation persistence, immutable historical
  preset snapshots/hashes, PNG/metadata capture, nomination, all three export
  outputs, and repository-side owner/value validation; and
- an x86_64 Windows portable ZIP containing the current Godot executable, PCK,
  release GDExtension, icon, catalog, scenarios, and replay resources without a
  Python/editor/checkout dependency.

Local macOS evidence proves the actual Windows PE artifact structure and resource
closure, not Windows execution. The Windows workflow is configured to run the
focused laboratory suite, build/validate the package, and launch the packaged
runtime. It has not run until the commits reach a Windows runner.

## Windows artifact acceptance boundary

The distributable is `Tet4D-Designer-0.7.5-windows-x86_64.zip`. Extracting it is
the install-equivalent operation. Run `Tet4D Designer/Tet4DDesigner.exe`; delete
the extracted directory to uninstall. The portable distribution intentionally
does not register a Start Menu entry, desktop shortcut, or Windows uninstall
record. Mutable profiles, evaluations, captures, and exports live under Godot's
per-user application-data root, never beside the executable.

Direct clean-machine Windows execution is the only platform item not executable
on the macOS implementation host. Do not describe that step as passed until a
Windows reviewer executes the checklist below.

## Human evaluation checklist

Start only from a green automated build.

### Launch and catalogue

- [ ] Extract the ZIP outside a repository checkout and launch
  `Tet4DDesigner.exe` without Python or a Godot editor installed.
- [ ] From the main menu choose **Design Laboratory**.
- [ ] Confirm all built-in presets show understandable names, descriptions,
  stable IDs, provenance/category, candidate status, and read-only identity.
- [ ] Apply and inspect each built-in; confirm the intended styles are visually
  distinct.
- [ ] Duplicate a built-in as a user candidate, edit it in the existing
  Presentation Designer, save it, close/relaunch, and confirm it reloads.

### Representative 2D / 3D / 4D review

- [ ] Review sparse and dense 2D scenarios for board scale, silhouette,
  readability, active/Ghost separation, and NEXT/HOLD balance.
- [ ] Review sparse and dense 3D scenarios for depth, occlusion, spatial
  comprehension, piece visibility, and hierarchy.
- [ ] Review sparse, dense, and sphere-like 4D scenarios for slice hierarchy,
  local depth, labels, and topology-oriented comprehension.
- [ ] Confirm piece controls stay prominent, camera/presentation controls remain
  secondary, and the 4D board retains enough viewport space.

### A/B and blind mode

- [ ] Select a scenario and two presets, then start comparison.
- [ ] Exercise **A**, **B**, **Toggle**, and **Reset scenario** repeatedly.
- [ ] Confirm switching is immediate, the gameplay state never jumps, and reset
  returns to the same board/piece/queue/HOLD/Ghost/camera/basis state.
- [ ] Enable blind mode and confirm judgment labels hide preset names while
  retaining enough orientation to choose an arm.

### Evaluation and screenshots

- [ ] Record Prefer A, Prefer B, and No preference in separate trials.
- [ ] Enter all eight optional 1–5 ratings plus free-text notes; save and reload.
- [ ] Capture A, B, and a pair; confirm `A.png`, `B.png`, and `metadata.json`
  contain the expected scenario/build/arm provenance and no names overlaid on
  blind images.

### Nomination and repository portability

- [ ] Nominate a user candidate and note the displayed absolute export path.
- [ ] Confirm `preset.json` matches the visible candidate's exact values,
  `comparison_summary.json` contains only real matching evaluations, and
  `DESIGN_PROPOSAL.md` is understandable review input.
- [ ] Copy the bundle to a source checkout and run
  `python3 tools/design_lab/validate_design_export.py <bundle-directory>`.
- [ ] Confirm validation does not alter the built-in catalog, production
  defaults, or authority documents.

### Clean exit / relaunch / removal

- [ ] Close and relaunch; confirm the user candidate and evaluations persist.
- [ ] Delete the extracted application directory and confirm no installed
  application files remain. Retain or remove per-user evidence separately as
  the reviewer intends.

## Repository promotion checklist

A successful human evaluation does not promote a design. Promotion requires a
separate reviewed repository change that:

1. validates the bundle schema;
2. resolves every property through the canonical registry and confirms exactly
   one semantic owner;
3. compares the candidate with the relevant baseline;
4. updates the appropriate authoritative design documentation;
5. updates the shipped catalog only if formally accepted;
6. updates regression fixtures/tests;
7. runs the full repository verification; and
8. keeps authority, runtime configuration, and shipped catalog consistent.

Stage 54F-6 owns default selection and any bounded polish. This acceptance
record does not predetermine that decision.

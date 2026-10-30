# Cockpit and Designer focused verification — 2026-10-30

Base: `aa63d22a`, including master integration `91987bb1`. This evidence covers
the subsequent F3 repair and focused regression execution; it does not promote
a new visual baseline. The owner authorized relevant tests after the prior
secrets-only restriction. The selected route is `godot_product_shell`; discovery
is bounded to the Designer owner, persistence consumer and camera/cockpit seams.
No manifest, native gameplay, packaging or platform-support change was made.

## Method and results

- `./gov check`: passed.
- `./gov explain --task "Fix Designer group reset baseline and verify camera cockpit integration"`:
  Godot product-shell route; default FEATURE exploration, narrowed to this
  already-localized defect and adjacent contracts.
- `./gov doctor`: passed, approved Python 3.14.8 source environment.
- Godot matched manifest build `4.7.2.stable.official.ed1daf0bf`.
- Tests ran in a temporary project copy with isolated HOME/XDG user data.
  Editor import: `Godot --headless --path <isolated-project> --editor --quit`.
  Test invocation: `Godot --headless --path <isolated-project> --script focused_review.gd`.
  The temporary runner loaded the four registered scripts below, awaited each
  public `run()`, aggregated failures, required all four executions, and returned
  a nonzero exit on failure. Logs were inspected for script/parse errors as the
  canonical wrapper requires. The repository's aggregate runner was unchanged.
- Before repair: new test cases with the committed old Designer implementation
  produced exactly three failures: group Reset after Save As, Save and Load.
- After repair: 4/4 suites executed, zero failures, no script/parse errors:
  `test_camera_rig.gd`, `test_live_cockpit.gd`,
  `test_presentation_designer.gd`, `test_presentation_profile_library.gd`.
- An initial repair import exposed a tooltip-line indentation error; corrected
  before the final fresh isolated run reported above.
- `CODEX_MODE=1 python tools/governance/validate_handoff_lifecycle.py`: passed.
- `CODEX_MODE=1 python tools/governance/validate_project_contracts.py`: passed,
  126 required paths checked. Python is the interpreter selected by `gov doctor`.

Scoped secrets/string sanitation over all 11 changed/new files and
`git diff --check` passed.

## Identity and limits

- `godot/Tet4D.Godot/scripts/ui/presentation_designer.gd`: `3fa134e5c2421dc539418780faef8d6f600807ed5e75afc2b4a5a9d4529a0b29`
- `godot/Tet4D.Godot/tests/test_presentation_profile_library.gd`: `9071adcc6c03f5e795bab07c4e89e151e163443c23ce06e446779a6b9b2d4353`

The existing macOS debug extension was reused from the main checkout; native
source is unchanged between that checkout and this branch. No fresh native
build or native-acceptance claim is made. The focused suites include their
existing production-scene integration checks, not just isolated helper calls.
R1/R2 now have focused automated coverage; full integration and human visual
acceptance remain separate. The complete registered Godot suite, repository
full gate, remote CI, packaging/device matrix and manual 3D/4D review were not
run. No screenshot or geometry baseline was regenerated.

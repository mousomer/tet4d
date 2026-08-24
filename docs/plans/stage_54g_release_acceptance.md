# Stage 54G Release-Candidate Evidence

Status: IMPLEMENTED / BLOCKER FIXED / HUMAN RE-ACCEPTANCE PENDING

Candidate date: 2026-08-24

Candidate branch: `codex/54g-release-hardening`
Starting commit: `162bfad57053a250051bb4b2bbb7dfaae108d10f`

## Decision boundary

This record prepares, but does not replace, the independent human acceptance
required by the Professional Core Game Gate. Agent-driven real-window evidence
is release diagnosis only. Until the human matrix below passes:

```text
Stage 54G: IMPLEMENTED / BLOCKER FIXED / HUMAN RE-ACCEPTANCE PENDING
PROFESSIONAL_CORE_GAME_READY: NO
```

No deterministic authority is established or transferred by this stage.

## Routing and prerequisite audit

- Primary task type: `packaging_and_release`.
- Modifier: `cross_layer`.
- Affected layers: documentation, governance, Godot, native,
  deterministic-state evidence, parity/conformance, integration boundary,
  visible product, packaging, platform, and release acceptance.
- Required evidence: documentation, governance structure, Godot, native,
  deterministic, parity/conformance, integration, human visual, packaging,
  platform, and release acceptance.
- Full repository gate: required.

The programme gate was re-read without modification. Stage 54E-3, Stage
54E-4, issue #74, NEXT geometry, Stage 54E-5, and Stage 54F remain accepted.
Stage 54D-3 remains COMPLETE / DETERMINISTIC AUTHORITY ESTABLISHED / HUMAN
VISIBLE ACCEPTED, and `AE-0055` remains established. Hold therefore satisfies
the formerly missing deterministic contract and readable NEXT/HOLD product
prerequisites. No formal pre-54G blocker remains.

## Release inventory

| Item | Candidate truth |
| --- | --- |
| Product | Tet4D |
| Version authority | `pyproject.toml`, version `0.7.5` |
| Product shell | Godot |
| Engine | `4.7.1.stable.official.a13da4feb` |
| Entry scene | `res://scenes/trace_replay.tscn` |
| Default viewport | 1600 x 960 |
| Supported minimum shell size | 634 x 660 |
| Supported modes | bounded 2D, 3D, and 4D live play plus replay demos |
| User data | platform application-data directory `Tet4D`; schema-3 shell settings and schema-4 game setup |
| Current release target | macOS 13+, Universal 2 app and ZIP |
| Current export preset | `macOS Universal` |
| Current native artifact | `libtet4d_core.macos.template_release.framework`, `x86_64` + `arm64` |
| Development-configured targets | Linux and Windows GDExtension names only |
| Retained legacy target | Python/PyInstaller `.dmg`, `.deb`, and `.msi` path |

The old Python packaging path is not current Godot product evidence. Linux and
Windows have no current Godot export preset or runtime acceptance and must not
be presented as supported release targets.

## Build, export, and artifact evidence

The exact pinned Godot editor and the matching official 4.7.1 macOS export
template produced:

- `artifacts/godot/macos/Tet4D.app`;
- `artifacts/godot/macos/Tet4D-0.7.5-macos-universal.zip`;
- app size approximately 165 MiB and ZIP size approximately 59 MiB; and
- candidate ZIP SHA-256
  `3f3bc759091abd52c398114aae2f22d3ee3db59f90415270c4610cdcb60b2859`.

Artifact inspection proved:

- the app executable and packaged GDExtension both contain `x86_64` and
  `arm64` slices;
- the GDExtension deployment target is macOS 13.0 for both slices;
- bundle identifier `io.github.mousomer.tet4d` and version `0.7.5` agree with
  repository authority;
- the framework metadata also declares version `0.7.5` and macOS 13.0;
- the ad-hoc signature passes `codesign --verify --deep --strict`;
- `Tet4D.pck`, replay bundle, settings registry, themes, scenes, compiled
  scripts, and native framework are present;
- the Godot test tree, saved user settings/setup, editor-local state, temporary
  evidence, and machine-local source paths are absent; and
- the build completed without an export warning or error.

The package is ad-hoc signed and not notarized. It is a local release candidate,
not a public Gatekeeper-ready distribution. Developer-ID signing,
notarization, stores, and unsupported-platform installers remain separate
distribution work.

## Startup and persistence matrix

| Check | Result | Evidence boundary |
| --- | --- | --- |
| Two clean users | PASS | The release smoke script copied the app outside the checkout and launched it twice with separate HOME/XDG roots and a non-repository working directory. |
| Additional clean starts | PASS | Two independently prepared clean roots launched the copied app with exit status 0 and engine-only logs. |
| Persisted preferences | PASS | A realistic schema-3 UI scale, High Contrast, Reduced Motion, HUD, display, window, and camera fixture plus schema-4 2D/3D/4D setup fixture survived two launches unchanged. |
| Partially invalid values | PASS | Invalid UI scale and unknown transient/gameplay-shaped keys fell back or were ignored while unrelated valid preferences and setup remained readable; two launches completed without warnings. |
| Malformed and range recovery | PASS by focused Godot evidence | Existing store suites cover malformed roots/JSON, unsupported schemas, partial invalid values, safe defaults, unrelated-value survival, and failure-safe replacement. |
| Actual preference save | PASS | Real-window High Contrast selection wrote the canonical schema-3 file; the file contains only registered persistent preferences. |
| Transient view exclusion | PASS | Saved shell/setup payloads contain no basis, yaw/pitch/roll, pan, zoom, Fit reference, projection identity, or named View Action identity. |
| Gameplay/Hold exclusion | PASS | Saved payloads contain no active piece, queue, board, Ghost, Hold slot, or Hold availability. New-session Hold canonicalization remains covered by accepted native/Godot regression evidence. |
| Relaunch | PASS | The actual saved user root relaunched from the outside-tree app with exit status 0 and no warning/error. |

This is a fresh-machine approximation using isolated user data, an exported
app outside the repository, and no current-working-directory dependency. It is
not evidence from a different physical machine.

## Agent-driven packaged-app regression

The actual outside-tree exported app was launched with the real macOS display
server at 1180 x 760. The ordinary runtime log contained no parser, resource,
GDExtension, persistence, theme, invalid-node, or recurring warning/error
output.

| Surface | Agent verdict |
| --- | --- |
| Fresh menu and setup | PASS; product menu and default 2D/3D/4D setup were reachable and usable. |
| 2D | PASS diagnostic sample; live board, active piece, Ghost, NEXT, empty/populated Hold, and menu recovery rendered from the package. |
| 3D | PASS diagnostic sample; volume, active piece, Ghost, NEXT, Hold command, view actions, and menu recovery were present. |
| 4D Standard | PASS diagnostic sample; four W-labelled volume slices, active/Ghost state, two-cell NEXT, multi-W Hold, and view actions remained comprehensible at the small window. |
| 4D High Contrast | PASS diagnostic sample; board and cockpit hierarchy strengthened as designed, including NEXT/HOLD. |
| Settings | PASS diagnostic sample; the scroll surface remained reachable at 1180 x 760, keyboard focus revealed lower controls, and High Contrast saved immediately. |
| Help/keybindings | PASS diagnostic sample; packaged help exposed the mode-specific controls and `C` Hold binding. |
| Replay | PASS for packaged browser/resource reachability; the included 2D/3D/4D corpus populated. Playback/navigation correctness remains covered by automated tests and the pending human matrix. |
| Quit/relaunch | PASS; Command-Q exited cleanly with status 0 and the saved root relaunched successfully. |
| Performance | PASS sanity only; headless starts completed in roughly 1.2-3.4 seconds and real-window 2D/3D/4D, Hold, Settings scrolling, and resizing/focus changes showed no obvious severe regression. |

This evidence does not claim exhaustive human play acceptance. Accepted
gameplay, controls, camera, Reset/Fit/Restart, modal ownership, setup recovery,
and replay contracts are also exercised by the pinned Godot and native suites.

## Independent-acceptance blocker correction

The first independent matrix passed the release candidate except for one
reproduced blocker. A retained Live-4D session returned from Main Menu through
Advanced / Diagnostics, Replay Demos, and Viewer with its HUD, NEXT, HOLD, and
running native session intact but no visible board. Fit could not recover it;
Reset could.

Executable Godot 4.7.1 diagnosis established that Main Menu correctly destroys
the presentation context. The HUD Viewer button then bypassed the app lifecycle
owner and exposed the still-live mode directly. In 2D and 3D this lost the
required canonical re-entry pose but geometry remained. In 4D the teardown also
cleared renderer instances, bounds, `B`, and `L`, so the exposed viewport was
blank. The viewport, renderer node, presentation root, and current camera all
remained visible and in the scene tree; the failure was missing presentation
reconstruction, not a hidden node, inactive viewport, wrong camera, or native
session loss.

Viewer navigation now emits an ownership request to the app. For a retained
live mode, the app restores running/paused state, live keyboard ownership,
snapshot/Ghost/HUD rendering, canonical presentation, bounds, geometry, camera,
and framing, then opens Viewer. Native gameplay is never reset or recreated.
Because Main Menu is an E4 presentation-context destruction boundary, the
deliberately noncanonical prior pose is not preserved; 2D, 3D, and 4D re-enter
their defined canonical presentation. Actual replay mode continues through the
unchanged replay path.

Reset recovered the old failure because its composite contract reconstructs
4D `B`, `L`, renderer geometry/bounds, canonical outer view, and fitted framing.
Fit intentionally reads existing valid bounds and changes framing only; with
the renderer cleared and bounds invalid, it correctly could not repair the
presentation. Fit semantics remain unchanged.

The rebuilt outside-tree exported app passed the exact Live-4D sequence with a
populated Hold: the board remained visible after Viewer without Fit, Reset, or
Restart; post-return Hold input was accepted; and selecting an actual 4D replay
still opened a valid replay view.

## Finding classification

- Release blocker: the first export correctly failed because macOS universal
  export texture support was disabled. The project now enables the required
  ETC2/ASTC import path; repeated exports pass.
- Release blocker: the previous native macOS build inherited the host's macOS
  deployment target. The release build now pins 13.0 and validates universal
  source and packaged frameworks.
- Release blocker: no checked-in Godot export preset or current Godot release
  workflow existed. Both now exist and are policy-pinned.
- Bounded release hardening: exact metadata, clean export HOME, framework
  metadata, signature checks, outside-tree two-user smoke, and current CI were
  added.
- Post-release polish: Standard Live-4D volumes remain slightly less legible
  than equivalent 2D/3D boards; Standard remains usable and High Contrast is
  strong.
- New features deferred: remapping, gamepad, audio, campaign, progression,
  Explorer, simulation, stores, notarization, and unsupported-platform
  installers.

### Bounded 4D polish decision

Disposition B: no sufficiently obvious low-risk presentation-only change was
better than the human-accepted Stage 54F candidate. The renderer, projection,
layout ownership, #69/#70 hierarchy, controls, and gameplay remain unchanged.
The known Standard-mode difference remains non-blocking post-release polish.

## Automated verification

Completed focused evidence:

- executable all-mode live-navigation lifecycle regression, including
  unchanged native bridge/state hash/snapshot, Hold, NEXT, Hold availability,
  Ghost destination, canonical re-entry, restored geometry/bounds/camera,
  retained running/paused state, input/focus ownership, Fit preservation, and
  replay isolation;
- pre-fix mutation evidence: seven expected failures across 2D/3D canonical
  re-entry and 4D session/bounds/grid/cells/canonical re-entry; zero failures
  after the correction;
- release packaging unit tests and shell syntax;
- workflow YAML parsing;
- project-contract and generated-configuration checks;
- `git diff --check`;
- repository sanitation;
- keybinding contract;
- native unit/conformance suite: 103 tests and 50 subtests; and
- repeated current-platform build/export/signature/outside-tree smoke.

Final frozen-candidate gates:

- `GODOT_BIN=<exact-4.7.1-editor> ./scripts/verify_godot_4_7.sh`: passed with
  `Godot 4.7.1 verification passed.`; and
- `CODEX_MODE=1 ./scripts/verify.sh`: passed with `verify: OK`.

The pinned Godot suite emits expected diagnostics from deliberate invalid-input
tests and its editor/test teardown, while ordinary exported-candidate smoke and
real-window logs contain no error or warning diagnostics.

## Independent blocker re-acceptance — pending

The prior independent matrix passed all other release surfaces. The human
reviewer may therefore use the rebuilt exported app for this narrow re-test:

1. start Live 4D and establish a visible board, preferably with populated Hold
   and a deliberately changed view;
2. navigate Main Menu, Advanced / Diagnostics, Replay Demos, and Viewer;
3. confirm the live board is visible without Fit, Reset, or Restart and that
   gameplay, Hold, NEXT, Ghost, pause state, camera input, and keyboard input
   remain correct;
4. open a real replay and confirm replay UI/camera behavior; and
5. perform quick 2D and 3D Viewer-return checks because the owner seam is
   shared.

Any crash, export/startup/native failure, source-tree dependency, incorrect
persistence, stale Hold/NEXT/Ghost state, unreachable required UI, replay
corruption, control/help mismatch, unreadable core 4D play, or false platform
claim changes this candidate to CHANGES REQUIRED.

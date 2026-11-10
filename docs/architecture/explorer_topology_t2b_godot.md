# T2B Godot Explorer integration

Scope: playable rank-2 bounded rectangle, X/Y cylinders and torus translations.
The T1 piece contract and T2A provider remain the semantic source; this slice
makes no terminal Python/native authority transfer. Rotation, twisted seams,
advanced inspection and 3D/4D topology execution remain deferred.

## Ownership and interface

The existing Explorer app, panel, input contract and renderer own presentation.
`explorer_2d_adapter.gd` holds only a detached snapshot. `Tet4DCoreApi.explorer_2d`
owns an independent `ExplorerPieceRuntime`, never a live Play session.
Requests are exact dictionaries selected by `op`: begin/profile (canonical v1
profile), replace (catalog index), snapshot, close, retry, propose (revision,
complete source, action), inverse (revision, recorded descriptor), apply
(complete candidate). Results carry `ok`, snapshot/revision or candidate, and
structured `error.code` on failure. Exact recursive Variant comparison rejects
coercion, omitted/extra fields and tampering before native apply. State import
is intentionally unavailable: callers can propose only against the exact
current canonical snapshot. Inverse accepts the latest retained descriptor.
Native proposals and runtime apply retain all validity authority.

Catalog creation normalizes and lexicographically indexes production classic
pieces once. Every new session receives a new namespace; replacements receive
monotonic ordinals. Retry retains identity. Profile changes preserve the selected
catalog piece and identity but establish a fresh initial placement, advance the
revision and clear inverses. The UI explicitly announces this reset.

## Acceptance and evidence plan

Provider: native whole-piece conformance and production extension build.
Consumer: actual extension strict types, complete preservation on failure,
canonical coordinates/IDs/frames, both directions on every profile, partial
crossings, inverse and Retry. Integration: existing Explorer entry and controls,
no gravity, exact renderer snapshot, view independence, Play hash isolation,
and unchanged 3D/4D suites. Run the governed full gate and Godot verifier.
Human acceptance separately exercises bounded walls, both cylinders, torus
split cells/Retry, and return to ordinary Play. Headless success is not visual
or human acceptance.

## Fullscreen integration and owner observation (2026-11-10)

T2B incorporates the safe-area correction from `fa3312c3` (PR #179):
translate the display safe rectangle into window coordinates before deriving
outer margins. This preserves existing Godot presentation ownership and avoids
pushing the shell off-screen when fullscreen runs on an offset monitor. The
associated offset-display and notch regressions accompany the correction.

The owner reports that cylinder and torus work in the 2D Explorer. This is
partial human acceptance, not a claim that both cylinder axes, every crossing,
Retry, bounded rejection, and return to Play have all been checked. Fullscreen
acceptance after incorporating this correction remains to be confirmed.

Verification of the integrated fullscreen correction: focused safe-area checks
passed; `scripts/verify_godot_4_7.sh` passed all 98 scripts and 59 shared topology
parity cases on Godot 4.7.2. This does not substitute for the remaining human
interaction checks above.

## Main Menu entry (2026-11-10)

The Main Menu Explorer card and its `E` shortcut emit one `explorer` action
(`ReplayHud.EXPLORER_ENTRY_ACTION`). The app resumes a retained Explorer in its
own dimension; with none retained (Play and replay clear it) it opens the 2D
topology Explorer, and the panel's 3D/4D buttons step up from there. The locked
Main Menu card list is unchanged. `test_practice_explorer.gd` presses the real
card and panel buttons and fails if the entry is pointed back at 4D.

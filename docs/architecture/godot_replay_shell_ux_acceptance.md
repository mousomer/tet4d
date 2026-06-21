# Godot Replay Shell UX Acceptance

Stage 30 accepts the current Godot replay shell as a usable product-shell
baseline after a manual launch pass and focused shell UX fixes. This is not a
parity stage, a gameplay stage, a native authority stage, or an authority
transfer.

## Scope

Allowed Stage 30 work:

- Godot replay shell layout and readability;
- generated shell settings panel readability;
- shell theme selection visibility;
- Godot shell tests for layout/settings/theme behavior;
- documentation of manual UX acceptance.

Forbidden Stage 30 work remains unchanged: no Python gameplay, topology,
movement, rotation, collision, scoring, trace semantics, replay correctness,
golden/parity fixtures, native semantic code, keyboard rebinding, gameplay
settings, or authority transfer.

## Manual UX Result

Manual launch command:

```bash
godot --path godot/Tet4D.Godot
```

Observed on June 21, 2026:

- the Godot shell launches without visible project errors;
- the main menu is readable;
- the screen title and replay-only Python-oracle subtitle are visible;
- menu actions are visible and not clipped;
- the shell can be brought to the foreground and captured for visual review.

Manual click/navigation from the automation environment was blocked by macOS
assistive-access permissions:

```text
System Events got an error: osascript is not allowed assistive access. (-25211)
```

Because of that external OS permission, Stage 30 manual evidence covers launch
and main-menu readability directly, while deeper settings/replay navigation is
covered by Godot headless tests and documented as an unverified manual area.

## UX Fixes

Stage 30 keeps fixes small and shell-local:

- `Plain` display mode now routes to a distinct Godot theme and visual palette
  instead of silently reusing Diagnostic High Contrast.
- The generated settings panel now has a compact title and shell-only subtitle.
- Settings labels wrap rather than clipping inside the fixed right inspector.
- Settings row control widths were tightened for the reserved inspector width.
- The replay layout contract now reports the settings panel rectangle so tests
  can guard horizontal reachability inside the right inspector.

These fixes affect presentation only. They do not alter copied trace data,
gameplay results, topology behavior, Python config, parity harnesses, or native
semantic state.

## Automated Acceptance Coverage

Godot tests cover the Stage 30 acceptance surface:

- theme resources load for Diagnostic, Tron, and Plain;
- Plain has a visibly distinct accent/palette from Diagnostic;
- the settings panel uses a `ScrollContainer`;
- generated settings include title/subtitle, category sections, wrapped labels,
  checkbox controls for booleans, slider groups with numeric labels for numeric
  values, and dropdown options for enums;
- the replay viewer layout keeps the right inspector reserved and confirms the
  settings panel remains horizontally reachable inside it.

## Boundary

Python remains the gameplay semantic oracle. Godot remains a product shell,
replay-view presentation surface, diagnostics surface, and local shell-settings
owner. Stage 30 adds no gameplay/topology/movement settings, no pygame menu
port, no C++/GDExtension semantic implementation, no parity slice, and no
authority transfer.

## Risks

- Manual settings/replay navigation is still pending a local OS environment
  with assistive access or direct human interaction.
- Visual theme distinctness is guarded mechanically, but full aesthetic
  acceptance remains a manual product judgment.

# Godot Visual Style Authority

Stage 31 defines the visual style authority for the Godot product shell. It
codifies the intended visual direction and MVP baseline for future Godot visual
implementation work. It is not an implementation stage, a parity stage, a
gameplay stage, a native authority stage, or an authority transfer.

## Purpose

This document owns the visual style direction for the Godot replay/settings
shell. Future Godot visual implementation should use this file before changing
theme resources, style tokens, shell UI layout styling, board/replay
presentation, inspector panels, diagnostics overlays, settings rows, or
keyboard-hint presentation.

The Godot replay/settings shell MVP baseline is accepted with known
manual-navigation limitations. The shell launches, layout is stable, settings
are generated from a shell-only registry, and automated Godot tests pass.
macOS assistive-access restrictions block automated click/navigation in the
current automation environment, but manual readability was verified in
Stage 30.

## Visual Direction

The Godot visual direction is:

```text
diagrammatic, readable, high-contrast, technical, lightly futuristic
```

The board must read as a mathematical/diagnostic 4D object, not as a realistic
3D world. The product shell should feel clear, controlled, technical, legible,
slightly neon when using the Tron theme, not game-arcade noisy, not
skeuomorphic, and not pseudo-realistic.

Rendering principle:

```text
diagrammatic rendering over realism
```

The Godot shell is a product shell and replay/viewer. It must remain read-only
with respect to gameplay semantics.

## Theme Model

Keep exactly these three themes for now:

| Theme ID | Display label | Purpose |
| --- | --- | --- |
| `diagnostic` | Diagnostic | High-readability development/debug view |
| `plain` | Plain | Neutral clean product view |
| `tron` | Tron | Stylized neon/futuristic presentation |

Do not add more themes until a later authority update explicitly changes this
model.

## Colour Roles

Future Godot style implementation must use semantic colour roles. Do not
hard-code visual colours directly into arbitrary UI nodes in future
implementation stages. Colours should be routed through theme/style tokens.

Required colour roles:

```text
background.primary
background.panel
background.board
background.elevated

text.primary
text.secondary
text.muted
text.inverse

accent.primary
accent.secondary
accent.focus

grid.major
grid.minor
grid.axis

cell.active
cell.locked
cell.ghost
cell.preview

trace.current
trace.past
trace.future

label.w_layer
label.axis
label.hint

diagnostic.bounds
diagnostic.metadata

state.warning
state.error
state.success
```

## Diagnostic Palette

Purpose: readable development/debug view.

```text
background.primary   #101318
background.panel     #171C24
background.board     #0A0D12
background.elevated  #202735

text.primary         #F2F6FF
text.secondary       #D3DAE6
text.muted           #8C98AA
text.inverse         #0A0D12

accent.primary       #64B5FF
accent.secondary     #FFD166
accent.focus         #9CDCFE

grid.major           #5E6B7A
grid.minor           #2F3844
grid.axis            #A7B5C8

cell.active          #7DD3FC
cell.locked          #A78BFA
cell.ghost           #4B5563
cell.preview         #93C5FD

trace.current        #34D399
trace.past           #64748B
trace.future         #FBBF24

label.w_layer        #FDE68A
label.axis           #C7D2FE
label.hint           #A5B4FC

diagnostic.bounds    #F97316
diagnostic.metadata  #38BDF8

state.warning        #FBBF24
state.error          #F87171
state.success        #34D399
```

## Plain Palette

Purpose: neutral product view.

```text
background.primary   #F4F6F8
background.panel     #FFFFFF
background.board     #E9EEF3
background.elevated  #FFFFFF

text.primary         #111827
text.secondary       #374151
text.muted           #6B7280
text.inverse         #FFFFFF

accent.primary       #2563EB
accent.secondary     #7C3AED
accent.focus         #1D4ED8

grid.major           #9CA3AF
grid.minor           #D1D5DB
grid.axis            #4B5563

cell.active          #0284C7
cell.locked          #7C3AED
cell.ghost           #CBD5E1
cell.preview         #60A5FA

trace.current        #059669
trace.past           #94A3B8
trace.future         #D97706

label.w_layer        #92400E
label.axis           #4338CA
label.hint           #475569

diagnostic.bounds    #EA580C
diagnostic.metadata  #0369A1

state.warning        #D97706
state.error          #DC2626
state.success        #059669
```

## Tron Palette

Purpose: stylized neon/futuristic presentation.

```text
background.primary   #05070D
background.panel     #0B1020
background.board     #02040A
background.elevated  #101A33

text.primary         #E6FBFF
text.secondary       #A9F3FF
text.muted           #5E8794
text.inverse         #02040A

accent.primary       #00E5FF
accent.secondary     #FF2BD6
accent.focus         #7CFF6B

grid.major           #00A7C4
grid.minor           #123B4A
grid.axis            #7CFF6B

cell.active          #00E5FF
cell.locked          #FF2BD6
cell.ghost           #24424D
cell.preview         #7CFF6B

trace.current        #7CFF6B
trace.past           #255A68
trace.future         #FFD166

label.w_layer        #FFD166
label.axis           #00E5FF
label.hint           #FF8AF0

diagnostic.bounds    #FF7A00
diagnostic.metadata  #00E5FF

state.warning        #FFD166
state.error          #FF4D6D
state.success        #7CFF6B
```

## Typography Rules

The Godot shell should use a clear sans-serif UI style.

| Role | Use |
| --- | --- |
| `title` | panel titles and shell title |
| `section_header` | settings sections / inspector groups |
| `body` | normal UI text |
| `caption` | descriptions, muted helper text |
| `monospace` | trace IDs, schema versions, hashes, frame indexes |

Sizing guidance:

```text
title: 20-24 px
section_header: 15-17 px
body: 13-15 px
caption: 11-13 px
monospace: 12-14 px
```

Hard rules:

- Trace IDs, schema versions, frame indexes, and hashes should use monospace.
- Settings descriptions should use caption styling and wrap.
- Keyboard hints should be readable but visually secondary.
- Do not bundle font files.
- Do not vendor external fonts.
- Use Godot/system defaults unless the repository already has approved font
  assets.

## Spacing And Layout Rules

Spacing scale:

```text
space.1 = 4 px
space.2 = 8 px
space.3 = 12 px
space.4 = 16 px
space.5 = 24 px
space.6 = 32 px
```

Layout rules:

- Panel padding should generally use `space.3` or `space.4`.
- Rows should have at least `space.2` vertical separation.
- Major sections should have at least `space.4` separation.
- Inspector content must not clip horizontally.
- Scrollable content must use explicit `ScrollContainer` behavior.
- Board area must not consume the right inspector.

Stage 31 documents this scale. Implementation belongs to Stage 32 or a later
explicit visual implementation stage.

## Component Style Rules

### Panels

- Panels use `background.panel`.
- Elevated/active panels use `background.elevated`.
- Panel borders use `grid.minor` or `accent.primary` depending on theme.
- Panel corners should be subtle, not cartoonish.

### Buttons

- Normal buttons use `background.elevated` with `text.primary`.
- Primary/focused actions use `accent.primary`.
- Danger/destructive actions use `state.error`.
- Buttons must have clear hover/focus states.

### Sliders

- Sliders are numeric only.
- Slider fill uses `accent.primary`.
- Slider value labels are required.
- Projection/replay speed sliders must clearly communicate visual-only scope.

### Checkboxes And Toggles

- Boolean settings use checkbox/toggle only.
- Never use sliders for booleans.

### Dropdowns

- Enum settings use dropdown/option button only.
- Theme selection must be a dropdown.
- Never use sliders for enums.

### Settings Rows

- Each row has label plus description on the left and generated control on the
  right.
- Descriptions wrap.
- Controls remain aligned.
- Rows must not clip horizontally.

## Board And Replay Visual Language

The board/replay view is part of this visual style authority.

- The board is diagrammatic.
- Grid lines should clarify structure, not dominate it.
- Major grid lines should be distinguishable from minor grid lines.
- Active/current trace state should be visually distinct.
- Past trace state should be muted.
- Future/preview state should be distinguishable but not dominant.
- W/layer labels must be legible and consistently placed.
- Projection strength is visual emphasis only; it must not imply semantic
  coordinate changes.

Forbidden visual implication:

- Do not use styling that suggests Godot is simulating gameplay.
- Do not animate fake movement as if it were semantic replay.
- Do not visually invent topology transitions that are not present in trace
  data.

## Accessibility And Readability Constraints

- Diagnostic and Plain themes must be readable at normal laptop size.
- Text contrast must be high enough for ordinary UI use.
- Settings descriptions must wrap, not clip.
- Right inspector must remain usable at supported minimum width.
- Keyboard hints must be readable when enabled.
- Theme differences must be visible and not purely cosmetic.
- The Tron theme may be stylized but must still be usable.

## MVP Baseline Decision

Decision: accept the current Godot replay/settings shell as the MVP baseline
for visual-style implementation.

The baseline is accepted because the shell launches, the layout is stable, the
right inspector is protected by the Stage 28 layout contract, settings are
generated from the Stage 29 shell-only registry, Stage 30 verified manual
readability, and automated Godot tests pass.

Caveat: automated click/navigation remains limited on macOS when
assistive-access permission is denied. This is an environment limitation, not a
semantic or shell architecture failure.

The MVP baseline does not mean the product is finished. It means the shell is
stable enough to style.

## Future Implementation Guidance

The next implementation stage should:

- map these semantic roles into Godot theme/style tokens;
- keep the three theme IDs `diagnostic`, `plain`, and `tron`;
- preserve the shell settings registry as shell-only;
- keep generated settings controls aligned with the component rules above;
- keep board/replay rendering diagrammatic rather than realistic;
- add or update Godot-facing tests for any changed theme resources, style
  scripts, or visual shell behavior.

Future implementation must not add gameplay, topology, movement, keyboard
rebinding, parity, or native semantic settings under the cover of visual style.

## Boundary

This visual authority does not transfer gameplay authority to Godot. Python
remains the gameplay semantic oracle. Godot owns product-shell presentation
only.

This document does not authorize gameplay/topology/movement implementation in
Godot. This document does not authorize C++/GDExtension semantic authority.
This document does not port pygame UI history. This document does not add a
new parity slice and does not transfer authority.

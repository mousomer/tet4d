# Godot game UI best practices and toolkit assessment

Role: reference
Status: reference
Reviewed: 2026-11-22
Repository basis: `mousomer/tet4d` master as read on 2026-11-22
Verification: documentation and source inspection only; **no library installed, runtime sample executed or usability test performed**

## 1. What applies to Tet4D

**Game UX is not merely attractive shell chrome.** The player must parse active and locked cells, 3D/4D depth and slice structure, NEXT/HOLD, piece transformations, camera/view transformations, and current state while under cognitive load. Decoration that delays those readings is a usability defect even if a screenshot looks polished.

- *Visual hierarchy:* make the playable board the immediate focus, followed by status and next/hold, then control hints, then diagnostics. Preserve the governed board hierarchy: active/locked/ghost > active frame > wireframe > grid > floor > background.
- *Recognition rather than recall:* visible, short action labels and keyboard/controller glyphs derived from the binding source. A help page alone cannot rescue unlabeled piece/view/camera distinctions.
- *Feedback and mode awareness:* show when the game is paused, when a move fails, when an Explorer seam is crossed, or when focus is in a menu. Use words plus shape, not color alone.
- *Learning curve:* the shell should show only essential controls initially and reveal technical alternatives when asked. Explorer must be approachable for understanding 4D rotation rather than resembling a debugging console.
- *Spatial continuity:* transformations and state transitions must not silently recenter, reorient or reset the board. Visual effects must not misrepresent cell adjacency or topology.
- *Aesthetic consistency:* reuse the same functional component across dimensions and across Play/Explorer, with two skins rather than two implementations.
- *Responsive UI:* Godot `Control` anchors and `Container` reflow with explicit focus/navigation; never simply scale a fixed 4D inspector until text becomes unreadable.
- *Accessibility:* readable typography, normal and High Contrast, keyboard navigation, sensible touch reach, reduced motion, controls that do not require recognizing a color alone, consistent help placement.
- *Measure usability:* novice tasks, wrong-command rates, time-to-first-success, focus navigation, clipping/snapshot comparisons and reader interpretation of neighboring 3D cells and 4D slice identity.

## 2. Evidence-backed principles

| Practice | Source | Tet4D implication |
| --- | --- | --- |
| Visibility of system status, recognition over recall, error prevention, minimalist design | Nielsen Norman Group — https://www.nngroup.com/articles/ten-usability-heuristics/ | Keep mode/status visible and input hints adjacent to actions |
| Navigation, focus, clear hierarchy and multiple input modes | Xbox Accessibility Guideline 112 — https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/112 | Test tab order and focus after all panel reflow and modal transitions |
| Context and comprehensible game controls | Xbox Accessibility Guideline 114 — https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/114 | Never expose unexplained XY/XW/W layer jargon without explanation |
| Goals and progress indication | Xbox Accessibility Guideline 109 — https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/109 | State the current target or next Explorer learning action |
| Text and contrast | Xbox Guidelines 101 / 102 — https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/101 and https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/102 | Verify readable labels in every shell state |
| Common access needs: remapping, text size, color blindness, captions | Game Accessibility Guidelines — https://gameaccessibilityguidelines.com/basic/ | Keep control binding behavior truthful; protect UI scale and color-independent meaning |
| Text 4.5:1 normal / 3:1 large; essential non-text UI 3:1 | WCAG 2.2 — https://www.w3.org/TR/WCAG22/ | Use as pragmatic numeric quality targets, not a claim of game WCAG certification |
| Godot Themes, type variations, responsive Controls and Containers | Godot stable documentation — https://docs.godotengine.org/en/stable/tutorials/ui/ | Native first; Theme variation can style without changing control identity |

## 3. Tested facts versus publisher claims

The following describes project documentation and metadata, not independent runtime verification.

| Option | Features from primary source | Version / integration risk | Decision |
| --- | --- | --- | --- |
| Native Godot Theme + Tet4D `ShellStyleManager` | Existing three palettes, role-based coloring, token constants, style applier, theme type variations, responsive policy | Already owned by Tet4D; local name-based rules need cleanup | **Default production architecture** |
| WoldUI | Token-generated UI themes; text, spacing, component styles, scope overrides, controller prompts, icons | Upstream README states v1.2.0 / Godot 4.7+; GitHub release v1.2.0 published 2026-10-14, MIT. Godot Asset Store currently shows an older v1.1.0 listing marked unstable. Competing project-wide Theme authority likely | **Isolated token/component spike** |
| gohud | Complete HUD/menu/form widgets, 14 skins (app-like Material and sci-fi/arcade), touch/safe areas, keyboard, icons | Upstream README states v1.3.0 / Godot 4.7+, MIT; 86 widget/service classes. Larger dependency/overlap surface; no shipping tests performed here | **Isolated component spike** |
| Theme Assist | Theme editor and component gallery | Store claims mixed stable/unstable status; asset declares AI use; not independently evaluated | **Reference only** |
| ThemeGen | Programmatic native `Theme` generation | More compatible with native ownership in principle, but duplicates existing custom style manager if used uncritically | **Reference only** |

Links:
- WoldUI: https://github.com/Holthouse/woldui-godot and https://store.godotengine.org/asset/holthouse/woldui/
- WoldUI v1.2.0 release: https://github.com/Holthouse/woldui-godot/releases/tag/v1.2.0
- gohud: https://github.com/thruthesky/gohud and https://thruthesky.github.io/gohud/
- Theme Assist: https://store.godotengine.org/asset/undiscovered-entertainment/theme-assist/
- ThemeGen: https://github.com/Inspiaaa/ThemeGen

## 4. Architectural incompatibilities to evaluate

**WoldUI:** it wants to generate and apply a project `Theme` from its own tokens. Tet4D already has a role palette manager and per-control style overrides. If both manage the same property, precedence and live theme-switching become uncertain. Any adapter must prove a single owner and no double application. WoldUI's optional automatic sound/hover/ripple effects are not appropriate as an unexamined global setting in a real-time puzzle game.

**gohud:** it can replace app chrome and skins, but wholesale menu/HUD replacement risks losing nuanced focus, responsive sizing, existing Explorer view/piece control semantics and presentation settings. Start by testing reusable isolated widgets; do not drive game state through gohud-specific navigation or preset engines.

**Using both at once:** not a design system. Two incompatible theme registries, local style overrides, input/focus layers and upgrade paths would increase regressions. "Both looks" means **one UI under two visual identities**, not **two installed UI frameworks**.

## 5. Prototype comparison protocol

Use the same three prototype scenes for each approach: (1) menu with Play/Explorer/Settings; (2) 4D HUD with board placeholder, NEXT/HOLD, Piece/View help and pause; (3) compact settings panel showing theme/contrast/scale. Avoid changing production scenes.

Record:
- Godot 4.7.2 import/parser success, license and asset notices.
- Runtime theme switching from Instrument to Vector Arcade and back, including CanvasLayer and popups.
- Component ownership map: which source owns fonts, colors, spacing, focus style, animation and accessibility state.
- Keyboard and gamepad navigation, focus persistence, screen-reader metadata where available.
- Text contrast and 3:1 state-indicator contrast; dark/light theme legibility.
- 680x520, 960x640, 1280x800, 1600x960 and 1920x1080 windows, plus tablet orientations.
- Runtime/frame and memory comparison, exported package size, platform renderer and initialization side effects.
- Migration lines/files impacted, reusability across 2D/3D/4D and Explorer, diagnostics on fallback.

Score each candidate on weighted criteria in the implementation plan. A native-only result is acceptable and likely lower-risk. No visual claim is accepted without rendered evidence.

## 6. Visual reference caution

Commercial puzzle/game screenshots can help compare HUD priority, board framing and restraint, but they are visual references, **not assets for import**. Do not copy other games' screen graphics, trade dress, logos, fonts, icon bundles or protected artwork into Tet4D. Create original mockups and license-check all libraries/assets.

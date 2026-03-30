# Researched Guidelines And Current Issues

Status: Active  
Last verified: 2026-02-20

## 1. Guidelines used (manuals and standards)

1. WAI-ARIA APG menu patterns:
2. [Menu Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/)
3. [Menu and Menubar Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)
4. WCAG 2.2:
5. [Consistent Help](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html)
6. [Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
7. [Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance)
8. Microsoft menu/flyout guidance:
9. [Menus and context flyouts](https://learn.microsoft.com/en-us/windows/apps/design/controls/menu-and-context-flyouts)
10. Material menu guidance:
11. [Material menus](https://m1.material.io/components/menus.html)
12. Nielsen heuristics:
13. [Ten usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
14. Apple HIG menus:
15. [Menus](https://developer.apple.com/design/human-interface-guidelines/menus)
16. Xbox accessibility guidelines:
17. [XAG 112](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/112)
18. [XAG 114](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/114)
19. Game accessibility baseline:
20. [Basic Guidelines](https://gameaccessibilityguidelines.com/basic/)
21. Content structuring reference:
22. [ONS structuring content](https://service-manual.ons.gov.uk/content/writing-for-users/structuring-content)

## 2. Core rules derived from those sources

1. Keep keyboard behavior predictable and consistent across menu contexts.
2. Preserve visible focus and contrast in all menu states and window sizes.
3. Keep help in predictable locations and retain direct in-game access.
4. Prefer short, scannable labels and shallow menu depth.
5. Show immediate status feedback after user actions (save/load/reset/apply).
6. Keep context menus context-specific and avoid overloading them as global navigation.
7. Prefer recognition over recall: place key/action hints near controls.

## 3. Current issues (open backlog)

1. Active open items are tracked in `config/project/backlog_debt.json` (`active_debt_items`).
2. Current active open items: `BKL-P1-010` (tutorial panel obstruction risk), `BKL-P1-011` (zoom tutorial step-count parity).
3. Current operational watch IDs: `BKL-P3-002`, `BKL-P3-003`, `BKL-P3-006`, `BKL-P3-007`, `BKL-P3-009`, `BKL-P3-013`.
4. Canonical source of active status is `docs/BACKLOG.md` + `config/project/backlog_debt.json`.

## 4. Active plan artifacts

1. Help/menu restructuring report and execution plan:
2. `docs/history/plans/PLAN_HELP_AND_MENU_RESTRUCTURE_2026-02-19.md`
3. Menu rehaul v2 and macbook no-keypad controls plan:
4. `docs/history/plans/PLAN_MENU_REHAUL_V2_2026-02-20.md`
5. Unreferenced-helper and dedup follow-up plan:
6. `docs/history/plans/PLAN_UNREFERENCED_HELPERS_AND_CODE_REDUCTION_2026-02-19.md`

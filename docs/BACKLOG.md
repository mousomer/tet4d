# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-02-20  
Scope: unified view of implemented change set + unresolved RDS/documentation/code gaps.

## 1. Priority Verification Rules

1. `P1`= user-facing correctness, consistency, and discoverability gaps.
2. `P2`= maintainability and complexity risks that can cause regressions.
3. `P3`= optimization, tuning, and documentation hygiene.

## 2. Unified Change Set (Implemented Baseline)

1. `DONE` Pause/main menu parity updates: launcher and pause both expose settings, bot options, keybindings, help, and quit.
2. `DONE`Keybindings menu now supports`General/2D/3D/4D` scopes and clear category separation (`gameplay/camera/system`).
3. `DONE` General keybindings are now separated in the main keybindings menu (not merged into default dimension views).
4. `DONE` Help expanded to include full key reference, settings reference, concepts, and control animation guidance.
5. `DONE`Keybinding/settings category docs externalized in`config/menu/structure.json`and validated in`tetris_nd/menu_config.py`.
6. `DONE`4D helper-grid guidance now extends across all rendered`w`-layer boards.
7. `DONE` Pause row handler refactored to table-driven dispatch (complexity hotspot removed).
8. `DONE`Shared 3D/4D side-panel helpers extracted to`tetris_nd/panel_utils.py`.
9. `DONE`Shared 3D/4D runtime loop orchestration extracted to`tetris_nd/loop_runner_nd.py`.
10. `DONE` RDS wording and status metadata normalized (verified date and active status alignment).
11. `DONE` Baseline CI/runtime verification was previously green for this batch.
12. `DONE` `ruff check` currently passes.
13. `DONE` `pytest -q` currently passes.
14. `DONE` `./scripts/ci_check.sh` is available and remains the expected local CI command.
15. `DONE` P2 frontend split executed:
16. `DONE`launcher flow extracted to`tetris_nd/launcher_play.py`.
17. `DONE`launcher settings/audio/display hub extracted to`tetris_nd/launcher_settings.py`.
18. `DONE`3D setup/menu/config extracted to`tetris_nd/front3d_setup.py`.
19. `DONE`4D render/view/clear animation layer extracted to`tetris_nd/front4d_render.py`.
20. `DONE` P3 tuning/tooling executed:
21. `DONE`playbot policy budgets/thresholds retuned in`config/playbot/policy.json`.
22. `DONE`offline policy comparison tool added:`tools/analyze_playbot_policies.py`.
23. `DONE` Translation/rotation arrow-diagram guide panel integrated into launcher menu, pause menu, unified settings, and keybindings menus.
24. `DONE` Complexity hotspots reduced in:
25. `tetris_nd/keybindings_menu.py` (`_run_menu_action`,`run_keybindings_menu`),
26. `tetris_nd/launcher_settings.py` (`run_settings_hub_menu`).
27. `DONE` New shared menu helper module added for arrow-diagram guide rendering:
28. `tetris_nd/menu_control_guides.py`.
29. `DONE` Validation after this batch:
30. `ruff check` passed,
31. `ruff check --select C901` passed,
32. `pytest -q` passed.
33. `DONE` In-game side panels now include compact translation/rotation diagram guidance via shared control-helper rendering.
34. `DONE`CI now runs across Python`3.11`,`3.12`,`3.13`, and`3.14` via workflow matrix.
35. `DONE` Score analyzer design was codified as a dedicated RDS and initial runtime integration was added:
36. `DONE`config:`config/gameplay/score_analyzer.json`,
37. `DONE`runtime module:`tetris_nd/score_analyzer.py`,
38. `DONE` HUD summary lines now render quality/board-health/trend in 2D/3D/4D side panels.
39. `DONE`4D dry-run stability hardening applied (higher dry-run budget floor + deterministic greedy fallback in dry-run path).
40. `DONE` Canonical maintenance contract added in:
41. `config/project/canonical_maintenance.json`
42. `DONE` Machine validator added and CI-wired:
43. `tools/validate_project_contracts.py`+`scripts/ci_check.sh`
44. `DONE` Contract coverage includes docs/help/tests/config synchronization checks.
45. `DONE` Canonical-maintenance expansion connected and enforced:
46. settings/save-state schemas + migration docs,
47. replay manifest + golden fixture directory,
48. help index + help asset manifest,
49. release checklist.
50. `DONE` Score analyzer phase-2 implementation completed:
51. analyzer settings are exposed in unified settings (`Audio/Display/Analytics`),
52. logging toggle persists via menu state and controls event/summary file writes,
53. analyzer protocol/persistence tests added in `tetris_nd/tests/test_score_analyzer.py`.
54. `DONE` CI stability follow-up implemented:
55. repeated dry-run stability tool added at `tools/check_playbot_stability.py`,
56. wired into local CI script (`scripts/ci_check.sh`).
57. `DONE` Small-window readability pass completed:
58. control helper rows now use constrained key/action columns to avoid overlap,
59. help controls page switches to stacked diagram layout on narrow windows.
60. `DONE` `launcher_settings.py` simplified by removing legacy dead paths and retaining one unified settings flow.
61. `DONE` Local CI runner was hardened to a hermetic Python-module flow:
62. `scripts/ci_check.sh` now requires `ruff` and `pytest` in the selected `PYTHON_BIN`,
63. global command fallback for lint/test runners was removed.
64. `DONE` Local toolchain bootstrap was standardized:
65. `scripts/bootstrap_env.sh` now creates/updates `.venv` and installs `pygame-ce`, `ruff`, and `pytest`.
66. `DONE` Canonical docs freshness checks were strengthened:
67. `tools/validate_project_contracts.py` now supports regex content rules,
68. stale fixed pass-count snapshots are blocked by `must_not_match_regex` rules in `config/project/canonical_maintenance.json`.
69. `DONE` Control-helper optimization batch completed:
70. action icons are now cached by `(action,width,height)` in `tetris_nd/control_icons.py` to avoid repeated per-frame redraw.
71. dimensional helper rows are assembled from shared row-spec builders in `tetris_nd/control_helper.py` to reduce duplication.
72. parity tests added for control UI helpers:
73. `tetris_nd/tests/test_control_ui_helpers.py`.
74. `DONE` Simplification batch completed:
75. shared UI helpers extracted to `tetris_nd/ui_utils.py` and consumed by launcher/help/keybindings/control views.
76. pause/settings menu row definitions externalized into `config/menu/structure.json` and loaded via `tetris_nd/menu_config.py`.
77. shared pause/settings list-panel renderer applied in `tetris_nd/pause_menu.py`.
78. keybindings menu split into dedicated input/view helpers:
79. `tetris_nd/keybindings_menu_input.py`, `tetris_nd/keybindings_menu_view.py`.
80. shared ND launcher orchestration extracted to `tetris_nd/launcher_nd_runner.py`.
81. shared 2D/ND lookahead selection helper extracted to `tetris_nd/playbot/lookahead_common.py`.
82. playbot policy validation monolith reduced by section validators in `tetris_nd/runtime_config_validation.py`.
83. `DONE` Post-split verification:
84. `ruff check .` passed,
85. `ruff check . --select C901` passed,
86. `pytest -q` passed.
87. `DONE` Follow-up simplification batch completed:
88. nested runtime help callbacks removed in `front2d.py` and `tetris_nd/loop_runner_nd.py`,
89. gameplay tuning validator decomposition completed in `tetris_nd/runtime_config_validation.py`,
90. shared 3D/4D projected grid-mode rendering extracted to `tetris_nd/grid_mode_render.py`,
91. keybinding split finalized with `tetris_nd/keybindings_defaults.py` and `tetris_nd/keybindings_catalog.py`,
92. score-analyzer feature extraction completed in `tetris_nd/score_analyzer_features.py`,
93. 2D side-panel extraction completed in `tetris_nd/gfx_panel_2d.py` and wired through `tetris_nd/gfx_game.py`.
94. `DONE` Validation after follow-up batch:
95. `ruff check .` passed,
96. `ruff check . --select C901` passed,
97. `pytest -q` passed,
98. `./scripts/ci_check.sh` passed.
99. `DONE` Next-stage decomposition + optimization batch completed:
100. runtime config validation split into dedicated section modules:
101. `tetris_nd/runtime_config_validation_shared.py`,
102. `tetris_nd/runtime_config_validation_gameplay.py`,
103. `tetris_nd/runtime_config_validation_playbot.py`,
104. `tetris_nd/runtime_config_validation_audio.py`,
105. with API compatibility maintained via `tetris_nd/runtime_config_validation.py`.
106. 3D frontend render/runtime split completed:
107. render/view path extracted to `tetris_nd/front3d_render.py`,
108. runtime loop/input orchestration retained in streamlined `tetris_nd/front3d_game.py`.
109. rendering optimization pass completed:
110. cached menu gradients in `tetris_nd/ui_utils.py`,
111. bounded text-surface cache in `tetris_nd/panel_utils.py`,
112. 2D panel text rendering now uses cached surfaces via `tetris_nd/gfx_panel_2d.py`.
113. `DONE` Validation after next-stage batch:
114. `ruff check .` passed,
115. `ruff check . --select C901` passed,
116. `pytest -q` passed,
117. `./scripts/ci_check.sh` passed.
118. `DONE` Further runtime optimization batch completed:
119. shared text-render cache extracted to `tetris_nd/text_render_cache.py`,
120. control-helper text rendering now uses cached surfaces (`tetris_nd/control_helper.py`),
121. panel/text cache now shared through `tetris_nd/panel_utils.py` and used by 2D panel rendering,
122. 4D layer rendering optimized to avoid per-layer full-board rescans:
123. locked cells are pre-indexed by `w` layer once per frame in `tetris_nd/front4d_render.py`,
124. layer-grid layout rectangles are memoized in `tetris_nd/front4d_render.py`.
125. `DONE` Validation after further optimization batch:
126. `ruff check .` passed,
127. `ruff check . --select C901` passed,
128. `pytest -q` passed,
129. `./scripts/ci_check.sh` passed.
130. `DONE` Repository secret scanning policy + scanner added and CI/local CI enforced:
131. `config/project/secret_scan.json`,
132. `tools/scan_secrets.py`,
133. `scripts/ci_check.sh`.
134. `DONE` Path/constants externalization batch executed via:
135. `config/project/io_paths.json`,
136. `config/project/constants.json`,
137. `tetris_nd/project_config.py`,
138. and migrated consumers (`keybindings`, `menu_settings_state`, `runtime_config`, `score_analyzer`).
139. `DONE` Projection lattice caching + shared cached-gradient routing implemented in projection/render stack.
140. `DONE` Low-risk LOC-reduction batch executed:
141. pause-menu action dispatcher simplified and deduplicated in `tetris_nd/pause_menu.py`,
142. dead projected-grid draw helpers removed and shared cache-key helpers added in `tetris_nd/projection3d.py`,
143. shared projection cache-key builders wired into `tetris_nd/front3d_render.py` and `tetris_nd/front4d_render.py`,
144. score-analyzer validation/update flow consolidated in `tetris_nd/score_analyzer.py`.
145. `DONE` LOC snapshot after this batch:
146. Python LOC `22,934 -> 22,817` (`-117`),
147. non-test Python LOC `20,166 -> 20,049` (`-117`).
148. `DONE` Boundary topology preset baseline implemented/planned:
149. setup-level topology selector targets `bounded`,`wrap_all`,`invert_all` for 2D/3D/4D,
150. gravity-axis wrapping stays disabled by default,
151. deterministic replay/test coverage is required for topology-enabled runs.
152. `DONE` Small-profile rotation layout replanned to keyboard-pair ladder:
153. `2D`: `Q/W`,
154. `3D`: `Q/W`, `A/S`, `Z/X`,
155. `4D`: `Q/W`, `A/S`, `Z/X`, `R/T`, `F/G`, `V/B`.
156. `DONE` Default system-key conflicts were deconflicted for the new small 4D ladder by moving system defaults to:
157. restart=`Y`, toggle-grid=`C`.
158. `DONE` Advanced boundary-warping designer baseline implemented:
159. setup menus expose `topology_advanced` + hidden `topology_profile_index` controls,
160. per-axis/per-edge topology profile overrides are loaded from `config/topology/designer_presets.json`,
161. deterministic export path is available at `state/topology/selected_profile.json`.
162. `DONE` Config externalization follow-up implemented:
163. additional animation timings moved to `config/project/constants.json`,
164. runtime fallbacks are enforced via `tetris_nd/project_config.py`.
165. `DONE` Rotation-animation overlay rendering now uses topology-aware mapping across 2D/3D/4D frontends:
166. `tetris_nd/gfx_game.py`,
167. `tetris_nd/front3d_render.py`,
168. `tetris_nd/front4d_render.py`,
169. via shared overlay mapping in `tetris_nd/topology.py`.
170. `DONE` Invert-boundary seam traversal for seam-straddling ND pieces is stabilized by deterministic piece-level fallback mapping:
171. `tetris_nd/topology.py`,
172. with regressions in `tetris_nd/tests/test_topology.py` and `tetris_nd/tests/test_game_nd.py`.
173. `DONE` 4D view-plane camera turns (`xw`/`zw`) implemented as render-only animated controls:
174. `tetris_nd/front4d_render.py`,
175. with dedicated keybind actions (`view_xw_pos/neg`,`view_zw_pos/neg`) in:
176. `tetris_nd/keybindings_defaults.py`, `keybindings/4d.json`.
177. `DONE` 4D view-turn coverage added for routing separation, replay invariance, and render stability:
178. `tetris_nd/tests/test_nd_routing.py`,
179. `tetris_nd/tests/test_gameplay_replay.py`,
180. `tetris_nd/tests/test_front4d_render.py`.
181. `DONE` 4D renderer cache-key correctness hardening:
182. projection cache extras now include total `W` size to prevent stale lattice/helper cache reuse across differing 4D board depths.
183. `DONE` 4D hyper-view zoom-fit hardening:
184. per-layer zoom fit now accounts for `xw`/`zw` transforms and centered `w` offset; regression coverage added for outer-layer bounds.
185. `DONE` Full local gate revalidation executed through `scripts/ci_check.sh` after this batch.
186. `DONE` Black-box cross-config 4D frame-cache regression added and passing:
187. `tetris_nd/tests/test_front4d_render.py` now asserts distinct `4d-full` cache entries for differing total `W` sizes under full-frame draws.
188. `DONE` Projection-lattice cache observability helpers added for regression/profiling validation:
189. `tetris_nd/projection3d.py` (`clear_projection_lattice_cache`, `projection_lattice_cache_keys`, `projection_lattice_cache_size`).
190. `DONE` 4D render profiling tool added and exercised:
191. `tools/profile_4d_render.py` with latest report at `state/bench/4d_render_profile_latest.json`.
192. `DONE` Sparse hyper-view overhead threshold assertion passed (no immediate optimization needed).
193. `DONE` Unreferenced helper cleanup pass executed:
194. removed definition-only helpers in `tetris_nd/frontend_nd.py`, `tetris_nd/menu_keybinding_shortcuts.py`, `tetris_nd/menu_model.py`, `tetris_nd/project_config.py`, and `tetris_nd/score_analyzer.py`.
195. profiler/policy tool output paths remain constrained to project root (`tools/profile_4d_render.py`,`tools/bench_playbot.py`,`tools/analyze_playbot_policies.py`).
196. `DONE` Setup-menu dedup follow-up (`BKL-P2-007`) completed:
197. `tetris_nd/front3d_setup.py` was collapsed to a thin adapter over shared ND setup logic in `tetris_nd/frontend_nd.py`,
198. removing duplicated 3D setup render/value/config paths while preserving runtime behavior.
199. Added regression coverage:
200. `tetris_nd/tests/test_front3d_setup.py`.
201. `DONE (superseded)` 4D `xw`/`zw` board-slot permutation fix:
202. this improved panel ordering but did not satisfy basis-decomposition behavior (`xw` should swap board decomposition axes).
203. superseded by active `BKL-P1-001` for full basis-driven 4D board decomposition.
204. `DONE` `[BKL-P1-001]` 4D `xw`/`zw` basis-driven board decomposition fix:
205. renderer now derives layer axis/count and board dims from signed-axis view basis,
206. and routes grid/cells/helper/clear-animation through one shared 4D->(layer,cell3) map in `tetris_nd/front4d_render.py`.
207. Added regression coverage in `tetris_nd/tests/test_front4d_render.py` for:
208. `(5,4,3,2)` + `xw` => `5` boards of `(2,4,3)`,
209. `(5,4,3,2)` + `zw` => `3` boards of `(5,4,2)`,
210. and 4D coord-map bijection.
211. `DONE` `[BKL-P1-002]` 4D post-basis regression cleanup:
212. exploration-mode rotation tween rendering restored (fractional overlay coordinates preserved),
213. `move_w` intent now maps to current basis layer axis (`w`/`x`/`z` by view),
214. compact profile 4D `w` movement defaults changed from `,/.` to `N`/`/`,
215. `macbook` built-in profile added with no-function 4D view defaults (`1/2/3/4`) and help=`Tab`,
216. 4D layer-region clear hardening added for layer-count reductions.
217. validation coverage added in:
218. `tetris_nd/tests/test_front4d_render.py`,
219. `tetris_nd/tests/test_nd_routing.py`,
220. `tetris_nd/tests/test_keybindings.py`,
221. and full local gates passed.
222. `DONE` `[BKL-P1-003]` Keybinding consistency update:
223. 4D camera `view_xw/view_zw` defaults now use number pairs (`1/2`,`3/4`) across shipped profiles,
224. `macbook` 4D `move_w` defaults now use `,/.`,
225. `full` profile keeps `move_w` on keypad (`Numpad7/Numpad9`) and now uses the same 4D letter-pair rotation ladder as compact profile to avoid camera/view collisions,
226. 2D positive rotation keeps `Up` arrow as default alongside `Q`.
227. `DONE` `[BKL-P1-004]` Remove slicing across runtime/UI/docs:
228. ND routing no longer carries slice state or slice actions; 3D/4D input routing is now system -> gameplay -> view.
229. 3D/4D keybinding groups and helper panels are now `game/camera/system` only.
230. 4D HUD/panel no longer shows active-slice indicators or active-layer slice highlighting.
231. `DONE` `[BKL-P2-008]` No-slice keybinding UX regroup + cleanup:
232. keybinding editor/help now present gameplay as `Translation` + `Rotation` sections, with `System` and `Camera/View` separate.
233. side-panel helpers now hide exploration-only translation rows unless exploration mode is enabled.
234. legacy profile `slice` groups were removed from shipped profile JSON files (`keybindings/profiles/*/{3d,4d}.json`).
235. dead no-op compatibility code was removed from `tetris_nd/keybindings.py` (unused `_merge_bindings` and unreachable `len(groups)==1` load branch).
236. `DONE` `[BKL-P2-009]` Menu-structure redesign follow-up:
237. pause `Settings` now routes to the shared launcher settings hub (`Audio`,`Display`,`Analytics`,`Save`,`Reset`,`Back`) instead of a separate pause-only implementation.
238. obsolete `pause_settings_rows` config/runtime paths were removed from `config/menu/structure.json` and `tetris_nd/menu_config.py`.
239. pause settings summary text now matches shared scope: `Audio + Display + Analytics`.
240. `DONE` `[BKL-P2-010]` Launcher settings rows are now config-driven:
241. unified settings row layout moved to `config/menu/structure.json` (`settings_hub_layout_rows`).
242. `tetris_nd/menu_config.py` now validates and serves typed settings-hub layout rows.
243. `tetris_nd/launcher_settings.py` now renders/selects settings rows from config instead of hardcoded `_UNIFIED_SETTINGS_ROWS`.
244. `DONE` `[BKL-P2-011]` Camera controls moved to numeric mappings:
245. 3D camera defaults now use top-row digits (`1-0`) for yaw/pitch/zoom/projection/reset.
246. 4D camera defaults now use top-row digits for view/yaw/pitch/zoom and profile-specific advanced actions.
247. full-profile 4D exploration movement keys were remapped off conflicting keypad digits to keep numeric camera bindings conflict-free.
248. `DONE` `[BKL-P1-005]` macbook no-keypad camera fallback:
249. macbook advanced 4D camera defaults now avoid keypad dependency (`-`, `=`, `P`, `Backspace`).
250. updated runtime defaults, shipped macbook profile JSON, and keybinding tests for parity.
251. `DONE` `[BKL-P1-006]` menu rehaul v2 (core IA pass):
252. launcher top-level IA updated to `Play`,`Continue`,`Settings`,`Controls`,`Help`,`Bot`,`Quit`.
253. launcher `Play` now opens a mode picker (`2D`,`3D`,`4D`) and `Continue` launches the last-used mode setup directly.
254. pause menu was simplified to core actions (`Resume`,`Restart`,`Settings`,`Controls`,`Help`,`Bot`,`Back To Main Menu`,`Quit`).
255. controls entry now opens keybindings with `General` scope first in both launcher and pause.
256. `DONE` `[BKL-P2-012]` Validation/IO simplification follow-up:
257. keybinding save/load context resolution is now shared through `_resolve_keybindings_io_context` in `tetris_nd/keybindings.py`.
258. duplicated menu-config type guards were reduced through shared validators in `tetris_nd/menu_config.py`.
259. playbot test-only wrappers were removed from `tetris_nd/playbot/planner_nd.py`; tests now use `tetris_nd/playbot/planner_nd_core.py` directly.
260. obsolete compatibility shim `tetris_nd/menu_gif_guides.py` was removed; control-guide usage is unified on `tetris_nd/menu_control_guides.py`.
261. `DONE` `[BKL-P2-013]` Stage-2 dedup and boilerplate reduction:
262. shared string-list validation path added in `tetris_nd/menu_config.py` and wired into row/action/scope validators.
263. settings-category docs validation in `tetris_nd/menu_config.py` now reuses shared object/string validators.
264. keybinding profile-clone and dimension-loop handling in `tetris_nd/keybindings.py` now use shared helpers/constants.
265. repeated enum index/label boilerplate in `tetris_nd/playbot/types.py` now uses shared typed helpers.
266. keybinding legacy dual-path handling was removed by making `small` profile resolve directly to root `keybindings/{2d,3d,4d}.json` paths in `tetris_nd/keybindings.py`.
267. `DONE` `[BKL-P2-014]` Stage-3 dead-code and validator reduction:
268. removed unreferenced helpers from `tetris_nd/runtime_config.py` (`playbot_policy_payload`, `audio_sfx_payload`),
269. removed unreferenced `topology_mode_index` from `tetris_nd/topology.py`,
270. removed unreferenced `reset_topology_designer_cache` from `tetris_nd/topology_designer.py`,
271. further reduced validator duplication in `tetris_nd/menu_config.py` by reusing shared object/int/bool/string guards in launcher/menu/setup/split-rules paths.
272. `DONE` `[BKL-P2-015]` Stage-4 launcher/tooling simplification:
273. duplicated 2D/3D/4D launch flow in `tetris_nd/launcher_play.py` is now routed through one shared `_launch_mode_flow` pipeline with shared bot-kwargs and window-size helpers.
274. playbot benchmark wrapper indirection was removed from `tetris_nd/playbot/types.py`.
275. benchmark/policy tools now read thresholds/history paths directly from runtime config in:
276. `tools/bench_playbot.py`,
277. `tools/analyze_playbot_policies.py`.
278. `DONE` `[BKL-P2-016]` Stage-5 runtime-config dedup cleanup:
279. removed unused `STATE_DIR` constant/import path from `tetris_nd/runtime_config.py`,
280. shared bucket/key helpers now reduce repeated dimension-bucket lookup boilerplate in runtime-config accessors,
281. speed-curve and assist-factor lookups now reuse shared normalization helpers in `tetris_nd/runtime_config.py`.
282. `DONE` `[BKL-P2-017]` External transform icon-pack integration:
283. external SVG icon pack was normalized under `assets/help/icons/transform/svg`.
284. runtime action-to-icon mapping config was added in `config/help/icon_map.json`.
285. `tetris_nd/control_icons.py` now resolves icons from SVG assets first, with procedural fallback retained for missing actions (including drop actions).
286. help asset contracts/docs were updated (`assets/help/manifest.json`, `docs/help/HELP_INDEX.md`, `docs/PROJECT_STRUCTURE.md`, and canonical-maintenance rules).
287. `DONE` `[BKL-P2-018]` Desktop packaging baseline (embedded runtime):
288. added canonical packaging spec `packaging/pyinstaller/tet4d.spec`,
289. added OS build scripts `packaging/scripts/build_{macos,linux}.sh` and `packaging/scripts/build_windows.ps1`,
290. added packaging CI matrix workflow `.github/workflows/release-packaging.yml`,
291. added release packaging docs `docs/RELEASE_INSTALLERS.md` and packaging RDS `docs/rds/RDS_PACKAGING.md`,
292. synced `README.md`, `docs/RELEASE_CHECKLIST.md`, `docs/PROJECT_STRUCTURE.md`, and canonical-maintenance contract for packaging artifacts.
293. `DONE` `[BKL-P2-019]` Font profile unification with per-mode values:
294. added shared font model/factory module `tetris_nd/font_profiles.py`,
295. removed duplicated `GfxFonts` + `init_fonts()` implementations in:
296. `tetris_nd/gfx_game.py`,
297. `tetris_nd/frontend_nd.py`,
298. `tetris_nd/front3d_render.py`,
299. preserved profile-specific sizing (`2d` panel font `18`, `nd` panel font `17`) through wrapper-based profile routing.
300. `DONE` `[BKL-P2-020]` Repository hygiene cleanup + history purge:
301. removed tracked IDE/log/legacy-asset artifacts (`.idea`, `app.log`, legacy GIF guides, duplicate source icon pack),
302. expanded ignore policy to prevent reintroduction of local/non-source files,
303. synced help/structure docs and RDS cleanup policy wording,
304. executed full-history purge of removed artifacts across refs and followed with force-push + secret scan sweep.

## 3. Active Open Backlog / TODO (Unified RDS Gaps + Technical Debt)

1. `[P3][BKL-P3-001] Pre-push local CI gate`
2. `Cadence:` before every push/release.
3. `Trigger:` any code/docs/config change on active branch.
4. `Done criteria:` latest `scripts/ci_check.sh` run exits `0` with no unresolved failures.
5. `[P3][BKL-P3-002] Scheduled stability + policy workflow watch`
6. `Cadence:` at least weekly and after workflow/config changes.
7. `Trigger:` `.github/workflows/ci.yml`, `.github/workflows/stability-watch.yml`, `tools/check_playbot_stability.py`, or `tools/analyze_playbot_policies.py` changes.
8. `Done criteria:` scheduled workflow runs are green and no unresolved stability/policy alerts remain.
9. `[P3][BKL-P3-003] Runtime-config validation module split watch`
10. `Cadence:` when adding new policy sections.
11. `Trigger:` growth in `tetris_nd/runtime_config_validation_playbot.py` beyond current maintainable scope.
12. `Done criteria:` split completed with unchanged behavior and passing lint/tests.
13. `[P3][BKL-P3-004] 3D renderer decomposition watch`
14. `Cadence:` when adding new rendering responsibilities.
15. `Trigger:` major feature growth in `tetris_nd/front3d_render.py`.
16. `Done criteria:` render responsibilities are split into focused modules with behavior parity and passing regression tests.
17. `[P3][BKL-P3-005] Projection/cache profiling watch`
18. `Cadence:` after projection/camera/cache changes and before release.
19. `Trigger:` edits to projection/cache/zoom paths (3D/4D render stack).
20. `Done criteria:` `tools/profile_4d_render.py` report recorded; deeper caching is only added when measured overhead justifies it.
21. `[P3][BKL-P3-006] Desktop release hardening watch`
22. `Cadence:` before each public release.
23. `Trigger:` edits in `packaging/`, `.github/workflows/release-packaging.yml`, or `docs/RELEASE_INSTALLERS.md`.
24. `Done criteria:` package matrix artifacts are green and signing/notarization follow-up status is explicitly tracked in release notes.
25. `[P3][BKL-P3-007] Repository hygiene watch (history + secret scan)`
26. `Cadence:` before each push/release and after any cleanup of sensitive/non-source files.
27. `Trigger:` accidental commit of local artifacts, suspected secret exposure, or path-sanitization policy changes.
28. `Done criteria:` targeted paths are removed from tracked tree and git history when needed, `python3 tools/scan_secrets.py` passes, and cleanup is documented in changelog/backlog.
## 4. Gap Mapping to RDS

1. `docs/rds/RDS_TETRIS_GENERAL.md`: CI/stability workflows and setup-menu dedup follow-up (`BKL-P2-007`) are closed.
2. `docs/rds/RDS_PLAYBOT.md`: periodic retuning is now operationalized through scheduled benchmark + policy-analysis workflow.
3. `docs/rds/RDS_MENU_STRUCTURE.md`: `BKL-P2-006` is closed; launcher/pause/help IA parity and compact hardening are complete.
4. `docs/rds/RDS_2D_TETRIS.md` / `docs/rds/RDS_3D_TETRIS.md` / `docs/rds/RDS_4D_TETRIS.md`: topology preset + advanced profile behavior must remain in sync with setup + engine logic.

## 5. Change Footprint (Current Batch)

1. Key implementation/doc files updated include:
`front2d.py`,
`tetris_nd/front3d_game.py`,
`tetris_nd/front4d_game.py`,
`tetris_nd/front4d_render.py`,
`tetris_nd/gfx_game.py`,
`tetris_nd/control_helper.py`,
`tetris_nd/game2d.py`,
`tetris_nd/game_nd.py`,
`tetris_nd/playbot/dry_run.py`,
`tetris_nd/tests/test_playbot.py`,
`tetris_nd/tests/test_score_analyzer.py`,
`.github/workflows/ci.yml`,
`scripts/ci_check.sh`,
`tools/check_playbot_stability.py`,
`docs/rds/RDS_SCORE_ANALYZER.md`,
`docs/FEATURE_MAP.md`,
`README.md`,
`config/project/canonical_maintenance.json`,
`tools/validate_project_contracts.py`,
`tetris_nd/tests/test_project_contracts.py`,
`config/schema/menu_settings.schema.json`,
`config/schema/save_state.schema.json`,
`docs/migrations/menu_settings.md`,
`docs/migrations/save_state.md`,
`tests/replay/manifest.json`,
`docs/help/HELP_INDEX.md`,
`assets/help/manifest.json`,
`docs/RELEASE_CHECKLIST.md`.
`tetris_nd/help_menu.py`,
`tetris_nd/control_helper.py`,
`config/menu/structure.json`.
2. New split modules/helpers introduced:
`tetris_nd/panel_utils.py`,
`tetris_nd/loop_runner_nd.py`,
`tetris_nd/front3d_setup.py`,
`tetris_nd/front4d_render.py`,
`tetris_nd/launcher_play.py`,
`tetris_nd/launcher_settings.py`,
`tetris_nd/ui_utils.py`,
`tetris_nd/keybindings_menu_view.py`,
`tetris_nd/keybindings_menu_input.py`,
`tetris_nd/launcher_nd_runner.py`,
`tetris_nd/playbot/lookahead_common.py`.
3. Offline/stability analysis tooling added:
`tools/analyze_playbot_policies.py`.
`tools/check_playbot_stability.py`.
4. Runtime policy retuned:
`config/playbot/policy.json` (reduced default budgets + tightened benchmark thresholds).
5. New score-analyzer defaults and telemetry hooks added:
`config/gameplay/score_analyzer.json`,
`tetris_nd/score_analyzer.py`.
6. Gap-closure batch additions:
`tetris_nd/key_display.py`,
`tetris_nd/keybindings_menu_model.py`,
`tetris_nd/menu_control_guides.py`,
`tetris_nd/tests/test_menu_policy.py`,
`.github/workflows/stability-watch.yml`.
7. Toolchain/contract hardening additions:
`scripts/bootstrap_env.sh`,
`scripts/ci_check.sh`,
`tools/validate_project_contracts.py`,
`config/project/canonical_maintenance.json`,
`README.md`,
`docs/GUIDELINES_RESEARCH.md`,
`docs/RDS_AND_CODEX.md`,
`docs/rds/RDS_TETRIS_GENERAL.md`.
8. Control-helper optimization additions:
`tetris_nd/control_icons.py`,
`tetris_nd/control_helper.py`,
`tetris_nd/tests/test_control_ui_helpers.py`.
9. Follow-up simplification additions (current batch):
`tetris_nd/game_loop_common.py`,
`front2d.py`,
`tetris_nd/loop_runner_nd.py`,
`tetris_nd/runtime_config_validation.py`,
`tetris_nd/front3d_game.py`,
`tetris_nd/front4d_render.py`,
`tetris_nd/gfx_game.py`,
`tetris_nd/gfx_panel_2d.py`,
`tetris_nd/grid_mode_render.py`,
`tetris_nd/keybindings_defaults.py`,
`tetris_nd/keybindings_catalog.py`,
`tetris_nd/keybindings.py`,
`tetris_nd/score_analyzer_features.py`,
`tetris_nd/score_analyzer.py`.
10. Next-stage decomposition + optimization additions:
`tetris_nd/front3d_render.py`,
`tetris_nd/front3d_game.py`,
`tetris_nd/runtime_config_validation.py`,
`tetris_nd/runtime_config_validation_shared.py`,
`tetris_nd/runtime_config_validation_gameplay.py`,
`tetris_nd/runtime_config_validation_playbot.py`,
`tetris_nd/runtime_config_validation_audio.py`,
`tetris_nd/ui_utils.py`,
`tetris_nd/panel_utils.py`,
`tetris_nd/gfx_panel_2d.py`.
11. Further runtime optimization additions:
`tetris_nd/text_render_cache.py`,
`tetris_nd/control_helper.py`,
`tetris_nd/panel_utils.py`,
`tetris_nd/gfx_panel_2d.py`,
`tetris_nd/front4d_render.py`.
12. Security/config hardening + path/constants externalization additions:
`tetris_nd/project_config.py`,
`config/project/io_paths.json`,
`config/project/constants.json`,
`config/project/secret_scan.json`,
`tools/scan_secrets.py`,
`scripts/ci_check.sh`,
`tetris_nd/runtime_config.py`,
`tetris_nd/menu_settings_state.py`,
`tetris_nd/keybindings.py`,
`tetris_nd/score_analyzer.py`,
`tetris_nd/projection3d.py`,
`tetris_nd/front3d_render.py`,
`tetris_nd/front4d_render.py`,
`README.md`,
`docs/SECURITY_AND_CONFIG_PLAN.md`.
13. Advanced topology-designer additions:
`config/topology/designer_presets.json`,
`tetris_nd/topology.py`,
`tetris_nd/topology_designer.py`,
`front2d.py`,
`tetris_nd/front3d_setup.py`,
`tetris_nd/frontend_nd.py`,
`tetris_nd/game2d.py`,
`tetris_nd/game_nd.py`,
`config/menu/defaults.json`,
`config/menu/structure.json`,
`config/schema/menu_settings.schema.json`,
`tetris_nd/tests/test_topology_designer.py`.
14. Latest simplification follow-up touched:
`tetris_nd/menu_config.py`,
`tetris_nd/keybindings.py`,
`tetris_nd/playbot/planner_2d.py`,
`tetris_nd/playbot/planner_nd.py`,
`tetris_nd/tests/test_playbot.py`,
`tetris_nd/menu_control_guides.py` (canonical guide module retained),
`tetris_nd/menu_gif_guides.py` (removed).
15. Stage-2 simplification follow-up touched:
`tetris_nd/menu_config.py`,
`tetris_nd/keybindings.py`,
`tetris_nd/playbot/types.py`.
16. Stage-3 simplification follow-up touched:
`tetris_nd/menu_config.py`,
`tetris_nd/runtime_config.py`,
`tetris_nd/topology.py`,
`tetris_nd/topology_designer.py`.
17. Stage-4 simplification follow-up touched:
`tetris_nd/launcher_play.py`,
`tetris_nd/playbot/types.py`,
`tools/bench_playbot.py`,
`tools/analyze_playbot_policies.py`.
18. Stage-5 simplification follow-up touched:
`tetris_nd/runtime_config.py`.
19. Stage-6 icon-pack integration touched:
`assets/help/icons/transform/svg/*`,
`config/help/icon_map.json`,
`assets/help/manifest.json`,
`tetris_nd/control_icons.py`,
`config/project/canonical_maintenance.json`,
`docs/help/HELP_INDEX.md`,
`docs/PROJECT_STRUCTURE.md`.
20. Desktop packaging baseline touched:
`.github/workflows/release-packaging.yml`,
`packaging/pyinstaller/tet4d.spec`,
`packaging/scripts/build_macos.sh`,
`packaging/scripts/build_linux.sh`,
`packaging/scripts/build_windows.ps1`,
`docs/RELEASE_INSTALLERS.md`,
`docs/rds/RDS_PACKAGING.md`,
`README.md`,
`docs/RELEASE_CHECKLIST.md`,
`config/project/canonical_maintenance.json`.
21. Font profile unification touched:
`tetris_nd/font_profiles.py`,
`tetris_nd/gfx_game.py`,
`tetris_nd/frontend_nd.py`,
`tetris_nd/front3d_render.py`,
`front.py`,
`docs/rds/RDS_TETRIS_GENERAL.md`,
`docs/plans/PLAN_FONT_PROFILE_UNIFICATION_2026-02-20.md`.

## 6. Source Inputs

1. `docs/rds/RDS_TETRIS_GENERAL.md`
2. `docs/rds/RDS_PLAYBOT.md`
3. `docs/rds/RDS_MENU_STRUCTURE.md`
4. `docs/RDS_AND_CODEX.md`
5. `config/project/canonical_maintenance.json`
6. Consolidated implementation diffs in current workspace batch.

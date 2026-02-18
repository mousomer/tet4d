# Score Analyzer RDS (All Gameplay)

Status: Active v0.3 (Phase-2 implemented, Verified 2026-02-18)
Author: Omer + Codex
Date: 2026-02-18
Target Runtime: Python 3.11-3.14 + `pygame-ce`

## 1. Purpose

Define a shared score-analysis model for 2D/3D/4D gameplay that:
1. measures board quality and placement quality on every piece lock,
2. works for all actor modes (human, assist, auto, step),
3. produces deterministic telemetry for tuning and replay analysis.

## 2. Canonical documentation location

This is the canonical design document for score-analyzer semantics.
1. RDS files define behavior contracts and schema intent.
2. README should only summarize usage-level behavior.
3. Feature-map docs should summarize shipped behavior, not replace schema/design.

## 3. Scope

In scope:
1. Feature vector definitions and normalization rules.
2. Split between board-health metrics and placement metrics.
3. Event protocol for analyzer updates.
4. Storage locations for config and runtime telemetry.
5. Retuning workflow inputs/outputs.

Out of scope:
1. Replacing core score rules (`lock points + clear points`) immediately.
2. ML/RL policy training.
3. Network telemetry upload.

## 4. Feature-vector model

Feature vectors are computed on every lock event:
1. `board_pre`: board-health features before lock.
2. `placement`: placement-quality features for the locked piece.
3. `board_post`: board-health features after lock.
4. `delta`:`board_post - board_pre` for selected dimensions.

All non-count metrics must be normalized to board size so values are comparable across 2D/3D/4D.

## 5. Board-health feature group

Board-health features describe global board state after lock.

Required fields:
1. `occupied_ratio`:`locked_cells / total_cells`.
2. `max_height_norm`: max column height along gravity, normalized to gravity-axis size.
3. `mean_height_norm`: mean column height, normalized.
4. `surface_roughness_norm`: neighbor height variation on non-gravity axes.
5. `holes_count_norm`: empty cells with at least one locked cell above on gravity axis, normalized by total cells.
6. `holes_depth_norm`: depth-weighted hole burden, normalized.
7. `cavity_volume_norm`: enclosed empty volume burden, normalized.
8. `near_complete_planes_norm`: almost-full clearable planes ratio.
9. `clearable_planes_norm`: fully clear planes ratio.
10. `top_zone_risk_norm`: occupancy ratio in top spawn-risk layers.
11. `fragmentation_norm`: disconnected locked-mass component count normalized to board scale.
12. `slice_balance_norm`(4D): occupancy distribution balance across`w` layers.

## 6. Placement feature group

Placement features describe quality of the just-locked piece position.

Required fields:
1. `drop_distance_norm`: lock distance traveled along gravity.
2. `landing_coords_norm`: normalized landing coordinates on non-gravity axes.
3. `support_contacts_norm`: piece cells supported from below.
4. `side_contacts_norm`: lateral contact with locked structure.
5. `overhang_cells_norm`: unsupported-overhang burden introduced by placement.
6. `immediate_clears_norm`: normalized clear count from this lock.
7. `clear_contribution_norm`: fraction of placed cells that participated in clear.
8. `near_complete_progress_norm`: progress added toward nearly complete planes.
9. `holes_created_norm`: newly created hole burden.
10. `holes_filled_norm`: previously existing holes now filled/sealed.
11. `cavity_delta_norm`: enclosed-volume delta caused by placement.
12. `roughness_delta_norm`: surface roughness delta caused by placement.
13. `top_risk_delta_norm`: top-zone risk delta caused by placement.

## 7. Derived analyzer scores

Two explicit analyzer scores are produced:
1. `board_health_score`: weighted aggregate from`board_post` features.
2. `placement_quality_score`: weighted aggregate from`placement`and selected`delta` features.

Design rules:
1. Score ranges should be stable (recommended `0.0..1.0` after clamping).
2. Weights are externalized in config, never hardcoded.
3. Core gameplay score remains authoritative unless explicitly changed in a separate RDS update.

## 8. Actor coverage

Analyzer must run for every gameplay mode:
1. `human` (no bot),
2. `assist`,
3. `auto`,
4. `step`.

Each analyzer event must include `actor_mode` and current assist/grid/speed modifiers for segmented analysis.

## 9. Event/update protocol

Current persisted event stream:
1. `piece_lock_analyzed` (repeats on every lock event).
2. Session boundary events (`session_start`/`session_end`) are reserved for future expansion and are not required for current telemetry files.

Required fields for `piece_lock_analyzed`:
1. `schema_version`
2. `session_id`
3. `seq`
4. `timestamp_utc`
5. `dimension`
6. `board_dims`
7. `piece_id`
8. `actor_mode`
9. `bot_mode`
10. `grid_mode`
11. `speed_level`
12. `raw_points`
13. `final_points`
14. `cleared`
15. `board_pre`
16. `placement`
17. `board_post`
18. `delta`
19. `board_health_score`
20. `placement_quality_score`

## 10. Storage and config locations

Canonical files:
1. `config/gameplay/score_analyzer.json`
2. `state/analytics/score_events.jsonl`
3. `state/analytics/score_summary.json` Rules:
1. `config/*` files are source-controlled defaults.
2. `state/*` files are runtime/user/generated outputs.
3. Schema versioning is mandatory for event compatibility.
4. Runtime logging is controlled by both config and user settings:
5. config default: `config/gameplay/score_analyzer.json -> logging.enabled`,
6. user override: `state/menu_settings.json -> analytics.score_logging_enabled`.

## 11. Retuning workflow

After major gameplay/planner/piece-set changes:
1. collect trend data from regular gameplay and bot gameplay,
2. segment by dimension and actor mode,
3. compare score-analyzer distributions and clear/survival outcomes,
4. tune weights and bounds in `config/gameplay/score_analyzer.json`,
5. keep benchmark latency within existing playbot policy thresholds.

## 12. UI update protocol

Recommended runtime UI fields:
1. `Quality`= placement-quality score.
2. `Board health`= board-health score.
3. `Trend`= short arrow/mini state (`up`,`flat`,`down`) from recent moving average.

Visibility rules:
1. Compact summary in side panel by default.
2. Detailed analyzer breakdown only in optional help/debug overlay.
3. Launcher `Settings -> Analytics` exposes score-logging toggle and persistence.

## 13. Testing requirements

Minimum tests:
1. deterministic feature extraction for fixed board snapshots,
2. invariant checks (`0..1` clamped normalized fields),
3. no missing required event fields in emitted JSONL entries,
4. mode coverage tests for human/assist/auto/step,
5. cross-dimension smoke tests (2D/3D/4D).
6. summary protocol validation for persisted `score_summary.json`.
7. logging-on path writes both event JSONL and summary JSON files.

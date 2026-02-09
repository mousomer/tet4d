# Tetris Family RDS (General)

Status: Draft v0.1  
Author: Omer + Codex  
Date: 2026-02-08  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Purpose

Define shared requirements for the Tetris family in this repository:

1. 2D Tetris
2. 3D Tetris
3. 4D Tetris

Mode-specific behavior is detailed in:

1. `RDS_2D_TETRIS.md`
2. `RDS_3D_TETRIS.md`
3. `RDS_4D_TETRIS.md`

## 2. Shared Product Goals

1. Deliver playable, deterministic Tetris variants.
2. Reuse a common ND engine where practical.
3. Keep controls discoverable and keyboard-first.
4. Make each mode independently testable and runnable.

## 3. Shared Non-Goals (MVP)

1. Multiplayer/online modes.
2. Full modern guideline parity (advanced spin/kick edge-cases).
3. GPU/OpenGL renderer requirement.
4. Mobile/touch-first UX.

## 4. Coordinate and Axis Conventions

1. Axis 0: `x` (left/right).
2. Axis 1: `y` (gravity direction, increases downward).
3. Axis 2: `z` (depth; used in 3D/4D).
4. Axis 3: `w` (fourth spatial axis; used in 4D).
5. Gravity always acts on axis `y` in MVP.

## 5. Mode Matrix

1. 2D mode:
2. Dims: `(x, y)`
3. Clear rule: full `x` row at fixed `y`
4. 3D mode:
5. Dims: `(x, y, z)`
6. Clear rule: full `x-z` layer at fixed `y`
7. 4D mode:
8. Dims: `(x, y, z, w)`
9. Clear rule: full `x-z-w` hyperlayer at fixed `y`

## 6. Shared Engine Requirements

1. Sparse occupancy board representation (`coord -> cell_id`).
2. Deterministic piece bag with seedable RNG.
3. Fixed-timestep gravity (independent from frame-rate).
4. Piece lifecycle:
5. Spawn -> move/rotate -> lock -> clear -> spawn next.
6. `y < 0` allowed pre-lock; lock above top triggers game-over.
7. Score, lines/layers cleared, and game-over state tracked in game state.

## 7. Shared UX Requirements

1. Setup menu before gameplay.
2. In-game HUD:
3. Score
4. Cleared lines/layers
5. Speed level
6. Controls summary
7. Core session controls:
8. Restart
9. Return to menu
10. Quit

## 8. Shared Technical Requirements

1. Runtime dependency file must specify `pygame-ce`.
2. Code imports use `import pygame` (module name remains `pygame`).
3. Python 3.14 compatibility required for logic and frontends.

## 9. Quality and Performance Targets

1. Target: 60 FPS on default board sizes.
2. No unbounded growth structures in the main loop.
3. Must degrade gracefully when window is resized.

## 10. Testing Requirements

1. Unit tests for movement, rotation, collision, lock, clear.
2. Deterministic replay test path for at least one scripted sequence.
3. Smoke test for each mode entry point.
4. Python 3.14 compatibility checks:
5. `py_compile` on all Python files
6. mode test suite pass

## 11. Milestone Framework

1. M0: engine primitives + rules per mode.
2. M1: playable frontend per mode.
3. M2: balancing + UX polish.
4. M3: packaging/docs and release hardening.

## 12. Acceptance Criteria (Family)

1. 2D, 3D, and 4D modes each run from their entry script.
2. Each mode can be played from start to game-over without crashes.
3. Clear/scoring logic matches each mode-specific RDS.
4. Python 3.14 checks pass.

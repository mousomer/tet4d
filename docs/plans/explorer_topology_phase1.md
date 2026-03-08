# Explorer Topology Phase 1

Status date: 2026-03-08

## Goal

Add an engine-owned general explorer-topology kernel based on boundary gluings and
signed-permutation tangent transforms, without switching the live runtime or UI
behavior yet.

## Canonical owner

- `src/tet4d/engine/topology_explorer/`

## Scope in this phase

1. boundary descriptors
2. signed-permutation transform model
3. explorer gluing profile model
4. engine-owned validation
5. discrete move-through-boundary mapping
6. compiled movement graph helpers
7. engine-owned basic presets for tests/examples

## Explicit non-goals in this phase

1. no runtime switch from the existing explorer topology system
2. no topology-lab UI rewrite yet
3. no save/load schema change yet
4. no normal-game topology change
5. no falling-piece integrity contract over general quotient gluings

## Acceptance

1. `src/tet4d/engine/topology_explorer/` exists and is pure engine code.
2. Signed-permutation transforms are validated and invertible.
3. Boundary gluings are validated for unique ownership and discrete bijection.
4. Per-cell boundary crossing can be mapped through a gluing.
5. Movement graphs can be built from the explorer topology profile.
6. Focused unit tests cover transform inversion, bijection failure, torus-like wrap,
   twisted wrap, and graph compilation.
7. No live gameplay/UI behavior changes in this phase.

# Cleanup Master Plan

Role: ledger
Status: active
Source of truth: this file for broad structural cleanup sequencing
Supersedes: none
Last updated: 2026-03-22

## Purpose

Track the remaining structural cleanup program for the live codebase.

Code is the source of truth.
Docs and manifests are synchronized after code changes land.

This file is not the topology-playground architecture authority and is not the
visible-shell spec.

## Structural work rule

Unless a stage explicitly authorizes semantic change, cleanup work in this
ledger must not change gameplay, replay, tutorial, scoring, packaging, or
accepted product behavior.

Structural work means:

1. identify a canonical owner
2. migrate callers
3. add or preserve equivalence coverage
4. delete duplicates
5. sync docs/manifests after code is correct

## Scope boundary

This ledger owns broad cleanup sequencing across the repo.
It does not own:

- topology-playground architecture precedence
- topology-playground visible-shell contract
- launcher/menu IA wording
- batch history

## Active cleanup domains

| Domain | Canonical owner | Status | Exit condition |
| --- | --- | --- | --- |
| Gameplay orchestration dedup | `engine/core/rules/lifecycle.py`, `engine/gameplay/lock_flow.py` | active | duplicated lock/drop orchestration in mode files is reduced as far as net deletion justifies |
| Runtime/settings ownership cleanup | `engine/runtime/menu_settings_state.py` facade over runtime submodules | active | facade pressure stays bounded or is narrowed further by real seam extraction |
| Launcher/bootstrap drift watch | `front.py` compatibility wrapper plus `cli/front*.py` | watch | no material duplication returns |
| Packaging/release drift watch | packaging scripts/workflows | watch | installer and release authority remain coherent |
| Explorer topology engine cleanup | `engine/topology_explorer/` plus runtime store/preview/runtime owners | active | legacy bridge is removable without breaking explicit compatibility paths |
| Docs/manifests sync discipline | code first, then state/backlog/generated docs/relevant RDS | active | drift checks remain green and narrative duplication is reduced |

## Explorer topology engine note

The explorer topology engine now has an established canonical owner set:

- pure gluing semantics in `src/tet4d/engine/topology_explorer/`
- runtime-owned storage/preview/integration in the runtime explorer modules
- graphical explorer scene under `src/tet4d/ui/pygame/topology_lab/`

Remaining cleanup is limited to:

- final compatibility-bridge deletion when justified,
- narrower supporting-editor cleanup,
- avoiding reintroduction of legacy edge-rule ownership.

## Watch items

These are not active redesign programs, but they still need drift monitoring:

- launcher/bootstrap thin-wrapper discipline
- packaging/release authority discipline
- readability drift in operational code
- doc/manifold duplication returning after future batches

## Completion rule

A cleanup item is complete only when:

- canonical owner is explicit,
- duplicate behavior has been removed or reduced,
- focused equivalence coverage exists,
- lower-precedence docs are synchronized,
- no historical or compatibility layer silently retains live authority.

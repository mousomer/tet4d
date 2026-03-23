# Plans Directory Guide

`docs/plans/` contains the active planning layer for the repo.

Use this directory for documents that still shape current work.
Do not use it as a dumping ground for completed batch notes, historical
manifests, or implementation archaeology.

## File header contract

Every file in `docs/plans/` should begin with these fields:

- `Role:` `authority` | `spec` | `ledger` | `reference`
- `Status:` `active` | `frozen` | `reference`
- `Source of truth:` `<path>` or `none`
- `Supersedes:` `<path list>` or `none`

Meaning:

- `authority`: accepted architecture, precedence, invariants, and non-goals.
- `spec`: a frozen or semi-frozen contract for one current workstream.
- `ledger`: active cleanup/debt/status tracking for unfinished work.
- `reference`: useful background that may inform active work but does not
  control execution.

## General planning layer

General planning/routing files are not topology-playground-specific.

- `plan_authority_map.md`
- `cleanup_master_plan.md`

These files exist so topology-playground-specific files do not have to carry
general planning redirection or repo-wide ownership notes.

## Domain-specific active files

### `topology_playground_current_authority.md`
- Role: `authority`
- Status: `active`
- Owns:
  - current topology-playground architecture
  - instruction precedence
  - accepted workspace model
  - ownership boundaries
  - invariants
  - explicit non-goals
  - mandatory execution rules

### `topology_playground_shell_redesign_spec.md`
- Role: `spec`
- Status: `frozen`
- Owns:
  - launcher first-layer contract for the current shell pass
  - topology-playground visible shell layout
  - visible wording contract
  - diagnostics demotion rules
  - shell acceptance checklist

### `topology_playground_debt_register.md`
- Role: `ledger`
- Status: `active`
- Owns:
  - transitional compatibility debt
  - deferred decomposition targets
  - unresolved cleanup seams
  - active follow-up debt for the playground path

## Ownership map

The canonical ownership matrix lives in `plan_authority_map.md`.

If two files appear to own the same rule, the docs are wrong and must be
normalized.

## Reference files

Reference files may remain in `docs/plans/` only if they still provide useful
background for active work and are explicitly labeled as `Role: reference`.

Current reference files:

- `piece_transform_extraction.md`
- `piece_transform_inventory.md`

Reference files do not control execution when they conflict with an active
authority/spec document.

## Retirement rule

Move a file out of `docs/plans/` and into history when any of the following
becomes true:

1. the file describes a completed one-off implementation pass,
2. the file no longer shapes current execution,
3. a newer authority/spec/ledger has replaced it,
4. keeping it in `docs/plans/` would create ambiguity about what is active.

Historical execution reports and retired one-off plans belong under:

- `docs/history/plans/`
- `docs/history/topology_playground/`

## Conflict rule

When documents disagree, precedence is:

1. newer task instruction
2. owning active `authority` document
3. owning active or frozen `spec` document
4. active `ledger` documents
5. `reference` documents
6. historical documents

If a lower-precedence file conflicts with a higher-precedence file, update or
move the lower-precedence file in the same batch.

## Directory policy

`docs/plans/` should stay small.

A file belongs here only if it is one of:

- current authority,
- current frozen spec,
- active debt/cleanup ledger,
- explicitly retained reference.

Everything else belongs in history.

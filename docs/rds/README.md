# RDS Directory Guide

`docs/rds/` contains durable product and behavior contracts.

An RDS file should define stable requirements, behavior rules, storage/schema
contracts, or acceptance criteria for a product surface.

RDS files are not the place for:

- active batch logs,
- current migration diaries,
- completed implementation status ledgers,
- historical execution notes,
- temporary planning redirects.

Those belong in:

- `docs/plans/*`
- `CURRENT_STATE.md`
- `docs/BACKLOG.md`
- `docs/history/*`

## Required header

Every active RDS file should begin with these fields:

- `Role: rds`
- `Status: active`
- `Scope: <domain>`
- `Canonical owner: <module/package or this file>`
- `Last verified: YYYY-MM-DD`

## RDS families

### Core/shared product contracts

- `RDS_TETRIS_GENERAL.md`
- `RDS_MENU_STRUCTURE.md`
- `RDS_KEYBINDINGS.md`

### Feature/domain contracts

- `RDS_PLAYBOT.md`
- `RDS_SCORE_ANALYZER.md`
- `RDS_PACKAGING.md`

### Mode-specific gameplay contracts

- `RDS_2D_TETRIS.md`
- `RDS_3D_TETRIS.md`
- `RDS_4D_TETRIS.md`

### Non-core or external-design candidates

Files that are not clearly part of the shipped tet4d product contract should be
moved out of active `docs/rds/` or explicitly called out as reference/design
material.

Current candidate for that decision:

- `RDS_FILE_FETCH_LIBRARY.md`

## Ownership boundaries

### `RDS_TETRIS_GENERAL.md`
Owns shared gameplay, topology, transform, kick, and cross-mode technical or UX
contracts.
It must not become a topology-playground migration log.

### `RDS_MENU_STRUCTURE.md`
Owns durable launcher, pause, settings, and menu interaction rules.
It must not become an implementation-status ledger or active shell-redesign log.

### Mode RDS files
Own mode-specific gameplay rules.
They must stay aligned with the current launcher/topology ownership model
instead of preserving stale setup ownership assumptions.

## Conflict rule

When an RDS conflicts with an active domain planning authority/spec during an
in-flight migration, do not silently invent a third rule.

Instead:

1. identify the owner using `docs/DOCUMENTATION_MAP.md` and
   `docs/plans/plan_authority_map.md`,
2. update the stale lower-precedence file,
3. move historical or temporary content out of `docs/rds/` if needed.

## Directory policy

Keep `docs/rds/` focused.

If a file is primarily:
- active planning,
- contributor process,
- generated reference,
- or historical narrative,

it does not belong here.

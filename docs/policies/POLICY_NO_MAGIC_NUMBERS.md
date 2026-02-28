# Policy: No Magic Numbers

## Purpose

Keep behavior tunable, auditable, and consistent by externalizing meaningful
numeric thresholds and constants.

## Rule

Do not hardcode non-trivial numeric constants in Python logic when they can be
defined in canonical non-Python config and loaded through runtime config access.

## Scope

This policy applies to:
1. gameplay thresholds and scoring weights
2. UI limits, percentages, timing values, and sizing defaults
3. runtime validation bounds and budget gates
4. tool and governance thresholds that affect pass/fail behavior

## Approved Decision Order

Use this order:
1. existing canonical config values in `config/*`
2. existing runtime/config accessors
3. new canonical config key + accessor if no suitable value exists

## Allowed Inline Constants

Inline numeric literals are acceptable only for:
1. obvious identity/control values (`0`, `1`, `-1`) when self-explanatory
2. short-lived loop/index mechanics with clear local meaning
3. schema structure markers where externalization adds no value

## Exceptions

Custom inline constants are allowed only when documented:
1. externalizing would add disproportionate complexity
2. value is purely algorithmic and not a tunable product behavior
3. migration is intentionally staged and temporary

## Mandatory Documentation for Exceptions

When taking an exception, include:
1. header comment: `Magic Number Exception: ...`
2. why config externalization is not justified
3. migration plan if temporary
4. tests covering boundary behavior

## Review and Enforcement

1. PR review rejects unexplained behavioral numeric literals.
2. New tunable values must be added to canonical config assets.
3. Governance/contract docs must stay synchronized with new config keys.

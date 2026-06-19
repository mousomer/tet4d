# Technical Debt Policy

## Scope

This policy defines a reusable technical-debt accounting model.

It does not define project-specific authority, domain semantics, concrete debt
items, or project-specific remediation priorities.

## Debt record fields

| Field | Required | Meaning |
|---|---:|---|
| `id` | yes | Stable debt identifier |
| `category` | yes | Debt category |
| `location` | yes | File, directory, subsystem, or policy surface |
| `source` | yes | Why the debt exists |
| `classification` | yes | deliberate-prudent, deliberate-reckless, inadvertent-prudent, inadvertent-reckless |
| `severity` | yes | low, medium, high, critical |
| `remediation_minutes` | yes | Estimated cleanup time |
| `interest` | yes | Risk/cost of leaving it |
| `owner` | yes | Responsible subsystem/team/project area |
| `introduced_by` | yes | Commit/task/decision if known, or `unknown` |
| `repayment_trigger` | yes | Event that should cause cleanup |
| `status` | yes | open, accepted, mitigated, closed |
| `notes` | no | Extra context |

## Calculation

Open debt minutes:

```text
sum(remediation_minutes for items with status open or accepted)
```

Open debt days:

```text
open_debt_minutes / 480
```

Closed or mitigated items are excluded from open-debt totals.

The numbers are estimates for governance prioritization, not exact accounting.

## Suppressions and advisories

Suppressions, strict-mode failures, and advisory validator findings may become
debt records when they represent accepted risk or deferred cleanup.

## Classifications

Allowed classifications:

- deliberate-prudent
- deliberate-reckless
- inadvertent-prudent
- inadvertent-reckless

## Severity

Allowed severities:

- low
- medium
- high
- critical

## Status

Allowed statuses:

- open
- accepted
- mitigated
- closed

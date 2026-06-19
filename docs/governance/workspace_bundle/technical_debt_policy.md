# Technical Debt Policy

Debt records should include:

| Field | Meaning |
|---|---|
| `id` | Stable identifier |
| `category` | Debt category |
| `location` | File/subsystem |
| `source` | Why it exists |
| `classification` | deliberate-prudent, deliberate-reckless, inadvertent-prudent, inadvertent-reckless |
| `severity` | low, medium, high, critical |
| `remediation_minutes` | Estimated cleanup time |
| `interest` | Risk/cost of leaving it |
| `owner` | Subsystem or team |
| `introduced_by` | Commit/task/decision if known |
| `repayment_trigger` | When it should be fixed |
| `status` | open, accepted, mitigated, closed |

## Calculation

Open debt minutes:

```text
sum(remediation_minutes for open debt items)
```

Open debt days:

```text
open_debt_minutes / 480
```

Estimates are governance approximations, not exact accounting.

Suppressions and advisory validator findings may be recorded as debt candidates.

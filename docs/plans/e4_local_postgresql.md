# E4 local PostgreSQL slice

The [E4 contract](e4_assessment_storage_contract.md) defines the logical
records. `migration/participant_data/001_assessment.sql` implements them as
typed tables and PL/pgSQL entry points, described in the
[platform architecture](../architecture/participant_data_platform.md). It is
for a disposable database with synthetic data only. The game does not depend
on it.

Apply the migration as a role that can create roles and schemas. It creates
four NOLOGIN roles if they are missing (`assessment_owner`,
`assessment_ingest`, `assessment_operator`, `research_reader`) and builds every
object as `assessment_owner`. Provision synthetic manifest rows (protocol,
items, forms, protocol visits, arms and activities) as the database owner.
A deployment must supply verified authentication, login roles that are members
of the caller roles, and a reviewed host decision before exposing anything
remotely.

`tests/integration/e4_harness/` is the test-only edge adapter. `edge.ingest`
and the WSGI factory `edge.application(conninfo)` accept
`POST /v1/assessment/enrollments/{enrollment}/commands` with
`{"version":1,"commands":[...]}`. Trusted authentication middleware sets
`tet4d.verified_principal` to a verified UUID; headers and payload fields
cannot provide identity. `operations` wraps the trusted study calls.

| Kind | Other fields |
| --- | --- |
| `submit` | `slot`, `attempt`, four-coordinate `response`, `latency_ms`, nullable `observed_at` |
| `outcome` | `slot`, `status` (invalid, interrupted or unpresented), nullable `observed_at` |
| `exposure` | `activity`, `active_ms`, `examples` |

`observed_at` is null or exactly `YYYY-MM-DDTHH:MM:SS.sssZ`. Calibration
thresholds and scheduling windows remain protocol inputs.

## Running the integration suite

Use an **empty, disposable** database. The suite refuses a database that
already has the `assessment` schema and leaves its synthetic records behind.
Without `TET4D_E4_TEST_DSN` a normal test run skips it.

```sh
python -m pip install -r migration/participant_data/requirements.txt
TET4D_E4_TEST_DSN='<disposable PostgreSQL connection string>' python -m pytest tests/integration/test_e4_postgresql.py
```

# E4 local PostgreSQL slice

The [E4 contract](e4_assessment_storage_contract.md) defines the logical
records. This slice maps them to typed tables and a synchronous ingestion
service with a WSGI endpoint. It is for a disposable database with synthetic data. Apply
`migration/participant_data/001_assessment.sql` as the database owner.
Install `migration/participant_data/requirements.txt` for Psycopg and RFC
8785 canonical serialization. The game does not import these local service
dependencies.

The WSGI factory is `tet4d.participant_data.http.application(conninfo)`.
POST UTF-8 JSON to `/v1/assessment/enrollments/{enrollment}/commands`
with `{"version":1,"commands":[...]}`. Trusted authentication middleware
sets `tet4d.verified_principal` to a verified UUID in the WSGI environment.
Headers and payload fields cannot provide this identity. The service can
also be called directly via `tet4d.participant_data.ingestion.ingest`.
A command carries a canonical UUID `id` and one of these shapes.

| Kind | Other fields |
| --- | --- |
| `submit` | `slot`, `attempt`, four-coordinate `response`, `latency_ms`, nullable `observed_at` |
| `outcome` | `slot`, `status` (invalid, interrupted or unpresented), nullable `observed_at` |
| `exposure` | `activity`, `active_ms`, `examples` |

Use an ISO 8601 UTC timestamp ending in Z for known observations. Timing
classification uses the client-reported observation and remains distinct
from server receipt. A successful response carries each command ID, digest
and original durable receipt timestamp. Provision synthetic access and
immutable manifest rows through the database owner. A deployment must
supply verified authentication and restricted service grants before exposing
this entry point remotely. The client command envelope carries no principal
or account ID. Trusted callers own scheduling, eligibility, and the
randomization decision. PostgreSQL serializes writes, finalization and
revocation on the enrollment row. Receipt timestamps measure ingestion and
client UTC observations are declared separately from monotonic latency.
Calibration thresholds and scheduling windows remain protocol inputs.

Run integration tests against an **empty, disposable PostgreSQL database**
using `TET4D_E4_TEST_DSN` and the optional dependencies. The local test
role needs schema creation and permission to assume `pg_read_all_data`. The suite refuses a
database that already has an assessment schema and leaves its synthetic
records in the disposable database. A regular repository test run skips
these tests when no DSN is supplied.

Run the synthetic suite with:

```sh
python -m pip install -r migration/participant_data/requirements.txt
TET4D_E4_TEST_DSN='<disposable PostgreSQL connection string>'   python -m pytest tests/integration/test_e4_postgresql.py
```

# Delivered Data Model

PostgreSQL stores platform users, scans, and normalized control results. The gateway's simulated process state and audit log are intentionally in memory and return to a known state through `/demo/reset`.

## User

| Field | Purpose |
|---|---|
| `id` | Primary key |
| `email` | Unique login identifier |
| `hashed_password` | Bcrypt password representation |
| `is_active` | Account state |
| `created_at` | Creation timestamp |

## Scan

| Field | Purpose |
|---|---|
| `id` | Primary key |
| `user_id` | Owning user |
| `target_url` | Persisted target label resolved by the backend |
| `status` | `running`, `completed`, `partial`, or `failed` |
| `gateway_profile` | Observed `vulnerable` or `hardened` profile |
| `security_score` | Integer score from 0 to 100 |
| `request_count` | Actual requests consumed from the shared budget |
| `duration_ms` | End-to-end execution duration |
| `authorization_confirmed` | User confirmation captured at creation |
| `created_at` | Creation timestamp |
| `completed_at` | Finalization timestamp, when available |

## TestResult

| Field | Purpose |
|---|---|
| `id` | Primary key |
| `scan_id` | Parent scan |
| `test_type` | Stable control identifier |
| `title` | Human-readable control title |
| `endpoint` | Assessed gateway endpoint |
| `method` | HTTP method used by the control |
| `is_vulnerable` | Whether the control found an exposure |
| `severity` | `critical`, `high`, `medium`, `low`, `info`, or `none` |
| `description` | Concise finding explanation |
| `recommendation` | Remediation guidance |
| `ot_impact` | Industrial consequence when relevant |
| `evidence` | Bounded, redacted structured proof |
| `error` | Normalized execution error, if any |

## Score

The score is deterministic:

```text
max(0, 100 - 30 × Critical - 15 × High - 7 × Medium - 2 × Low)
```

Safe, informational, and error results do not subtract points. Errors influence the execution status and are shown separately so an incomplete assessment cannot be confused with a clean result.

## Evidence rules

Evidence is JSON-compatible, size-bounded, and redacted before persistence. Authorization, cookie, token, password, secret, and API-key values are replaced with `[REDACTED]`. Raw platform JWTs, gateway tokens, reset keys, database credentials, and full oversized responses must never be stored.

## Schema upgrades

New databases are created from the SQLAlchemy models. Existing local databases from the generic scanner can be upgraded with `backend/migrations/lot5_schema.sql`. The migration is idempotent and intended for this local demonstration project; it is not a general migration framework.

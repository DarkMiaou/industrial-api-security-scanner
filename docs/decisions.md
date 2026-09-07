# IASS-OT Decision Log

This log captures the decisions that materially shaped the delivered system.

## DEC-001 — Five development containers

The development environment uses nginx, React, FastAPI, PostgreSQL, and a separate OT gateway container. This keeps the simulated asset outside the scanner process and makes the trust boundary visible.

## DEC-002 — Closed target selection

The browser sends `ot-gateway-demo`, not a URL. The backend alone resolves that value to `http://ot-gateway-demo:8081`, preventing the scanner from becoming a general-purpose SSRF proxy.

## DEC-003 — Server-owned limits and credentials

Request budgets, timeouts, response limits, gateway credentials, and the reset key are configuration owned by the backend. The user cannot raise limits or provide target credentials.

## DEC-004 — Profile fixed at gateway startup

`OT_PROFILE` is read when the gateway container starts. Changing profile therefore requires recreating the gateway, which produces a clear and reproducible demonstration state.

## DEC-005 — Gateway restricted to the internal network

Port 8081 is never published and nginx has no gateway route. Only the backend can reach the simulated OT service.

## DEC-006 — In-memory process state

Pumps, telemetry, rate-limit counters, and audit records remain in memory. `/demo/reset` restores a deterministic scenario and is protected by an internal key.

## DEC-007 — Separate identity domains

Platform users authenticate with the platform JWT. Guest, Operator, Supervisor, and Admin gateway identities use a distinct issuer, signing secret, and purpose.

## DEC-008 — Synchronous scanner in a worker thread

The scanner uses the synchronous `requests` client. The asynchronous FastAPI route delegates orchestration to a threadpool so blocking network calls do not run on the event loop.

## DEC-009 — Client-side printable report

The early design proposed a backend HTML endpoint. The delivered report is a protected React route at `/scans/:id/report`; it loads only the owner-authorized JSON scan contract, contains no raw credentials, and uses a dedicated print stylesheet.

## DEC-010 — Purpose-built data model

`Scan` and `TestResult` contain the metadata required by the seven fixed controls. The model is intentionally not a universal vulnerability-management schema.

## DEC-011 — Lightweight local schema upgrade

New databases use SQLAlchemy model creation. Existing inherited local databases can apply the idempotent `backend/migrations/lot5_schema.sql`; introducing a full migration framework is outside v1.0.

## DEC-012 — Profile derived from the scan

The early design proposed an authenticated `/config/scan` route. It was not needed: the frontend owns fixed public target metadata, while the authoritative gateway profile is captured from the health preflight and returned with every completed scan.

## DEC-013 — Persist authorization confirmation

The scan request and database record both retain the user's explicit authorization confirmation. This is an accountability signal, not a substitute for legal permission.

## DEC-014 — Preserve useful upstream structure

Authentication, database foundations, routing conventions, nginx, and frontend tooling were retained where they remained useful. Scanner and interface behavior were adapted without an unnecessary full rewrite.

## DEC-015 — Error results do not improve or reduce the score

Execution errors are reported separately and influence `partial` or `failed` state. They do not subtract score because an unexecuted check is not evidence of a vulnerability; the status prevents it from being mistaken for assurance.

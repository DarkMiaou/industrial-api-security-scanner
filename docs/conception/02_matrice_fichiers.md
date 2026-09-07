# File Responsibility Matrix

This document explains which parts of the upstream project were retained, adapted, replaced, or added for IASS-OT.

## Root and infrastructure

| Path | Treatment | Responsibility |
|---|---|---|
| `README.md` | Replaced | Primary English setup and operator guide |
| `SECURITY.md` | Added | Authorized-use, secret, and deployment policy |
| `.env.example` | Adapted | Platform, database, scanner, and gateway configuration template |
| `compose.yml` | Adapted | Production-oriented four-container runtime |
| `dev.compose.yml` | Adapted | Five-container development runtime with health checks |
| `justfile` | Adapted | Start, stop, test, lint, and build commands |
| `conf/nginx/` | Retained | Single browser entry point and `/api` reverse proxy |

## Backend

| Area | Treatment | Responsibility |
|---|---|---|
| `routes/auth.py`, auth service, user model | Retained | Platform registration and JWT login |
| `routes/scans.py` | Adapted | Authorized scan creation, listing, and owner-only retrieval |
| `models/Scan.py`, `models/TestResult.py` | Adapted | OT execution metadata and normalized findings |
| schemas and repositories | Adapted | API contracts and persistence |
| `core/target_policy.py` | Added | Closed target resolution and SSRF boundary |
| `core/safe_http.py` | Added | Timeouts, redirect blocking, body cap, redaction, request accounting |
| `core/request_budget.py` | Added | Shared immutable request ceiling |
| `core/redaction.py` | Added | Recursive secret removal and evidence bounding |
| `core/control_catalog.py` | Added | Stable seven-control metadata and order |
| `core/scoring.py` | Added | Deterministic severity-weighted score |
| generic scanner files | Adapted | Four API-focused gateway controls |
| `ot_*_scanner.py` | Added | Command authorization, audit, and command rate-limit controls |
| `services/scan_service.py` | Replaced | Full orchestration, normalization, status, and persistence |
| `migrations/lot5_schema.sql` | Added | Idempotent local upgrade from the inherited schema |
| `backend/tests/` | Added | Unit and orchestration coverage for the safety-critical backend |

## OT gateway

| Path | Treatment | Responsibility |
|---|---|---|
| `ot-gateway-demo/app/main.py` | Added | Pump, telemetry, command, audit, reset, and health endpoints |
| `app/security.py` | Added | Demo identities, tokens, roles, and zone checks |
| `app/audit.py` | Added | In-memory correlated audit records |
| `app/rate_limit.py` | Added | Deterministic hardened command throttling |
| `app/models.py` | Added | Request, response, pump, telemetry, and audit contracts |
| `tests/` | Added | Profile, authorization, reset, SQLi, audit, and throttling tests |

## Frontend

| Area | Treatment | Responsibility |
|---|---|---|
| authentication pages/components | Retained and restyled | Platform account access |
| `DashboardPage.tsx` | Replaced | OT scope, scan launch, control plan, and history |
| `NewScanForm.tsx` | Replaced | Locked target and mandatory authorization confirmation |
| `ScansList.tsx` | Adapted | Profile, status, score, and severity history |
| `ScanResultsPage.tsx` | Replaced | Scan summary and grouped normalized findings |
| `TestResultCard.tsx` | Replaced | Endpoint, method, severity, impact, evidence, and remediation |
| `ScanReportPage.tsx` | Added | Printable report generated from owner-authorized API data |
| types, guards, constants, and presentation helpers | Adapted | Runtime/API alignment and consistent labels |
| CSS files | Adapted or added | Responsive OT visual system and print layout |

## Documentation

| Path | Responsibility |
|---|---|
| `docs/ARCHITECTURE.md` | Authoritative implementation architecture |
| `docs/DEMO.md` | Rehearsable 5–7 minute demonstration |
| `docs/VALIDATION.md` | Recorded quality and runtime checks |
| `docs/decisions.md` | Architectural decision log |
| `docs/conception/` | Requirements, traceability, and delivery history |

Generated folders such as `node_modules`, `dist`, Python caches, and local databases are not source architecture and are excluded from version control.

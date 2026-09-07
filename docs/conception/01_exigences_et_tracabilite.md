# Requirements and Traceability

This matrix records the final v1.0 state. `Implemented` means the behavior exists and has direct code or test evidence. `Deferred` identifies optional work that does not block v1.0.

## Scope and safety

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| SCP-01 | Represent one simulated pumping station, not a multi-site platform. | Implemented | `ot-gateway-demo/app/main.py` |
| SCP-02 | Accept only the closed target key `ot-gateway-demo`. | Implemented | `backend/core/target_policy.py`, target-policy tests |
| SCP-03 | Require explicit user authorization before a scan. | Implemented | scan schema, route, and `NewScanForm.tsx` |
| SCP-04 | Keep the gateway private to the Docker network. | Implemented | both Compose files |
| SCP-05 | Never activate the simulated emergency stop. | Implemented | `ot_command_scanner.py` and scanner tests |
| SCP-06 | Make no IEC 62443 certification claim. | Implemented | `README.md`, `SECURITY.md`, report disclaimer |

## Gateway

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| GTW-01 | Run a health-checked gateway on internal port 8081. | Implemented | gateway Dockerfile and Compose definitions |
| GTW-02 | Select `vulnerable` or `hardened` at startup. | Implemented | `app/config.py`, `OT_PROFILE` |
| GTW-03 | Restore deterministic assets and telemetry. | Implemented | gateway state store and reset tests |
| GTW-04 | Provide Guest, Operator, Supervisor, and Admin identities. | Implemented | `app/security.py` |
| GTW-05 | Enforce RBAC and zone ownership in hardened mode. | Implemented | access-control tests |
| GTW-06 | Expose intentional auth, BOLA, SQLi, audit, and rate-limit weaknesses in vulnerable mode. | Implemented | gateway test suite |
| GTW-07 | Protect `/demo/reset` with the internal reset key. | Implemented | state/auth tests |
| GTW-08 | Emit complete, correlated audit records in hardened mode. | Implemented | audit tests |
| GTW-09 | Return deterministic `429` and `Retry-After` behavior in hardened mode. | Implemented | rate-limit tests |

## Scanner security envelope

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| SEC-01 | Resolve a symbolic key to one fixed internal origin. | Implemented | `target_policy.py` |
| SEC-02 | Reject arbitrary schemes, hosts, ports, and redirects. | Implemented | target-policy and safe-HTTP tests |
| SEC-03 | Apply connection/read timeouts and a 1 MiB response cap. | Implemented | `safe_http.py` |
| SEC-04 | Share a server-owned 60-request budget across all controls. | Implemented | `request_budget.py`, budget tests |
| SEC-05 | Persist the actual request count. | Implemented | orchestrator and orchestration tests |
| SEC-06 | Redact secrets before persisting evidence. | Implemented | `redaction.py`, redaction tests |
| SEC-07 | Keep platform and gateway credentials separate. | Implemented | backend configuration and gateway configuration |

## Controls, orchestration, and data

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| CTL-01 | Authentication enforcement control. | Implemented | `auth_scanner.py` |
| CTL-02 | Object-level authorization/BOLA control. | Implemented | `idor_scanner.py` |
| CTL-03 | SQL injection control. | Implemented | `sqli_scanner.py` |
| CTL-04 | Authentication rate-limit control. | Implemented | `rate_limit_scanner.py` |
| CTL-05 | OT command authorization control. | Implemented | `ot_command_scanner.py` |
| CTL-06 | OT audit completeness control with state restoration. | Implemented | `ot_audit_scanner.py` |
| CTL-07 | OT command rate-limit control with bounded idempotent calls. | Implemented | `ot_rate_limit_scanner.py` |
| ORC-01 | Execute controls in canonical order in a worker thread. | Implemented | `scan_service.py`, `routes/scans.py` |
| ORC-02 | Isolate control errors and derive completed/partial/failed state. | Implemented | orchestration tests |
| ORC-03 | Persist profile, score, requests, duration, completion time, and normalized results. | Implemented | models, schemas, repositories |
| ORC-04 | Apply the documented weighted score with a zero floor. | Implemented | `scoring.py`, orchestration tests |
| ORC-05 | Restrict scan retrieval to its owner. | Implemented | repository/service ownership checks |

## Interface, report, and quality

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| UI-01 | Present an OT laboratory dashboard with a locked target. | Implemented | `DashboardPage.tsx`, `NewScanForm.tsx` |
| UI-02 | Show the profile, status, score, duration, requests, and severity counts. | Implemented | dashboard/results pages |
| UI-03 | Group and explain all seven controls and their OT impact. | Implemented | result cards and presentation helpers |
| RPT-01 | Produce a printable owner-only report from stored scan data. | Implemented | `ScanReportPage.tsx`, protected route |
| RPT-02 | Include scope, summary, findings, errors, limitations, and disclaimer. | Implemented | report component and print stylesheet |
| NFR-01 | Health-check the complete Docker stack. | Implemented | Dockerfiles and Compose files |
| NFR-02 | Validate backend, gateway, and frontend with repeatable commands. | Implemented | root `justfile` and test suites |
| DOC-01 | Provide English setup, architecture, security, and demo documentation. | Implemented | root README, SECURITY, `docs/` |
| DOC-02 | Provide sanitized reference screenshots. | Implemented | `docs/assets/` |
| OPT-01 | JSON export, graphical comparison, Wazuh integration, and React component tests. | Deferred | Optional post-v1.0 enhancements |

The final verification record is maintained in [../VALIDATION.md](../VALIDATION.md).

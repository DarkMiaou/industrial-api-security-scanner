# IASS-OT Architecture

## 1. Purpose and boundaries

IASS-OT models one deterministic water-pump API security scenario. It is deliberately narrower than a general-purpose scanner:

- one server-resolved target key: `ot-gateway-demo`;
- one simulated station with two pumps and two zones;
- two mutually exclusive startup profiles: `vulnerable` and `hardened`;
- seven bounded controls;
- no arbitrary URL, OpenAPI discovery, Internet scan, real PLC, or industrial protocol.

IEC 62443 provides vocabulary and context only. The application does not claim compliance or certification.

## 2. Runtime components

| Component | Technology | Responsibility | Exposed in development |
|---|---|---|---|
| Reverse proxy | Nginx | Single browser entry point, `/api` proxy, health endpoint | `localhost:80` |
| Frontend | React, TypeScript, Vite | Authentication UI, assessment configuration, history, results, printable report | `localhost:5173` |
| Scanner API | FastAPI, SQLAlchemy | Platform authentication, target policy, orchestration, scoring, ownership, persistence | `localhost:8000` |
| Database | PostgreSQL 16 | Users, scans, and test results | `localhost:5432` |
| OT gateway | FastAPI | Simulated process state, identities, RBAC, audit, validation, and rate limiting | Docker network only |

Development uses five containers because Vite and Nginx are separate. The production-oriented image builds the frontend into Nginx, resulting in four runtime containers.

## 3. Trust boundaries

```text
Untrusted browser input
        |
        | platform JWT
        v
+-----------------------------+
| FastAPI platform boundary   |
| - Pydantic request schema   |
| - authenticated user        |
| - scan ownership            |
| - closed target policy      |
+-------------+---------------+
              |
              | server-created URL and demo identities
              | no redirects, 3 s connect / 5 s read timeout
              | 1 MiB response cap, 60-request shared budget
              v
+-----------------------------+
| Docker-only OT gateway      |
| - deterministic state       |
| - vulnerable/hardened mode  |
| - independent gateway JWT   |
+-----------------------------+
```

The user controls only the selected test identifiers and the required authorization acknowledgement. The user cannot provide a URL, token, request limit, gateway role, or emergency-stop confirmation.

## 4. Assessment sequence

```text
POST /scans/
  1. Validate the platform JWT, target key, selected controls, and authorization flag.
  2. Move synchronous scan work into a worker thread.
  3. Resolve the closed target key on the server.
  4. Create one shared 60-request budget.
  5. Read `/health` and validate the gateway-reported profile.
  6. Persist the Scan with status `running`.
  7. Call the protected `/demo/reset` endpoint.
  8. Execute selected controls in the canonical order.
  9. Redact and commit each TestResult immediately.
 10. Calculate the score from vulnerable results only.
 11. Persist `completed`, `partial`, or `failed` with request count and duration.
 12. Return the owned Scan and ordered results.
```

If one scanner raises an exception, the orchestrator converts it into an `error` result and continues with the next selected control when the safety budget permits. If reset fails, no control is executed and the scan is finalized as `failed`.

## 5. Canonical control order

1. `auth`
2. `idor`
3. `sqli`
4. `rate_limit`
5. `ot_command_authz`
6. `ot_audit`
7. `ot_rate_limit`

The frontend sorts stored results with the same order. Selection order in the request does not change execution order.

## 6. Safe HTTP envelope

Every scanner uses `SafeScannerClient` and a `ResolvedTarget`; scanner classes never receive a raw URL.

| Control | Enforced behavior |
|---|---|
| Destination | Exact `http://ot-gateway-demo:8081` origin and normalized relative paths |
| Redirects | Disabled |
| Connection timeout | 3 seconds |
| Read timeout | 5 seconds |
| Response size | 1 MiB maximum |
| Evidence excerpt | 500 characters maximum |
| Request budget | 60 shared requests per assessment |
| Redaction | Recursive key and bearer-value masking |

The 61st request is rejected before network I/O. Network failures, oversized responses, unexpected origins, and abnormal timeouts fail the active control safely.

## 7. Gateway model

Initial process state after `/demo/reset`:

| Asset | Zone | State |
|---|---|---|
| `pump-001` | A | stopped |
| `pump-002` | B | running |

Initial telemetry is 2.5 bar, 120 L/min, 65% level, emergency stop disabled, and a 2.5 bar setpoint.

The gateway owns four demonstration identities:

| Role | Hardened-profile access |
|---|---|
| Guest | No process endpoint |
| Operator A/B | Telemetry and the pump in the assigned zone |
| Supervisor | Pump start/stop commands |
| Admin | Audit, setpoint changes, and explicitly confirmed emergency stop |

The scanner never confirms emergency stop. Its reversible audit control restores the pump to its original state.

## 8. Profile behavior

| Security behavior | Vulnerable profile | Hardened profile |
|---|---|---|
| Telemetry authentication | Missing/invalid authentication can succeed | Rejected |
| Pump object authorization | Cross-zone object can be read | Zone ownership enforced |
| Maintenance-order input | Simulated SQL behavior for known harmless probes | Strict integer validation |
| Login throttling | No deterministic limit | `429` with `Retry-After` |
| OT command authorization | Insufficient roles can issue commands | RBAC and confirmation enforced |
| Command audit | Missing or incomplete event | Complete correlated event |
| OT command throttling | No deterministic limit | `429` with `Retry-After` |

`OT_PROFILE` is read when the gateway starts. No API route can switch it at runtime.

## 9. Persistence model

```text
User 1 ----- * Scan 1 ----- * TestResult
```

### User

- `email`: unique account identifier.
- `hashed_password`: bcrypt hash; plaintext is never stored.
- `is_active`: account state.

### Scan

- owner: `user_id`;
- target: canonical URL, closed key, and display name;
- context: gateway profile and authorization acknowledgement;
- lifecycle: status, start date, completion date;
- metrics: score, actual request count, and duration.

### TestResult

- identity: control type and human-readable title;
- location: HTTP method and endpoint;
- outcome: `safe`, `vulnerable`, or `error` plus severity;
- explanation: details and OT impact;
- supporting data: redacted JSON evidence and recommendations.

Deleting a user cascades to scans and results. Deleting a scan cascades to its results. Reads and deletes validate scan ownership and return `403` for a different authenticated user.

Existing local databases can be upgraded with `backend/migrations/lot5_schema.sql`. Fresh databases are created from SQLAlchemy metadata.

## 10. Score model

```text
score = max(0, 100 - 30C - 15H - 7M - 2L)
```

`C`, `H`, `M`, and `L` count only vulnerable Critical, High, Medium, and Low results. Informational, safe, and error results have no penalty. The score is pedagogical and is not a risk certification.

## 11. Frontend architecture

- TanStack Query owns server state and invalidates the scan history after creation or deletion.
- Zustand keeps short-lived form state and evidence expansion state.
- Runtime guards validate API responses before the UI uses them.
- The target card is display-only; the form submits the constant target key.
- Result cards render all three outcome states and keep raw evidence collapsed.
- `/scans/:id/report` renders a separate sanitized view and invokes `window.print()`.
- Print CSS uses an A4 layout and hides interactive controls.

## 12. Deliberate non-goals

- Real OT equipment, PLCs, SCADA systems, or industrial protocols.
- Internet scanning, subnet discovery, proxy support, or redirect following.
- Destructive exploitation, denial of service, persistence, or lateral movement.
- Multi-site asset inventory, SOC integration, Redis, Celery, or distributed workers.
- Server-side PDF generation.
- IEC 62443 compliance or certification.

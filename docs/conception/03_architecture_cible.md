# Delivered IASS-OT Architecture

The target architecture defined during the design phase is now implemented. See [../ARCHITECTURE.md](../ARCHITECTURE.md) for the complete runtime documentation.

## Logical flow

```text
Browser -> nginx -> React frontend
                 -> FastAPI backend -> PostgreSQL
                                    -> isolated OT demo gateway
```

The development stack contains five containers: `nginx`, `frontend`, `backend`, `db`, and `ot-gateway-demo`. The gateway is reachable only from the internal Docker network; neither nginx nor the host publishes port 8081.

## Trust boundaries

1. The browser authenticates only to the platform backend.
2. The platform JWT never becomes a gateway credential.
3. A user submits the symbolic target key `ot-gateway-demo`, never an arbitrary URL.
4. `TargetPolicy` resolves that key to the fixed internal gateway URL.
5. `SafeScannerClient` enforces the request budget, timeout, redirect, response-size, and evidence-redaction rules.
6. Gateway credentials and the reset key remain server-side.

## Assessment sequence

1. `POST /api/scans` validates the authorization confirmation and closed target key.
2. The backend creates a `running` scan record.
3. A worker thread checks gateway health and executes the seven controls in canonical order.
4. Every control shares one request budget and returns a normalized `TestResult`.
5. Results, request count, duration, gateway profile, status, and score are persisted.
6. The owner retrieves the scan through `GET /api/scans/{id}`.
7. The React report route `/scans/:id/report` renders the stored data for printing.

## Canonical controls

| Order | Control | Domain |
|---:|---|---|
| 1 | Authentication enforcement | API |
| 2 | Object-level authorization | API |
| 3 | SQL injection handling | API |
| 4 | Authentication rate limiting | API |
| 5 | OT command authorization | OT |
| 6 | OT audit completeness | OT |
| 7 | OT command rate limiting | OT |

## Reproducible profiles

`OT_PROFILE=vulnerable` intentionally exposes teaching weaknesses. `OT_PROFILE=hardened` activates RBAC, zone ownership, audit records, safer query handling, and rate limiting. The gateway state is reset before each scan using an internal key, which keeps demonstrations repeatable.

## Safety invariants

- Only `ot-gateway-demo` is accepted as a target.
- Redirects are disabled and destination policy is checked before every request.
- The server owns all limits and credentials.
- The total assessment budget is 60 requests by default.
- Emergency stop is tested only with the non-confirming request; the scanner never activates it.
- Stored evidence is bounded and redacted.
- Scan ownership is checked before returning results.

## Error behavior

The orchestrator isolates control failures. A failed control produces an `error` result and later controls may continue while budget remains. Final status is `completed`, `partial`, or `failed`; errors are counted but do not reduce the security score.

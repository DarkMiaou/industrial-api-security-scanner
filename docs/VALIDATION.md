# IASS-OT v1.0 Validation Record

This record captures the final Lot 7 checks performed on 2026-09-07. The host was macOS with Docker Desktop 28.2.2 on ARM64. Timing varies with network and hardware, but functional outcomes are deterministic.

## Automated quality gates

| Area | Gate | Result |
|---|---|---|
| Backend | Ruff static analysis | Passed |
| Backend | Pytest | 58 passed in 0.51 s |
| OT gateway | Ruff static analysis, non-root image | Passed |
| OT gateway | Pytest | 11 passed in 0.23 s |
| Frontend | TypeScript project check | Passed |
| Frontend | Biome | 43 files checked, no fixes required |
| Frontend | Stylelint | Passed with zero warnings |
| Frontend | Vite production build | 271 modules transformed in 1.11 s |
| Production images | Backend, frontend, and OT gateway Compose build | Passed |
| Compose definitions | Development and production configuration validation | Passed |

The root `just check` recipe reproduces the backend, gateway, and frontend quality gates in containers.

## Fresh-build timing

The development images were rebuilt with Docker layer caching disabled:

```bash
docker compose -f dev.compose.yml build --no-cache
```

Observed wall-clock time: **115.11 seconds**. This includes operating-system packages plus Python and pnpm dependency downloads and is well below the 20-minute acceptance budget. A subsequent complete build, recreation, dependency wait, and health-check start took **18.82 seconds**.

## Runtime health

After recreation, all five development services reached the expected state:

| Service | Expected condition | Observed |
|---|---|---|
| `db` | PostgreSQL ready | Healthy |
| `ot-gateway-demo` | `/health` answers internally | Healthy |
| `backend` | `/health` answers on port 8000 | Healthy |
| `frontend` | Vite answers on port 5173 | Healthy |
| `nginx` | `/health` answers on port 80 | Healthy |

Health probes use explicit `127.0.0.1` addresses so Alpine containers do not resolve `localhost` to an IPv6 listener that the process does not expose.

## End-to-end profile comparison

Each reference scan used the seven canonical controls, the closed target, authorization confirmation, and the same 60-request server budget. The gateway reset its state before each run.

| Profile | Status | Safe | Vulnerable | Errors | Score | Requests | Duration |
|---|---|---:|---:|---:|---:|---:|---:|
| `vulnerable` | Completed | 0 | 7 | 0 | 0/100 | 45 | 3,628 ms |
| `hardened` | Completed | 7 | 0 | 0 | 100/100 | 41 | 2,585 ms |

The gateway was restored to the default `vulnerable` profile after validation. The temporary validation account and its two scans were deleted after the measurements.

## Documentation and visual review

- Root README, security policy, implementation architecture, decision log, traceability matrix, data model, delivery record, and demo guide are written in English.
- Historical upstream notes are clearly marked as non-authoritative.
- The 5–7 minute demo guide covers both profiles, report printing, safety boundaries, and cleanup.
- Login and registration reference captures were inspected at 1280×720. Their fields are empty and they contain no token, password, email address, reset key, or internal credential.

Reference captures:

- `docs/assets/login.jpg`
- `docs/assets/register.jpg`
- `docs/assets/assessment-control-plan.png`
- `docs/assets/profile-comparison.png`
- `docs/assets/vulnerable-assessment.png`
- `docs/assets/hardened-assessment.png`

All six captures were inspected at full resolution. The assessment images exclude the signed-in account identity and unrelated browser overlays, while diagnostic evidence remains collapsed or outside the captured frame.

## Interpretation limit

Passing these checks confirms the behavior of the local educational laboratory. It does not certify a real industrial system, establish IEC 62443 compliance, or authorize testing of an external target.

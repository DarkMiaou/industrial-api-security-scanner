# Security Policy

## Supported scope

IASS-OT is an educational local laboratory. Security fixes are applied to the current branch only; no long-term support or production security guarantee is provided.

The intentionally vulnerable behavior of `ot-gateway-demo` when `OT_PROFILE=vulnerable` is part of the teaching scenario. A report about that documented behavior is not a vulnerability in this repository unless it escapes the local gateway boundary or affects the platform itself.

## Reporting a vulnerability

Do not publish an unpatched platform vulnerability in a public issue. Report it privately to the repository owner through the private security-reporting channel configured on the repository host. Include:

- the affected commit and component;
- a concise impact statement;
- exact reproduction steps using the local laboratory;
- logs or screenshots with credentials and tokens removed;
- a suggested remediation, if available.

Do not include real industrial addresses, production data, personal credentials, or secrets.

## Laboratory safety rules

The following boundaries are mandatory:

1. Run assessments only against the bundled `ot-gateway-demo` service.
2. Do not add user-controlled URLs, hosts, ports, schemes, redirects, or proxy settings to the scan request.
3. Do not expose gateway port `8081` on the host in committed Compose files.
4. Do not add destructive payloads, denial-of-service loops, long time-based probes, file access, command execution, or real industrial protocols.
5. Keep the global request budget at or below 60 unless the safety model and tests are reviewed first.
6. Never send the confirmation header for the simulated emergency-stop command.
7. Restore changed gateway state after every reversible control and reset the gateway before each assessment.
8. Keep platform and gateway JWT secrets separate.

## Secrets and local configuration

- Copy `.env.example` to `.env`; never commit `.env`.
- Replace `SECRET_KEY`, `OT_JWT_SECRET`, database credentials, and `OT_DEMO_RESET_KEY` outside local development.
- Values in `.env.example` are demonstration placeholders and must never be reused in a shared or public deployment.
- Never place credentials in screenshots, reports, issues, commits, or test fixtures intended for publication.

Before committing, inspect staged changes for tokens, passwords, private keys, cookies, and connection strings.

## Scanner security controls

The scanner's safety envelope is implemented in these modules:

- `backend/core/target_policy.py`: resolves the single allowed target key.
- `backend/core/safe_http.py`: disables redirects, applies split timeouts, caps response bodies, and records sanitized response metadata.
- `backend/core/request_budget.py`: shares a 60-request budget across preflight, reset, and all selected controls.
- `backend/core/redaction.py`: recursively masks sensitive keys and bearer-like values.
- `backend/services/scan_service.py`: resets the target, executes controls in a fixed order, persists each result, and records terminal metrics.

Changes to these files require targeted tests and a complete vulnerable/hardened smoke test.

## Data handled by the platform

The platform stores local account emails, bcrypt password hashes, scan ownership, assessment metadata, findings, sanitized evidence, and recommendations in PostgreSQL.

The printable report intentionally excludes raw evidence. The interactive evidence view is available only to the authenticated owner of the scan. Cross-user read and delete attempts return HTTP `403`.

To remove all local laboratory data:

```bash
docker compose -f dev.compose.yml down -v
```

This action permanently deletes the local database volume.

## Deployment limitations

The production-oriented Compose file is a packaging example, not a complete public-cloud deployment. Before any shared deployment, add at minimum:

- unique secrets delivered by a secret manager;
- TLS termination and an appropriate Content Security Policy;
- restricted ingress and egress rules;
- centralized logs with retention controls;
- dependency and container-image scanning;
- database backups and migration management;
- a documented incident-response process.

IASS-OT must not be represented as IEC 62443 compliant or certified. It demonstrates selected security concepts only.

# Delivery Lots and Acceptance Criteria

IASS-OT was delivered through eight bounded lots. This document records what each lot established and how it is accepted.

| Lot | Delivered outcome | Acceptance evidence | State |
|---:|---|---|---|
| 0 | Reproducible baseline and working branch | Repository inventory, branch `iass-ot`, preserved upstream base | Complete |
| 1 | Deterministic OT gateway | Two profiles, fixed state, identities, reset, health, gateway tests | Complete |
| 2 | Scanner safety envelope | Closed target, SSRF rejection, timeouts, response cap, budget, redaction tests | Complete |
| 3 | Four API security controls | Authentication, BOLA, SQLi, and auth rate-limit scanners in both profiles | Complete |
| 4 | Three OT security controls | Command authorization, audit, and command rate limiting with safe cleanup | Complete |
| 5 | Orchestration, persistence, and score | Canonical workflow, normalized data, ownership, final status, score tests | Complete |
| 6 | OT interface and printable report | Locked scope, authorization confirmation, history, results, print route | Complete |
| 7 | Quality, documentation, and demonstration | Health checks, unified checks, English docs, demo guide, sanitized captures | Complete |

## Final validation gates

The v1.0 baseline is accepted when all of the following are true:

- the development Compose stack starts and every service becomes healthy;
- the gateway is not published to the host or exposed through nginx;
- vulnerable and hardened profiles produce reproducibly different results after reset;
- backend lint and essential tests pass;
- gateway lint and tests pass;
- frontend type checking, linting, stylesheet linting, and production build pass;
- setup from a prepared Docker workstation fits inside a 20-minute teaching slot;
- the documented walkthrough can be delivered in 5–7 minutes;
- reports and screenshots contain no credentials or secret values;
- README, security guidance, architecture, traceability, and validation documents describe the real implementation in English.

Run all static and automated checks from the repository root:

```bash
just check
```

Runtime validation and observed reference values are recorded in [../VALIDATION.md](../VALIDATION.md).

## Definition of done

Version 1.0 is complete when the final gates above pass. Optional exports, trend charts, external SIEM integration, richer component tests, and multi-target scanning remain outside this definition and may be considered separately.

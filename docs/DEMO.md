# IASS-OT Demonstration Guide

This script is designed for a 5–7 minute portfolio or interview demonstration. It uses only the local Docker laboratory and does not expose credentials or raw evidence.

## Preparation before the meeting

1. Create `.env` from `.env.example` and keep it out of Git.
2. Start the vulnerable profile:

   ```bash
   OT_PROFILE=vulnerable docker compose -f dev.compose.yml up --build -d
   ```

3. Check that all five services are ready:

   ```bash
   docker compose -f dev.compose.yml ps
   ```

4. Open `http://localhost`, register a disposable local demonstration account, and sign in.
5. Close terminals containing environment values and clear unrelated browser tabs.
6. Keep the browser at 1280×720 or larger and use 100% zoom.

Never show `.env`, gateway tokens, platform JWTs, database connection strings, or expanded technical evidence during a recorded demonstration.

## 0:00–0:45 — Introduce the problem

Suggested explanation:

> IASS-OT is a deliberately bounded API security laboratory for a simulated water-pump gateway. It demonstrates how ordinary API weaknesses become operational risks without connecting to real industrial equipment or protocols.

Point out the three dashboard safeguards:

- one server-enforced local target;
- a maximum of 60 requests;
- seven non-destructive controls.

Make the limitation explicit: this is not an IEC 62443 certification product.

## 0:45–1:30 — Explain the assessment plan

Show the locked **Water Pump Gateway** target and the two control groups:

- API boundary controls: authentication, BOLA/IDOR, SQL injection, and login throttling;
- OT operational safeguards: command authorization, correlated audit, and command throttling.

Explain that the frontend sends only a target key. The backend resolves the internal Docker address and owns the request budget, timeouts, and credentials.

Keep all seven controls selected, check the authorization acknowledgement, and start the assessment.

## 1:30–2:45 — Review the vulnerable profile

The complete vulnerable run should finish in a few seconds, remain below 60 requests, and return seven ordered results.

Highlight:

- the backend-reported `vulnerable` profile;
- the execution status, duration, and actual request count;
- the security score and separate safe/finding/error counts;
- one API finding and one OT-specific finding.

Open a result card and explain the four layers:

1. control and endpoint;
2. outcome and severity;
3. direct observation;
4. concrete OT impact and remediation.

Do not expand raw evidence in a recorded or shared demonstration.

## 2:45–3:30 — Explain the safety design

Briefly describe the implementation:

- redirects are disabled;
- connection/read timeouts are 3/5 seconds;
- response bodies are capped at 1 MiB;
- evidence excerpts are capped at 500 characters and recursively redacted;
- the 61st request is rejected before network I/O;
- emergency stop is never confirmed;
- the audit control restores the pump state.

Explain that every result is persisted immediately. A late technical error produces a `partial` scan instead of deleting earlier evidence.

## 3:30–4:30 — Show the printable report

Select **Open printable report**.

Show the executive summary, scope, profile, metrics, findings, impacts, and recommended actions. Explain that raw technical evidence and credentials are intentionally excluded.

Select **Print or save as PDF** only if the audience wants to see the browser print preview. Cancel the dialog rather than saving a file during the live demonstration.

## 4:30–5:45 — Compare the hardened profile

In a prepared terminal, run:

```bash
OT_PROFILE=hardened docker compose -f dev.compose.yml up -d --force-recreate ot-gateway-demo
```

Wait for the gateway to become healthy:

```bash
docker compose -f dev.compose.yml ps ot-gateway-demo
```

Return to the dashboard and run the same seven controls again. The hardened run should show the backend-reported `hardened` profile and safe results for enforced authentication, zone isolation, input validation, RBAC, audit, and rate limits.

Use the history to compare the two profiles. Stress that the test plan did not change; only the target's startup profile changed.

## 5:45–6:30 — Close with engineering decisions

Summarize three decisions:

1. A closed target key was chosen instead of a generic URL scanner to make SSRF structurally impossible in the v1 workflow.
2. Synchronous scanner code runs in a worker thread, avoiding an unnecessary Celery/Redis deployment for a short local job.
3. The score is a transparent teaching aid, while raw execution errors remain separate from security findings.

Finish by pointing to the automated backend, gateway, and frontend checks.

## Expected reference results

On the validated local environment, a full run produced:

| Profile | Execution | Score | Requests | Typical duration |
|---|---|---:|---:|---:|
| Vulnerable | completed | 0/100 | 45 | about 3.6 s |
| Hardened | completed | 100/100 | 41 | about 2.6 s |

Small timing differences are normal. A result order change, more than 60 requests, an unreported profile, or a non-restored pump state is not normal and should be investigated before presenting.

## After the demonstration

Return the local development gateway to its default profile:

```bash
OT_PROFILE=vulnerable docker compose -f dev.compose.yml up -d --force-recreate ot-gateway-demo
```

Stop the environment without deleting the demonstration history:

```bash
docker compose -f dev.compose.yml down
```

Use `down -v` only when you intentionally want to delete all local accounts and scans.

## Reference screenshots

The repository includes the finalized, sanitized interface captures used by the project presentation:

- [`assets/assessment-control-plan.png`](assets/assessment-control-plan.png): locked target, safety envelope, and seven-control assessment plan;
- [`assets/profile-comparison.png`](assets/profile-comparison.png): vulnerable and hardened runs shown together in the assessment history;
- [`assets/vulnerable-assessment.png`](assets/vulnerable-assessment.png): completed vulnerable profile with seven findings and a 0/100 score;
- [`assets/hardened-assessment.png`](assets/hardened-assessment.png): completed hardened profile with seven safe controls and a 100/100 score;
- [`assets/login.jpg`](assets/login.jpg): empty sign-in form;
- [`assets/register.jpg`](assets/register.jpg): empty account-registration form.

The captures were reviewed at full resolution. They contain no email address, token, password, cookie, environment value, terminal history, expanded diagnostic evidence, or unrelated browser overlay.

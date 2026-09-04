# Security Policy

**AI Job Agent** takes security seriously. This policy covers supported
versions, how to report vulnerabilities, and how secrets — including AI
provider API keys — must be handled.

---

## Supported Versions

| Version | Supported | Notes |
|---|---|---|
| 2.1.x | ✅ Supported | Current release (v2.1.0) |
| 2.0.x | ⚠️ Maintenance | Security fixes only on request |
| < 2.0.0 | ❌ Unsupported | Development snapshots (v0.x tags) |

---

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Please report vulnerabilities privately via **GitHub Security Advisories**
(the "Report a vulnerability" button on the repository's *Security* tab).

When reporting, include:

1. **Description** — what is affected and why it matters.
2. **Severity assessment** — your estimate of impact (critical / high /
   medium / low) and affected components (e.g., API, auth, AI renderer).
3. **Steps to reproduce** — minimal reproduction, including affected versions.
4. **Impact** — what an attacker could do (data exposure, privilege
   escalation, prompt injection, denial of service).
5. **Suggested fix (optional)** — a patch or mitigation, if you have one.

You will receive an acknowledgement within **5 business days** and a status
update at least every **10 business days** until the issue is resolved or
declined.

---

## Responsible Disclosure

- **Coordinate first.** Give maintainers reasonable time (we recommend **90
  days**) to fix and release a patch before any public disclosure.
- **Do not exploit** the vulnerability beyond what is necessary to demonstrate
  it (no data exfiltration, no persistence).
- **Do not test against production instances** you do not own.
- **Delete** any data obtained during research unless the maintainers agree
  otherwise.
- If a vulnerability is actively exploited, disclose with a high-level summary
  immediately — do not wait for the 90-day window.

We will acknowledge valid reports, keep reporters informed of progress, and
credit reporters (with consent) in release notes.

---

## Secret Handling

### Rules for developers

- **Never commit secrets.** `.env` files, API keys, tokens, and certificates
  are covered by `.gitignore` and must never be added to the repository.
- **Rotate leaked secrets.** If a key is exposed (committed, pasted in an
  issue, or logged), revoke and rotate it immediately — treat it as
  compromised.
- **Environment variables only.** All configuration, including `APP_SECRET_KEY`
  and provider API keys, is read from the environment. See
  `backend/.env.example` for the full list.
- **No secrets in logs.** Structured logging masks PII and must never record
  secrets. Request/response bodies of AI providers are not logged.
- **Frontend isolation.** Frontend configuration uses `VITE_`-prefixed
  variables only for non-secret settings. API keys must never be shipped in
  frontend bundles.
- **Backend secret rotation.** `APP_SECRET_KEY` is generated on first setup by
  the launcher scripts. Rotate it in production by setting a new value and
  restarting the backend.

### Runtime safeguards

- Bcrypt password hashing with per-user salts; passwords never stored or
  logged in plaintext.
- JWT with refresh-token rotation and `jti` claim; tokens are not logged.
- CORS restricted to configured origins in production.
- Request/correlation IDs for traceability without leaking internals.

---

## AI Provider API Keys

AI provider API keys (OpenRouter, OpenAI, Anthropic, Gemini, Ollama) are
sensitive credentials that bill your account:

- Configure them **only** in `backend/.env` (or the container environment).
- They are read server-side by the AI provider clients and are never exposed
  through the API or the frontend.
- Do not paste keys into issues, PRs, chat logs, or screenshots.
- Use dedicated keys with spending limits where the provider supports it.
- If a key is suspected of leaking, revoke it at the provider and issue a new
  one before continuing.

---

## Security Features

- Prompt injection protection on all rendered prompt variables (injection
  attempts raise an error before any provider call).
- Ownership-enforced authorization on all user-scoped resources.
- Password strength validation.
- Structured JSON logging with PII masking.
- Health/readiness endpoints for deployment-time verification.

See [docs/security/](docs/security/) for the full security architecture and
checklist.

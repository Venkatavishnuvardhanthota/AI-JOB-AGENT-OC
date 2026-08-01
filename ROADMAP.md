# AI Job Agent — Roadmap

**Version:** 2.1.0 (v2.1.0 — AI Platform Release)

This document summarizes what has been delivered in v2.1.0, ideas under
consideration for future releases, and known technical debt.

**Future items are ideas, not commitments.** Priorities shift with real-world
usage; nothing below is promised.

---

## Completed (v2.1.0)

The original four-sprint implementation roadmap is complete. Highlights:

- **AI Platform (Sprints 1–4):** multi-provider AI abstraction with 5 providers
  (OpenRouter, Ollama, OpenAI, Anthropic, Gemini), 25-templates prompt registry
  with rendering, structured output generation, retry/fallback routing, and 15
  AI feature areas (16 registered functions).
- **Provider ecosystem:** pluggable Provider SDK with factory, registry,
  lifecycle, request pipeline, auth abstraction, and capability system; 10 ATS
  providers; Indian portal providers; discovery routing with four strategies.
- **Universal Form Intelligence Engine:** 15 modules for automated application
  form filling, validation, checkpoints, recovery, and approval workflows.
- **Browser automation:** Playwright-based session, navigation, form filling,
  and screenshots.
- **Production services:** observability, structured logging with correlation
  IDs and PII masking, metrics, health/readiness, alerts, diagnostics.
- **Frontend management center:** provider management, resume/cover letter
  generators, application engine (Kanban), authentication, production
  dashboard.
- **Sprint 4 hardening:** standardized error envelope, request IDs, health
  checks, prompt injection protection (active + 52 regression tests), seed
  script, launcher scripts, Makefile.
- **Quality:** 3,031 passing backend tests, 779 passing frontend tests, 69
  documentation files, independent audit score 6.6/10 (Mostly Ready,
  conditionally approved — conditions met).

---

## Future Ideas (not commitments)

Ideas under consideration — none of these are planned dates or promises:

- **Real-time updates** — WebSocket support for live application and job
  discovery status.
- **Resume parsing** — PDF/DOCX import with structured extraction.
- **Calendar integration** — interview scheduling and reminders.
- **Notifications** — email, in-app, and push notification channels.
- **Advanced analytics** — deeper dashboards, cost analytics, exportable
  reports.
- **More ATS integrations** — expanding coverage beyond the current 10.
- **Multi-language support** — localized UI and job content handling.
- **CI/CD pipeline** — automated builds, tests, and deployment on every push.
- **End-to-end Playwright suite** — full-stack browser-level test coverage.
- **Plugin system** — third-party provider contribution mechanism.

---

## Potential Enhancements

Concrete, well-scoped improvements identified during the v2.1.0 audit and
release preparation. These are candidates for the next release:

- **API request rate limiting** — implement the existing `RateLimitError`
  abstraction as middleware before any public internet deployment.
- **Streaming AI endpoint** — expose an SSE route for real-time AI generation
  (provider and config support already exist).
- **Per-dimension matching scores** — extend the matching response contract so
  `skill`/`experience`/`education`/`company`/`keyword` dimensions return real
  values instead of the single overall score (requires an extended AI prompt
  schema or wiring the richer `app/job_matching/` engine).
- **Resume service decomposition** — split the 1,000+ line `ResumeService`
  into focused modules.
- **Structured parsing in the AI feature layer** — reuse the structured output
  parser across all feature functions.
- **Docker healthcheck hardening** — replace inline `python -c` healthchecks
  with dedicated scripts.

---

## Known Technical Debt

Tracked, understood, and scheduled:

| Item | Location | Notes |
|---|---|---|
| 3 pre-existing test failures | `tests/test_providers.py`, `tests/test_provider_state.py` | Provider registration semantics introduced in Phase 6.2 (commit `27ddf16`); predate Sprint 4; documented in release notes |
| Legacy `cover_letter/` package | `backend/app/cover_letter/` | Deprecated, still imported by orchestrator/application package; half-migrated |
| Mutable global scoring config | `backend/app/api/v1/matching.py` | `global _scoring_config`; lost on restart |
| Legacy prompt templates | `backend/app/ai/dependencies.py` | 10 "legacy compat" templates remain |
| `__import__("datetime")` | `backend/app/main.py` | Should be a standard import |
| Minimal frontend AI service | `frontend/src/services/ai.ts` | Provider CRUD only; no feature-specific endpoints |
| In-memory metrics | production services | Consider Redis/Prometheus for production deployments |

---

See [docs/ROADMAP.md](docs/ROADMAP.md) for the product vision document and
[RELEASE_NOTES_v2.1.0.md](RELEASE_NOTES_v2.1.0.md) for the full release notes.

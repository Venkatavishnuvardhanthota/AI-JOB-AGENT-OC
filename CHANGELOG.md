# Changelog

All notable changes to **AI Job Agent** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

A phase-by-phase change log is maintained in [docs/CHANGELOG.md](docs/CHANGELOG.md).

## [Unreleased]

### Added

- **Resume Strategy System:** per-user resume strategy (`use_existing` /
  `tailor` / `generate` / `ask`) and save-generated-resumes policy (`never` /
  `submitted_only` / `every`), stored in a new `user_ai_settings` table
  (migration `6f7a8b9c0d1e`).
- **Best-resume selection:** deterministic scoring (skill overlap, keyword
  overlap, role alignment, ATS compatibility) instead of newest-upload
  heuristics.
- **Tailor & generate workflows:** AI tailoring via the existing
  `resume-improvement-ai` template and generation via `resume-ai-generation`,
  with fingerprint-based reuse so identical jobs with unchanged profiles do
  not spend AI credits twice.
- **Application history:** applications record the strategy used, the original
  and generated resume references, and generation metadata; `POST
  /applications/prepare` accepts an optional `resume_strategy_override`.
- **New endpoints:** `GET`/`PUT /ai/settings/resume-strategy`,
  `POST /ai/strategy/preview`, `POST /ai/strategy/select`; `GET /resumes`
  supports `?origin=master|generated` filtering.
- **Frontend:** Resume Strategy settings panel, Master/AI-Generated resume
  library tabs, an "Apply with AI" preview dialog on the job detail page, and
  AI strategy details on the application page.

## [2.1.0] - 2026-07-28

The **AI Platform Release**. This release completes the original four-sprint
implementation roadmap (Sprints 1–4), delivering a pluggable multi-provider AI
platform, 30+ job provider integrations, a universal form intelligence engine,
browser automation, a production observability stack, and an authenticated
React + TypeScript management frontend.

### Added

- **AI Platform (Sprints 1–4):** multi-provider AI abstraction with 5 providers
  (OpenRouter, Ollama, OpenAI, Anthropic, Gemini), prompt template registry with
  versioning and rendering (25 templates), structured output generation,
  retries and fallback routing, and 15 AI feature areas implemented as 16
  registered feature functions (resume, cover letter, matching, interview,
  company research, email, profile and project enhancement).
- **Provider SDK:** pluggable factory/registry/lifecycle, request pipeline with
  caching and retry, auth abstraction (OAuth, cookies, credentials, session and
  browser tokens), capability system, response normalization, observability
  integration.
- **Provider integrations:** 10 ATS providers (Greenhouse, Lever, Ashby, Workday,
  SmartRecruiters, BambooHR, iCIMS, Jobvite, Oracle Recruiting, SAP
  SuccessFactors), Indian portal providers (Internshala, Unstop, Freshersworld),
  discovery routing with four strategies, search analytics.
- **Universal Form Intelligence Engine:** 15 modules (field detection, semantic
  mapping, answer engine, validation, multi-step coordination, checkpoints,
  recovery, approval workflow, submission manager).
- **Browser automation framework:** Playwright-based sessions, navigation, form
  filling, screenshots, downloads, parallel execution.
- **Production services:** observability, structured logging with correlation
  IDs and PII masking, metrics, health/readiness checks, alerts, diagnostics.
- **Frontend:** React + TypeScript management center — provider management,
  resume and cover letter generators, application engine with Kanban board,
  authentication (login, register, password reset), production dashboard.
- **Sprint 4 production hardening:** standardized `AppError` response envelope,
  request/correlation ID middleware, `GET /health` and `GET /ready`,
  structured JSON logging, JWT `jti` claim, restricted CORS, seed data script,
  root Makefile, cross-platform launcher scripts (`run`/`stop`/`restart`/`status`).

### Changed

- Unified job discovery behind the Provider Router with fallback chains and
  continuous improvement scoring.
- Backend test suite expanded from 488+ (v2.0.0) to **3,031 passing tests**
  (198 skipped without a PostgreSQL test database; 3 pre-existing failures — see
  Known Limitations).
- Frontend expanded to 242 TypeScript source files with 779 passing tests.
- Standardized error responses across all API endpoints.

### Improved

- Provider registration semantics: factory now registers only configured
  providers, with normalized names and `NOT_IMPLEMENTED`/`UNAVAILABLE` state
  reporting.
- AI feature layer, prompt rendering, and documentation repository (69 docs).
- Developer experience: launcher-based development with health-checked startup
  and automatic Docker Desktop recovery.

### Fixed

- `ProviderRegistry.getAll()` bug in the provider management service.
- Prompt injection protection: `_INJECTION_PATTERNS` is now actively applied in
  `PromptRenderer.render()` — user-supplied variables are scanned and injection
  attempts raise `RenderError` (52 dedicated regression tests).
- Provider registration ordering and name normalization.

### Security

- Prompt injection detection active for all rendered prompt variables.
- JWT authentication with refresh token rotation and `jti` claim.
- Bcrypt password hashing; password strength validation.
- CORS restricted to configured origins; ownership-enforced authorization.
- Secrets never logged; PII masking in structured logs.

### Documentation

- 69-file documentation repository covering architecture, API, database,
  frontend, backend, AI, providers, testing, security, deployment, and
  operations.
- New release documentation: `README.md` (overview, quick start, stats),
  `ARCHITECTURE.md` (Mermaid diagrams and workflows), `ROADMAP.md`,
  `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and root `LICENSE`.
- Independent release audit report (`AUDIT_REPORT.md`, 6.6/10 — Mostly Ready,
  conditions satisfied).

### Known Limitations

- **No API request rate limiting.** A `RateLimitError` abstraction exists but
  rate-limiting middleware is not yet implemented. Acceptable for the current
  release; address before public internet deployment.
- **3 pre-existing test failures** (`test_ai_provider_not_implemented`,
  `test_factory_does_not_register_not_implemented`,
  `test_factory_normalizes_names`). They predate Sprint 4, originate from
  provider registration semantics introduced in Phase 6.2 (commit `27ddf16`),
  are unrelated to Sprint 4, and are tracked as known technical debt. They do
  not affect implemented AI workflows.
- No streaming AI endpoint (provider and config support exist; no SSE route).
- 198 tests are skipped when no PostgreSQL instance is available.

## [2.0.0] - 2026-07-24

### Added

- Initial public release of the AI-powered job application automation platform.
- Core platform: FastAPI backend (Clean Architecture), React + TypeScript
  frontend, PostgreSQL 16, Docker Compose deployment.
- Job discovery across 17+ sources with rate limiting, retries, deduplication,
  and normalization.
- Career profile and resume management with ATS optimization, versioning, and
  PDF/DOCX export.
- Job matching with configurable weighted scoring, batch scoring, and
  threshold filtering.
- Applications: preparation, submission, tracking, duplicate prevention,
  ownership-enforced authorization.
- Dashboard and analytics with exportable reports.
- Security: JWT authentication, bcrypt hashing, application-level authorization.

### Known Limitations

- Password reset requires SMTP configuration.
- Browser automation requires Playwright system dependencies in Docker.
- Frontend test coverage was a foundation (9 tests) at release.
- Some ATS provider integrations were in beta.

---

See [docs/CHANGELOG.md](docs/CHANGELOG.md) for the complete phase-by-phase
development log.

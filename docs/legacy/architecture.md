# Architecture Documentation

## Overview

The AI Job Application Agent follows **Clean Architecture** principles with a clear separation of concerns across layers.

## Layer Structure

### 1. Domain Layer (`backend/app/models/`)
- SQLAlchemy ORM entities
- Domain-specific types and constraints
- No dependency on external frameworks beyond ORM

### 2. Application Layer (`backend/app/services/`)
- Use case orchestration
- Business rule enforcement
- Depends on repositories (abstractions)

### 3. Interface Adapters (`backend/app/api/`, `backend/app/repositories/`)
- **API**: FastAPI route handlers (controllers)
- **Repositories**: Data access implementations
- **Schemas**: Pydantic request/response models

### 4. Frameworks & Drivers (`backend/app/core/`)
- FastAPI framework configuration
- Database engine and session management
- Security (JWT, password hashing)
- Logging (structlog)
- Environment configuration (pydantic-settings)

## Dependency Injection

FastAPI's `Depends()` function is used for DI:
- `get_db()` provides database sessions
- `get_current_user()` authenticates requests
- `get_user_repository()` provides data access
- Repositories are injected into services

## Data Flow

```
HTTP Request
  → FastAPI Router (api/v1/)
    → Depends (auth, db session)
      → Controller (route handler)
        → Service (business logic)
          → Repository (data access)
            → Database (PostgreSQL)
```

## Security

- JWT-based authentication (HS256)
- Password hashing with bcrypt
- OAuth2 password bearer flow
- Superuser role for admin endpoints

## Database

- PostgreSQL 16 with async SQLAlchemy 2.0
- Alembic for schema migrations
- UUID primary keys
- Timestamped entities (created_at, updated_at)

## API Design

- Versioned routes: `/api/v1/`
- RESTful conventions
- Consistent error responses
- OpenAPI documentation at `/docs`

## Frontend Architecture

- React 18 with TypeScript
- Vite for build tooling
- React Router v6 for routing
- Custom API client with JWT token management
- Vitest + Testing Library for tests

## Docker Setup

- Multi-stage Dockerfile for frontend (build + nginx serve)
- Python slim image for backend
- PostgreSQL with health checks
- Separate network for service isolation
- Persistent volume for database data

## Environment Configuration

All configuration is managed via environment variables:
- `APP_SECRET_KEY`: JWT signing key
- `DATABASE_URL`: Async PostgreSQL connection
- `CORS_ORIGINS`: Allowed origins for CORS
- `LOG_LEVEL`: Logging verbosity

## CI/CD Pipeline

GitHub Actions workflow:
1. Backend linting (ruff)
2. Backend tests (pytest with coverage)
3. Frontend linting (ESLint)
4. Frontend tests (vitest)

## Phase 1 Completed Components

- [x] Project structure (Clean Architecture layout)
- [x] Backend skeleton (FastAPI with all layers)
- [x] Frontend skeleton (React + Vite + TypeScript)
- [x] Database models (User entity with UUID PK)
- [x] Authentication (JWT, register, login, /me)
- [x] User management CRUD (admin-only routes)
- [x] Database migrations (Alembic configured)
- [x] Testing infrastructure (pytest, conftest, test DB)
- [x] Docker configuration (backend, frontend, DB)
- [x] Docker Compose (full stack orchestration)
- [x] CI/CD pipeline (GitHub Actions)
- [x] Linting & formatting (ruff, black, ESLint, Prettier)
- [x] Logging (structlog)
- [x] Configuration management (pydantic-settings)
- [x] Environment variables (.env.example)
- [x] Dependency injection (FastAPI Depends)

## Phase 4 — Provider Framework

The [provider framework](providers.md) is a pluggable system for fetching jobs from 17 sources:

- [x] Provider interface (`BaseProvider` ABC)
- [x] Provider registry and factory
- [x] Rate limiting (token-bucket)
- [x] Retry logic with exponential backoff
- [x] Structured logging (structlog)
- [x] Metrics collection
- [x] Health checks
- [x] 17 provider implementations (LinkedIn, Indeed, Wellfound, Greenhouse, Lever, Ashby, Workday, Google Jobs, RemoteOK, We Work Remotely, Career Pages, Y Combinator, Naukri, Foundit, Internshala, Unstop, Freshersworld)
- [x] Job normalization and deduplication
- [x] Job schemas (Pydantic)
- [x] Comprehensive test suite (314 tests)

## Phase 5 — Job Search, Storage & APIs

- [x] `JobPostingRepository` — CRUD, search, filter (keyword, location, remote, salary, job_type, skills), pagination, saved-jobs query, stats aggregation
- [x] `JobSearchService` — orchestrates provider search, normalizes, deduplicates, stores, filters, paginates
- [x] `JobCache` — in-memory TTL cache with LRU eviction for search results
- [x] `JobScheduler` + `JobQueue` — async background job search with task status tracking
- [x] Jobs API routes (`/api/v1/jobs/search`, `/list`, `/{id}`, `/saved`, `/refresh`, `/refresh/status/{task_id}`, `/stats`)
- [x] Frontend: `JobSearchPage` with keyword, location, remote, salary, job_type filters and pagination
- [x] Frontend: `JobDetailPage` with description, skills, requirements, benefits, mark-as-applied, activate/deactivate
- [x] Frontend: `SavedJobsPage` with pagination and status indicators
- [x] Frontend API client (`jobsApi`) and TypeScript types
- [x] Backend tests (314 passing, 0 lint errors)
- [x] Frontend compiles clean (0 TypeScript errors)

## Phase 6 — Match Scoring System

- [x] `SkillExtractor`, `KeywordExtractor`, `ExperienceExtractor`, `EducationExtractor`, `CompanyAnalyzer`
- [x] `MatchScorer` — configurable weighted engine (skill 35%, experience 25%, education 15%, keyword 15%, company 10%), boosts (title match +5%, current company +5%), penalty (blacklisted -30%)
- [x] `ThresholdFilter` — per-category + overall minimum score filtering
- [x] Scoring schemas + API routes (`/matching/config`, `/jobs/{id}/score`, `/jobs/batch-score`, `/jobs/{id}/explain`, `/jobs/scored`)
- [x] Frontend `ScoreBadge` (SVG circular gauge) + `ScoreExplanationPanel`
- [x] Search results integrate score badges with batch scoring; sort-by-match button; detail page shows overall badge + explanations
- [x] 259 backend tests, 0 lint errors; frontend compiles clean

## Phase 7 — LLM Abstraction, Embeddings, Vector DB, RAG & Prompts

- [x] **BaseLLMClient** — abstract interface with `complete()` + response parsing + usage tracking
- [x] **OpenAI-compatible client** — `/chat/completions` endpoint, configurable base URL for Azure/self-hosted
- [x] **Anthropic-compatible client** — `/messages` endpoint, system message separation
- [x] **Gemini-compatible client** — `generateContent` endpoint, system instruction support
- [x] **Ollama client** — `/api/chat` endpoint for local LLMs
- [x] **OpenRouter client** — `/chat/completions` with model routing
- [x] **LLM factory** — `get_llm_client(provider)` + `list_providers()` + client lifecycle
- [x] **LLMConfig** — per-provider settings (api_key, base_url, model, timeout, retries, enabled)
- [x] **LLMCache** — in-memory TTL cache with LRU eviction, SHA256 request key, invalidation
- [x] **EmbeddingService** — text embedding across OpenAI, Ollama, Gemini providers
- [x] **VectorStore** — in-memory vector DB with cosine similarity search, top-k + min_score filtering
- [x] **RAGService** — Retrieval Augmented Generation: embed query → vector search → LLM generation with source context
- [x] **PromptRegistry** — built-in prompts (job-application-email, cover-letter, skill-based-question, interview-prep)
- [x] **PromptTemplateService** — DB-backed prompt templates with versioning, variable extraction, rendering
- [x] **Prompt versioning** — auto-increment versions, activate/deactivate, track history
- [x] **LLM API routes** (`/api/v1/llm/providers`, `/chat`, `/embed`, `/vector/add`, `/vector/search`, `/rag/query`, `/prompts/registry/*`, `/prompts/templates/*`)
- [x] Backend tests: 314 passing, 0 lint errors
- [x] Frontend compiles clean (0 TypeScript errors)

## Phase 8 — Resume Optimization & Cover Letters

- [x] **ATS Scoring** — `ResumeOptimizer` scores resumes against job descriptions (format, keyword, section, AI-readiness checks)
- [x] **Keyword Analysis** — Gap analysis identifying missing resume keywords vs job description
- [x] **ATS Resume Generation** — `ATSResumeGenerator` produces LLM-rewritten resumes optimized for ATS parsing
- [x] **Keyword Optimization** — `ResumeKeywordOptimizer` injects target keywords per section or across the full resume
- [x] **Cover Letter Generation** — `CoverLetterGenerator` creates personalized letters with company research, resume context, tone/length control
- [x] **Cover Letter Versioning** — Auto-increment versions, `is_active` flag, DB-backed CRUD
- [x] **Cover Letter Export** — PDF (Reportlab) and DOCX export with file storage
- [x] **Company Research (Phase 8 baseline)** — Basic LLM-powered company info retrieval
- [x] 75 new tests (314 → 389 total), 0 lint errors

## Phase 9 — Company Research Engine

- [x] **Company Research Engine** — `CompanyResearchService` enhanced with all profiling dimensions:
  - Industry, Products/Services, Mission, Culture
  - Recent public news, Headquarters, Company size
  - Hiring trends, Technology stack
  - Funding rounds (total, last round, date, investors)
- [x] **Summary Generation** — Natural-language summary synthesized from all research fields
- [x] **Caching** — Two-tier: in-memory `_InMemoryCache` (per-instance TTL cache) + DB persistence via `CompanyResearch` model
- [x] **CompanyResearch Model** — SQLAlchemy model with `company_name` unique index, JSON columns for lists/dicts
- [x] **API Routes** — `POST /company/research`, `GET /company/research/{name}`, `GET /company/research/{name}/summary`, `DELETE /company/research/{name}`
- [x] **Fallback Handling** — Graceful degradation when LLM unavailable (structured fallback dict with summary)
- [x] **DB Write Resiliency** — Persistence failures logged but never crash the request
- [x] 29 new tests (389 → 418 total), 0 lint errors

## Phase 10 — Interview Preparation Engine

- [x] **InterviewPrep Model** — SQLAlchemy model storing all interview prep data per user per job as JSON columns
- [x] **InterviewPrepService** — Full generation engine with LLM-driven content for all 8 categories:
  - Behavioral questions (STAR method: Situation, Task, Action, Result)
  - Technical questions (topic-tagged, difficulty-graded, with detailed answers)
  - Salary expectations (market range, recommended value, factors, negotiation tips)
  - Notice period guidance (current period, negotiability, industry standard)
  - Strengths (evidence-backed, role-relevant, categorized)
  - Weaknesses (improvement plan, positive framing, categorized)
  - Career goals (short-term, long-term, company alignment, timeline)
  - Company-specific answers (tailored Q&A from company research)
- [x] **TruthValidator** — Standalone service to validate interview answers for consistency using LLM analysis
- [x] **Context Builders** — `_build_resume_context()` and `_build_company_context()` produce structured summaries from raw snapshot/research data
- [x] **Partial Generation** — Individual sections can be toggled on/off via request flags
- [x] **LLM Fallback** — All generation methods gracefully degrade to empty results when LLM unavailable
- [x] **API Routes** — `POST /company/interview-prep/generate`, `GET /company/interview-prep`, `GET /company/interview-prep/{id}`, `DELETE /company/interview-prep/{id}`, `POST /company/interview-prep/validate-truth`
- [x] **Schemas** — 13 Pydantic models covering all question types, responses, and truth validation
- [x] 38 new tests (418 → 456 total), 0 lint errors

## Phase 11 — Browser Automation

- [x] **Browser Automation Framework** — Playwright-based browser automation with consent verification
- [x] **Site Configurations** — Greenhouse, Lever, Ashby support with field mappings and consent status
- [x] **BaseBrowserClient** — Abstract interface (navigate, fill text/textarea/checkbox/dropdown/radio, upload file, submit, screenshot)
- [x] **PlaywrightBrowserClient** — Full Playwright async implementation with headless mode, viewport config, custom user-agent
- [x] **FormFiller** — Orchestrates form field completion, resume/cover letter/certificate uploads, and submission
- [x] **BrowserAutomationService** — Retry logic with exponential backoff, error handling, screenshots on failure, logging
- [x] **Consent Verification** — Only runs on sites explicitly marked with `consent_status: permitted`
- [x] **API Routes** — `GET /company/automation/sites`, `POST /company/automation/run`, `GET /company/automation/logs`, `GET /company/automation/logs/{id}`
- [x] 36 new tests (456 → 492 total), 0 lint errors

## Phase 12 — Application Automation (Manual Apply)

- [x] **ApplicationSchedule Model** — SQLAlchemy model storing per-user schedules (daily/weekly/custom cron, timezone, max applications/day, days of week, time of day, status tracking)
- [x] **ApplicationRun Model** — SQLAlchemy model tracking individual application runs (status, job IDs, submitted count, target, error messages, timestamps)
- [x] **Notification Model** — SQLAlchemy model for in-app notifications (type, title, message, read/unread status)
- [x] **ScheduleService** — Full CRUD for schedules plus start, stop, pause, resume controls with next-run computation (daily/weekly/custom cron logic)
- [x] **ApplicationRunService** — Create runs, update status (running/completed/failed/cancelled), list with pagination
- [x] **ApplicationAutomationService** — Manual apply orchestration, scheduled apply execution, daily limit enforcement, stats aggregation
- [x] **NotificationService** — Create, list (with unread filter), mark-read (batch), unread count
- [x] **API Routes** — Full REST API under `/api/v1/apply/`:
  - `POST/GET /schedules` — CRUD for schedules
  - `POST /schedules/{id}/start|stop|pause|resume` — Schedule controls
  - `POST /runs` — Manual apply
  - `GET /runs` / `GET /runs/{id}` — Run history
  - `GET /notifications` / `GET /notifications/unread-count` / `POST /notifications/mark-read` — Notifications
  - `GET /stats` — Daily application stats
- [x] **Background Schedule Checker** — `check_and_run_due_schedules()` method finds due schedules and executes scheduled runs
- [x] **Daily Limit Enforcement** — Tracks applications per day, respects `max_applications_per_day` per schedule
- [x] **Timezone Support** — Timezone field on schedules for timezone-aware scheduling
- [x] 64 new tests (492 → 556 total), 0 lint errors

## Phase 13 — Application History & Tracking

- [x] **Application Tracking Models** — `Application` (with status, company, job details, is_active, applied_at), `ApplicationNote`, `ApplicationTag`, `ApplicationTagMapping` (composite PK), `ApplicationTimelineEvent` — all with UUID PKs, FKs, cascade deletes, and unique constraints
- [x] **Duplicate Prevention** — UniqueConstraint on `(user_id, job_posting_id)`, duplicate check returns 409 on creation
- [x] **Full CRUD API** — 22 endpoints under `/api/v1/applications/` covering applications (create/list/get/update/delete), notes (add/list), tags (CRUD + app mapping), timeline events, analytics overview, CSV export, duplicate check, search, and filter (status, company, date range, tag IDs, is_active)
- [x] **ApplicationTrackingService** — create with duplicate validation, get with joinedload, list_by_user with 8 filter params + pagination, update with timeline event on status change, cascade delete, notes CRUD, tag mapping, timeline queries
- [x] **ApplicationAnalyticsService** — `get_analytics()` computing total, status breakdown, top 10 companies, weekly/monthly counts, active count, interview rate, success rate
- [x] **ApplicationExportService** — CSV export with all application fields + tags
- [x] **Tag System** — Per-user tags with unique name constraint, hex color support, many-to-many mapping with applications
- [x] **Timeline Events** — Automatic event creation on create, status change, note added, tag added/removed
- [x] 46 new tests (556 → 604 total), 0 lint errors

## Phase 14 — Dashboard, Statistics, Charts & Reports

- [x] **Dashboard Service** — `DashboardService.get_summary()` provides aggregated overview: total/active applications, weekly/monthly counts, interviews scheduled, offers received, interview/success rates, status breakdown
- [x] **Statistics Service** — `StatisticsService.get_statistics()` computes detailed statistics for configurable periods (week/month/year) including: period totals, status breakdown, daily/weekly/monthly trend data, previous period comparison with growth percentage, top companies, interview/success rates
- [x] **Chart Service** — `ChartService` with 7 chart data endpoints:
  - `get_status_distribution()` — pie/bar chart data with color-coded statuses
  - `get_daily_trends()` — line chart data for daily application volume
  - `get_weekly_trends()` — line chart data for weekly trends
  - `get_monthly_trends()` — line chart data for monthly trends
  - `get_company_distribution()` — bar chart data for top companies
  - `get_funnel()` — funnel chart data (saved → applied → screening → interview → offer → accepted)
  - `get_daily_statistics()` — per-day statistics with status breakdown
- [x] **Report Service** — `ReportService.generate_report()` generates period-based reports (daily/weekly/monthly) in 3 formats:
  - **CSV** — Summary, status breakdown, daily breakdown, top companies, and per-application detail rows
  - **XLSX** — Multi-sheet Excel workbook (Summary, Daily Breakdown, Top Companies, Application Details) via openpyxl
  - **PDF** — Formatted PDF with tables and headings via reportlab
- [x] **API Routes** — 11 endpoints under `/api/v1/dashboard/`: summary, statistics (with period params), 5 chart endpoints, daily-statistics, and report generation (type + format param, file download response)
- [x] **Cross-dialect Compatibility** — Uses `strftime` for SQLite (testing) and `date_trunc` for PostgreSQL (production) for weekly/monthly date grouping
- [x] **Frontend-Ready Chart Data** — ChartDataResponse schema with labels, datasets, background colors, and border colors matching Chart.js conventions
- [x] 35 new tests (604 → 640 total), 0 lint errors

## Remaining for Future Phases

- [ ] Email automation
- [ ] Interview scheduling
- [ ] Template management
- [ ] Advanced reporting (custom date ranges, saved reports)

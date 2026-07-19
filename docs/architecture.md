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

## Remaining for Future Phases

- [ ] Resume parsing and analysis improvements
- [ ] Application generation
- [ ] Email automation
- [ ] Interview scheduling
- [ ] Dashboard and analytics
- [ ] Notification system
- [ ] Template management

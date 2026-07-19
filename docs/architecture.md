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
- [x] Comprehensive test suite (259 tests)

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
- [x] Backend tests (259 passing, 0 lint errors)
- [x] Frontend compiles clean (0 TypeScript errors)

## Phase 6 — Match Scoring System

- [x] `SkillExtractor` — extracts skills from job descriptions using a comprehensive tech-skills dictionary; computes skill match scores against user's profile skills
- [x] `KeywordExtractor` — extracts non-stopword keywords from job descriptions; computes keyword match scores against user's experience titles and skills
- [x] `ExperienceExtractor` — extracts required years of experience and seniority level from job descriptions; computes user's total experience years from work history; scores experience fit
- [x] `EducationExtractor` — extracts required education level and field of study; compares against user's education records; scores education fit
- [x] `CompanyAnalyzer` — checks company against user's blacklist and past employers; scores company fit
- [x] `MatchScorer` — configurable weighted scoring engine combining skill, keyword, experience, education, and company factors into a 0–1 match score; supports boost (exact title match, current company) and penalty (blacklisted) modifiers
- [x] `ThresholdFilter` — filters scores below configurable per-category and overall thresholds
- [x] Scoring schemas (`MatchScore`, `SkillScore`, `KeywordScore`, `ExperienceScore`, `EducationScore`, `CompanyScore`, `ScoreExplanation`, `ScoringConfig`, `ScoringWeights`, `ScoredJobResponse`, `BatchScoreRequest/Response`)
- [x] Scoring API routes (`/api/v1/matching/config` GET/PUT, `/jobs/{id}/score` POST, `/jobs/batch-score` POST, `/jobs/{id}/explain` POST, `/jobs/scored` GET)
- [x] Frontend `ScoreBadge` — SVG circular progress indicator with color coding (green ≥80%, yellow ≥40%, red <20%)
- [x] Frontend `ScoreExplanationPanel` — category-by-category breakdown with scores, weights, and detailed text explanations
- [x] Search results integrate score badges with batch scoring; sort-by-match button
- [x] Job detail page shows overall match badge + toggleable scoring explanation panel
- [x] Backend tests: 259 passing, 0 lint errors
- [x] Frontend compiles clean (0 TypeScript errors)

## Remaining for Phase 7

- [ ] Resume parsing and analysis
- [ ] Application generation
- [ ] Email automation
- [ ] Interview scheduling
- [ ] Dashboard and analytics
- [ ] Notification system
- [ ] Template management

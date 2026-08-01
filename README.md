# AI Job Application Agent

**Version 2.1.0** — Production-ready AI-powered job application automation platform.

Discover jobs across 30+ providers, score against your profile, generate tailored resumes and cover letters, and track applications through a unified workflow — all powered by a pluggable multi-provider AI system.

---

## Project Overview

AI Job Agent is a full-stack, AI-first job application automation platform. It combines:

- **Job discovery** across 30+ sources via a pluggable Provider SDK (discovery, portal, and ATS integrations)
- **AI-powered matching** that scores jobs against your career profile
- **Automated application generation** — tailored resumes, cover letters, and intelligent answers via a Universal Form Intelligence Engine
- **Browser automation** (Playwright) for end-to-end application submission
- **A production observability stack** — structured logging, metrics, health checks, and alerting
- **An authenticated React + TypeScript management center**

The backend follows Clean Architecture (API → Service → Repository → Database), and all AI traffic flows through a multi-provider abstraction layer supporting **OpenRouter, Ollama, OpenAI, Anthropic, and Gemini** with a versioned prompt template registry.

---

## Screenshots

*Screenshots will be added here with the v2.1.0 release assets.*

| | |
|---|---|
| *Dashboard placeholder* | *Provider Management placeholder* |
| *Resume Generator placeholder* | *Application Kanban placeholder* |

---

## Architecture

```
├── backend/              # FastAPI Python backend (Clean Architecture)
│   ├── app/
│   │   ├── api/          # API routes (controllers)
│   │   │   ├── v1/       # Versioned endpoints (ai, matching, resumes, etc.)
│   │   │   └── responses.py  # Standardized error responses
│   │   ├── ai/           # Multi-provider AI system (service, factory, prompts)
│   │   ├── core/         # Configuration, security, database, exceptions, logging
│   │   ├── middleware/   # Request ID & correlation ID middleware
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # Business logic layer
│   │   └── repositories/ # Data access layer
│   ├── alembic/          # Database migrations
│   ├── scripts/          # Seed data & utility scripts
│   └── tests/            # 3031+ pytest tests
├── frontend/             # React + TypeScript (Vite)
│   ├── src/
│   │   ├── components/   # Reusable UI components (Radix UI)
│   │   ├── pages/        # Route pages (React Router v6)
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # Frontend service modules
│   │   │   ├── provider-sdk/    # Pluggable provider SDK
│   │   │   ├── provider-management/ # Provider management
│   │   │   ├── ats/             # ATS provider integrations
│   │   │   ├── discovery/       # Job discovery engine
│   │   │   ├── matching/        # AI matching engine
│   │   │   ├── application-engine/ # Application automation
│   │   │   ├── browser/         # Browser automation
│   │   │   ├── authentication/  # Auth service layer
│   │   │   ├── production/      # Observability & ops
│   │   │   ├── orchestration/   # Workflow orchestration
│   │   │   └── routing/         # Provider routing
│   │   └── types/        # TypeScript type definitions
│   └── tests/            # 779+ vitest tests
├── docs/                 # Full documentation repository
└── docker-compose.yml    # Development & production stack
```

## Prerequisites

- Docker Desktop 4+ (Docker Compose v2 included)
- Python 3.11+ (used only by the cross-platform launcher; no Python packages need to be installed locally)

On Linux, install Docker Engine with the Compose plugin and ensure your user can run `docker` without `sudo`.

## Start the development environment

The launcher is the supported way to run the project. It starts Docker Desktop when possible, reuses or recovers the project's containers, waits for PostgreSQL, applies Alembic migrations, waits for both application health checks, and opens the browser once.

```bash
git clone <repository-url>
cd AI-JOB-AGENT
```

Windows PowerShell:

```powershell
.\run.ps1
```

Windows Command Prompt (or double-click `run.cmd`):

```bat
run.cmd
```

Linux/macOS:

```bash
./run
```

The first run creates `.env` from `backend/.env.example` and replaces the placeholder `APP_SECRET_KEY`. Docker handles Python, Node, PostgreSQL, and all application dependencies inside containers.

Useful commands:

```text
./status                 # check Docker, containers, health endpoints, and ports
./stop                   # stop app and database containers, preserving their data
./stop --keep-database   # stop only app containers
./restart                # graceful stop followed by a fresh health-checked start
./run --no-open          # do not open a browser
./run --debug            # show Docker command output for troubleshooting
```

Use the corresponding `*.ps1` or `*.cmd` command on Windows. The running application is normally available at `http://localhost`, with API docs at `http://localhost:8000/docs`. The launcher reads the actual Compose port binding before printing final URLs.

### Launcher architecture and operational behavior

`scripts/launcher.py` is the orchestration layer; `scripts/launcher/config.py`, `console.py`, and `errors.py` keep configuration, output, and error policy isolated. `run`, `stop`, `restart`, and `status` are thin Bash, PowerShell, and batch entry points. The orchestration layer owns Docker/container management, database migration, service health checks, browser opening, and port checks. It never uses fixed startup delays: database readiness is checked with `pg_isready`, backend readiness with `/health`, and frontend readiness with `/health`.

If a named project container is unhealthy, the launcher attempts one restart before failing. It shows the last service logs when a service exits or a readiness deadline expires. It does not kill an unrelated process that owns ports 80, 8000, or 5432; it instead reports the conflict and suggests changing the Compose mapping or stopping the owning process. Run with `--debug` for underlying Docker command output.

Known limitation: automatic Docker Desktop launch is best-effort and depends on the normal Docker Desktop install location and OS service permissions. On Linux, the launcher never invokes `sudo`; start the Docker service manually if policy prevents the user service from starting it.

## Manual Docker workflow (advanced)

```bash
cp backend/.env.example backend/.env
export APP_SECRET_KEY=$(openssl rand -hex 32)
docker compose up -d
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Direct host development (advanced)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
# Backend (3031+ tests)
cd backend && pytest --cov=app

# Frontend (779+ tests)
cd frontend && npm test

# Full backend test suite (excluding PostgreSQL-dependent tests)
cd backend && python -m pytest tests/ --ignore=tests/test_database_models.py --ignore=tests/test_repositories.py -v
```

## Build & Lint

```bash
# Frontend build
cd frontend && npm run build

# Backend lint
cd backend && ruff check app tests

# Frontend lint & typecheck
cd frontend && npm run lint && npx tsc --noEmit
```

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, structlog
- **Frontend:** React 18, TypeScript, Vite, React Router v6, TanStack Query, Radix UI, Tailwind CSS v4
- **AI:** Multi-provider (OpenRouter, Ollama, OpenAI, Anthropic, Gemini), prompt templates, RAG
- **Database:** PostgreSQL 16
- **Browser:** Playwright
- **Infrastructure:** Docker, Docker Compose, Nginx
- **CI/CD:** GitHub Actions

## Provider System

The system fetches jobs from **30+ sources** using a pluggable provider framework:

### Discovery Providers (10)
LinkedIn, Indeed, Naukri, Foundit, Wellfound, Y Combinator, Google Jobs, RemoteOK, We Work Remotely, Company Career Pages

### Portal Providers (7)
Internshala, Unstop, Freshersworld, LinkedIn (portal), Indeed (portal), Company Career Pages, Google Jobs

### ATS Providers (10)
Greenhouse, Lever, Ashby, Workday, SmartRecruiters, BambooHR, iCIMS, Jobvite, Oracle Recruiting, SAP SuccessFactors

### Additional (3+)
LinkedIn Easy Apply, Wellfound Easy Apply, Y Combinator Apply

Each provider implements the Provider SDK with shared rate limiting, retries, logging, metrics, error handling, and normalization.

## Application Engine

The Universal Form Intelligence Engine powers automated job applications:
- **Field Detection:** Automatic form field detection on any job board
- **Profile Mapping:** Smart mapping of user profile data to application fields
- **Answer Engine:** Context-aware answer generation using AI
- **Multi-Step Coordination:** Wizard-based multi-page form handling
- **Checkpoints & Recovery:** Auto-save and resume interrupted applications
- **Approval Workflow:** Review-before-submit for critical applications
- **Validation Engine:** Rules-based and AI-assisted field validation

## Features

### Core Platform
- JWT authentication with refresh token rotation
- Profile management (education, experience, skills, projects, certifications, languages)
- Blacklisted companies tracking
- 30+ job provider integrations
- Rate limiting with token-bucket algorithm (outbound provider requests)
- Retry & error handling (exponential backoff)
- Job normalization & deduplication (hash-based)
- Job search (keyword, location, remote, salary, type, experience filters)
- Background refresh via task queue
- In-memory TTL cache for search results

### AI & Intelligence
- Multi-provider AI abstraction (OpenRouter, Ollama, OpenAI, Anthropic, Gemini)
- Prompt template management with versioning
- Structured output generation
- Embeddings & vector database (cosine similarity)
- RAG pipeline with context-aware AI answers
- Company research engine with deep profiling
- Interview preparation (STAR method, technical Q&A)

### Resume & Cover Letter
- ATS-optimized resume generation
- Resume keyword gap analysis
- Multiple template support with PDF/DOCX export
- Personalized cover letter generation
- Cover letter versioning & export
- **Resume strategy system** — per-user strategy (`use existing` / `tailor` / `generate` / `ask each time`), deterministic best-resume selection scoring, and a save policy for AI-generated resumes (never / only when submitted / always)
- **AI credit reuse** — tailoring or generating the same job with an unchanged profile reuses the previous result instead of spending credits again

### Job Matching
- Configurable weighted scoring (skills, experience, education, company fit)
- Batch scoring with threshold filtering
- Visual score badges with detailed explanations

### Application Automation
- Manual & automated scheduling (daily/weekly/custom cron)
- Pause/resume/stop controls
- Configurable daily application limits
- Application history with full CRUD
- Timeline, notes, tags, status tracking
- Duplicate prevention
- Analytics (interview/success rates, trends, top companies)

### Dashboard & Reports
- Real-time aggregated statistics
- Interactive charts (status, trends, funnel)
- Exportable reports (CSV, XLSX, PDF)
- Period comparison with growth rates

### Observability
- Structured logging with correlation IDs
- Metrics collection and aggregation
- Health checks and alerting
- Performance sampling
- Recovery analytics
- Diagnostics & maintenance

## Production Hardening (Sprint 4 / v2.1.0)

The following production-readiness improvements were completed in Sprint 4:

| Feature | Description |
|---|---|
| **Standardized Error Responses** | All endpoints return `{"success": false, "error": {"code", "message", "details", "request_id"}}` via `AppError` hierarchy |
| **Request/Correlation ID** | `RequestIDMiddleware` assigns UUID per request, propagated through logs and response headers |
| **Health & Readiness** | `GET /health` (status, version, timestamp) and `GET /ready` (database, AI, providers, config) |
| **Structured Logging** | JSON log output (`LOG_FORMAT=json`), `request_id` injected into every event; no secrets logged |
| **Security Hardening** | JWT with `jti` claim, CORS restricted to configured origins, prompt injection protection, bcrypt hashing |
| **Workflow Integration Tests** | 20 tests covering 5 critical workflows |
| **Authentication Tests** | 15 parametrized tests covering 14 protected routes |
| **Pydantic Validation Tests** | 35 tests covering field validation across all feature schemas |
| **Seed Data** | `python -m scripts.seed` creates demo user, career profile, skills, jobs, AI config |
| **Makefile** | `install`, `test`, `test-cov`, `lint`, `format`, `docker`, `seed`, `clean` targets |

## Configuration

Key environment variables:

```
# Backend
APP_SECRET_KEY=<random-32-hex>
DATABASE_URL=postgresql://user:pass@db:5432/ai_job_agent
OPENROUTER_API_KEY=<key>

# Frontend
VITE_API_URL=http://localhost:8000/api/v1

# AI Providers
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
GOOGLE_API_KEY=<key>
OLLAMA_BASE_URL=http://localhost:11434
```

## Project Stats (v2.1.0)

- **Backend Tests:** 3031 passed
- **Frontend Tests:** 779 passed
- **Total Tests:** 3810
- **Frontend Source Files:** 242 TypeScript files
- **Service Modules:** 17 frontend service directories
- **Job Providers:** 30+
- **AI Providers:** 5 (OpenRouter, Ollama, OpenAI, Anthropic, Gemini)
- **AI Features:** 15 feature areas (16 registered functions)
- **Prompt Templates:** 25 (versioned registry)
- **API Endpoints:** 136 versioned v1 routes
- **Documentation Files:** 69
- **Frontend Build Time:** ~7.5s
- **Backend Test Time:** ~107s
- **Frontend Test Time:** ~23s

## Documentation

Full documentation is available in the `docs/` directory:

- [Architecture](docs/architecture/)
- [API](docs/api/)
- [Providers](docs/providers/)
- [Deployment](docs/deployment/)
- [Security](docs/security/)
- [Database](docs/database/)
- [Testing](docs/testing/)
- [Operations](docs/operations/)
- [Frontend](docs/frontend/)
- [Backend](docs/backend/)
- [AI](docs/ai/)
- [Product](docs/product/)

## Roadmap

- [ROADMAP.md](ROADMAP.md) — completed v2.1.0 scope, future ideas, and known technical debt
- [RELEASE_NOTES_v2.1.0.md](RELEASE_NOTES_v2.1.0.md) — full release notes
- [CHANGELOG.md](CHANGELOG.md) — change log (Keep a Changelog format)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup,
testing, coding standards, commit conventions, and the pull request process.

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md) — how to report vulnerabilities

## Support

- **Issues:** use GitHub Issues for bugs and feature requests (search first for duplicates)
- **Security issues:** report privately per [SECURITY.md](SECURITY.md)
- **Docs:** the `docs/` directory covers architecture, API, database, deployment, operations, and AI
- **Discussions:** use GitHub Discussions for questions and ideas

## License

This project is licensed under the [MIT License](LICENSE).

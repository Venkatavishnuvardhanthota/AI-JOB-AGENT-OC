# AI Job Application Agent

**Version 2.1.0** — Production-ready AI-powered job application automation platform.

Discover jobs across 30+ providers, score against your profile, generate tailored resumes and cover letters, and track applications through a unified workflow — all powered by a pluggable multi-provider AI system.

---

## Architecture

```
├── backend/              # FastAPI Python backend (Clean Architecture)
│   ├── app/
│   │   ├── api/          # API routes (controllers)
│   │   ├── core/         # Configuration, security, database
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # Business logic layer
│   │   └── repositories/ # Data access layer
│   ├── alembic/          # Database migrations
│   └── tests/            # 2785+ pytest tests
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

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- PostgreSQL 16 (if running without Docker)

## Quick Start (Docker)

```bash
cp backend/.env.example backend/.env
export APP_SECRET_KEY=$(openssl rand -hex 32)
docker compose up -d
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Development Setup

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
# Backend (2785+ tests)
cd backend && pytest --cov=app

# Frontend (779+ tests)
cd frontend && npm test
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
- Rate limiting with token-bucket algorithm
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

- **Backend Tests:** 2785 passed
- **Frontend Tests:** 779 passed
- **Total Tests:** 3564
- **Frontend Source Files:** 242 TypeScript files
- **Service Modules:** 17 frontend service directories
- **Job Providers:** 30+
- **AI Providers:** 5 (OpenRouter, Ollama, OpenAI, Anthropic, Gemini)
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

## License

See [LICENSE.txt](docs/LICENSE.txt).

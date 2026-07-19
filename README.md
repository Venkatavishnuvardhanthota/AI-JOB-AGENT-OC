# AI Job Application Agent

A production-ready AI-powered job application automation system built with FastAPI, React, and PostgreSQL.

## Architecture

```
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── api/      # API routes (controllers)
│   │   ├── core/     # Configuration, security, database
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic validation schemas
│   │   ├── services/ # Business logic layer
│   │   └── repositories/ # Data access layer
│   ├── alembic/      # Database migrations
│   └── tests/        # Pytest test suite
├── frontend/         # React + TypeScript frontend
│   ├── src/
│   │   ├── api/      # API client
│   │   ├── components/ # UI components
│   │   ├── hooks/    # Custom React hooks
│   │   ├── pages/    # Route pages
│   │   ├── types/    # TypeScript type definitions
│   │   └── utils/    # Utility functions
│   └── tests/        # Vitest test suite
├── docs/             # Architecture documentation
└── docker-compose.yml # Development & production stack
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- PostgreSQL 16 (if running without Docker)

## Quick Start (Docker)

```bash
# Copy environment configuration
cp backend/.env.example backend/.env

# Set a secure secret key
export APP_SECRET_KEY=$(openssl rand -hex 32)

# Start all services
docker compose up -d

# Access the application
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

# Copy and edit environment
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start development server
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
# Backend
cd backend && pytest --cov=app

# Frontend
cd frontend && npm test
```

## Linting & Formatting

```bash
# Backend
cd backend && ruff check app tests && black --check app tests

# Frontend
cd frontend && npm run lint && npm run format
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Frontend**: React 18, TypeScript, Vite, React Router v6
- **Database**: PostgreSQL 16
- **Infrastructure**: Docker, Docker Compose, Nginx
- **CI/CD**: GitHub Actions

## Provider Framework

The system fetches jobs from **17 sources** using a pluggable provider framework:

**Global job boards:** LinkedIn, Indeed, Google Jobs, Wellfound, RemoteOK, We Work Remotely, Y Combinator
**ATS platforms:** Greenhouse, Lever, Ashby, Workday
**Indian job portals:** Naukri, Foundit, Internshala, Unstop, Freshersworld
**Career pages:** Company Career Pages (configurable scraping)

Each provider implements `BaseProvider` and reuses shared rate limiting, retries, logging, metrics, error handling, and normalization. See [docs/providers.md](docs/providers.md) for full documentation.

## Features

- **Authentication:** JWT-based register, login, profile management
- **Profile Management:** Education, experience, skills, projects, certifications, languages, resume upload
- **Blacklisted Companies:** Track companies to exclude from applications
- **17 Job Provider Integrations:** LinkedIn, Indeed, Wellfound, Greenhouse, Lever, Ashby, Workday, Google Jobs, RemoteOK, We Work Remotely, Career Pages, Y Combinator, Naukri, Foundit, Internshala, Unstop, Freshersworld
- **Rate Limiting:** Token-bucket with configurable rates per provider
- **Retry & Error Handling:** Exponential backoff, structured error types
- **Job Normalization & Deduplication:** Hash-based dedup with configurable strategies
- **Job Search:** Keyword, location, remote, salary range, job type, and skills filters with pagination
- **Job Storage:** Full CRUD with PostgreSQL, saved jobs tracking
- **Background Refresh:** Async job search via task queue with status polling
- **Caching:** In-memory TTL cache for search results
- **Frontend Pages:** Job search with filters, job detail view, saved jobs list
- **Match Scoring:** Skill, keyword, experience, education, and company fit scoring with configurable weights and thresholds
- **Score Visualization:** SVG circular progress badges with color coding and detailed explanation panels
- **Batch Scoring:** Score multiple jobs at once; sort search results by match score
- **Threshold Filtering:** Filter jobs by minimum overall and per-category match scores
- **Logging & Metrics:** Structured logging (structlog), per-provider metrics, health checks
- **Test Coverage:** 259 backend tests, 0 lint errors

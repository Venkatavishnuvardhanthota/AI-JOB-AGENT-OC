# AI Job Agent Version 2.1.0 — Release Notes

**Release Date:** 2026-07-28

**Version:** 2.1.0

See [RELEASE_NOTES_v2.1.0.md](RELEASE_NOTES_v2.1.0.md) for the full v2.1.0 release notes.

---

# AI Job Agent Version 2.0.0 — Release Notes

**Release Date:** 2026-07-24

**Version:** 2.0.0

---

## Overview

AI Job Agent V2 is a production-ready, AI-powered job application automation platform. It discovers jobs across 17+ sources, scores them against your profile, generates tailored resumes and cover letters, and tracks applications through a unified workflow.

This is the initial public release.

---

## Features

### Core Platform
- Modular FastAPI backend with Clean Architecture
- React + TypeScript frontend with Radix UI and TanStack Query
- PostgreSQL database with SQLAlchemy 2.0 ORM
- Docker and Docker Compose deployment

### AI & Intelligence
- Multi-provider AI abstraction (OpenRouter, Ollama)
- Prompt template management with rendering and parsing
- Structured output generation
- Intelligence layer for analytics, recommendations, learning, and optimization
- A/B experimentation engine
- Weighted scoring engine (resume, application, provider, job, workflow quality)

### Career Profile & Resume
- Profile management (education, experience, skills, projects, certifications, languages)
- Resume generation, versioning, and ATS optimization
- Multiple template support
- PDF/DOCX export

### Job Discovery (17+ Providers)
- Global: LinkedIn, Wellfound, Y Combinator
- ATS: Greenhouse, Lever, Ashby, Workday, SmartRecruiters, BambooHR, Recruitee
- Indian: Naukri, Foundit, Internshala, Unstop, Freshersworld
- Rate limiting, retry logic, deduplication, normalization

### Job Matching
- Configurable weighted scoring (skills, experience, education, company fit)
- Batch scoring and threshold filtering
- Visual score badges with detailed explanations

### Applications
- Application preparation, submission, and tracking
- Timeline and status management
- Duplicate prevention
- Ownership-enforced authorization

### Browser Automation
- Playwright-based browser management
- Screenshots, downloads, cookie management
- Multi-context and multi-session support

### Security
- JWT authentication with refresh token rotation
- Bcrypt password hashing
- Password strength validation
- Application-level authorization (ownership checks)
- Security headers in nginx

### Deployment
- Docker Compose with health checks
- Production nginx configuration with caching and compression
- Comprehensive environment variable configuration
- Non-root container execution

### Testing
- 488+ backend unit tests
- Frontend component tests
- 95 intelligence-specific tests

### Documentation
- Complete documentation repository (architecture, API, database, security, deployment, operations)
- Architecture Decision Records (ADRs)
- Security checklist and deployment guide

---

## System Requirements

- **Backend:** Python 3.11+, PostgreSQL 16
- **Frontend:** Node.js 20+, Modern web browser
- **Docker:** Docker Compose v2+ (optional)

---

## Quick Start

```bash
# Clone and configure
cp backend/.env.example backend/.env
# Edit backend/.env with your settings

# Start with Docker
docker compose up -d

# Access
# Frontend: http://localhost
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

See [docs/deployment/Deployment-Guide.md](docs/deployment/Deployment-Guide.md) for full instructions.

---

## Known Limitations

- Password reset email sending requires SMTP configuration
- Browser automation requires Playwright system dependencies in Docker
- Frontend test coverage is a foundation (9 tests) — expansion planned
- Some ATS provider integrations are in beta
- No WebSocket support for real-time updates

---

## Future Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full v2.1–v3.0 roadmap.

---

## License

See [LICENSE.txt](docs/LICENSE.txt).

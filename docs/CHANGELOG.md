# Changelog

All notable changes to **AI Job Agent Version 2** will be documented in this file.

This project follows the principles of **Keep a Changelog** and **Semantic Versioning (SemVer)**.

- Format: https://keepachangelog.com/
- Versioning: https://semver.org/

---

# [Unreleased]

## Added

- Placeholder for upcoming features.
- Future provider integrations.
- Additional AI model support.
- Performance improvements.
- UI enhancements.

## Changed

- No unreleased changes yet.

## Deprecated

- None.

## Removed

- None.

## Fixed

- None.

## Security

- None.

---

# [2.0.0] - 2026-07-24

## Overview

Initial public release of **AI Job Agent Version 2**.

This release introduces a modular, AI-powered job application platform capable of discovering jobs, evaluating opportunities, generating tailored application materials, and tracking applications through a unified workflow.

---

## Added

### Core Platform

- Modular FastAPI backend
- React + TypeScript frontend
- PostgreSQL database
- SQLAlchemy ORM
- Alembic migrations
- Docker support
- Docker Compose support

---

### AI

- AI Orchestrator
- Prompt management
- Model routing
- Output validation
- AI testing framework
- Multi-provider abstraction

Supported providers:

- OpenRouter
- Ollama

---

### Career Profile

- Career profile management
- Skills management
- Experience management
- Education management
- Preferences
- Resume metadata

---

### Resume

- Resume generation
- ATS optimization
- Resume versioning
- Resume storage
- Resume templates
- PDF generation support

---

### Job Discovery

- Provider interface
- Job normalization
- Duplicate detection
- Match scoring
- Search filtering

---

### Job Applications

- Application tracking
- Status management
- Notes
- Timeline
- Duplicate prevention

---

### Frontend

- Dashboard
- Resume management
- Job search
- Applications page
- Settings
- Authentication pages

---

### Backend

- REST API
- Service architecture
- Repository pattern
- Background workers
- Scheduler

---

### Security

- JWT authentication
- Authorization
- Input validation
- Secret management
- Security checklist

---

### Testing

- Backend tests
- Frontend tests
- AI tests
- Integration testing strategy

---

### Deployment

- Deployment guide
- Infrastructure documentation
- Deployment pipeline
- Docker deployment

---

### Operations

- Operations runbook
- Monitoring strategy
- Maintenance procedures

---

### Documentation

Complete documentation repository including:

- Product
- Architecture
- API
- Database
- Backend
- Frontend
- AI
- Providers
- Testing
- Security
- Deployment
- Operations

---

## Changed

- Production-ready release
- Version bumped from 0.1.0 to 2.0.0
- Production database connection pool configuration
- Graceful browser cleanup on shutdown
- Improved nginx security headers and caching
- Production logging defaults
- Expanded environment configuration template

---

## Fixed

- Application endpoints now verify user ownership (security fix)
- JWT tokens now include `iat` and `jti` claims
- Password reset endpoints now function correctly (no longer stubs)
- nginx health check endpoint corrected

---

## Security

Implemented:

- JWT authentication
- Secure configuration
- Secret management
- HTTPS-ready deployment
- Security monitoring
- Operational security procedures

---

# Semantic Versioning Policy

The project follows:

```
MAJOR.MINOR.PATCH
```

Examples:

```
2.0.0

2.1.0

2.1.3

3.0.0
```

Definitions:

- **MAJOR** — incompatible API or architecture changes.
- **MINOR** — new backward-compatible features.
- **PATCH** — backward-compatible bug fixes.

---

# Release Checklist

Before every release:

- Documentation updated
- Tests passing
- Security review completed
- Database migrations verified
- Deployment validated
- Changelog updated
- Version tag created

---

# Release Notes Template

For future releases:

```markdown
# [x.y.z] - YYYY-MM-DD

## Added

-

## Changed

-

## Deprecated

-

## Removed

-

## Fixed

-

## Security

-
```

---

End of Document
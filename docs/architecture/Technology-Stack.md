# Technology Stack

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Technology Stack |
| Version | 2.0 |
| Status | Approved |
| Related Documents | System-Architecture.md, Deployment-Architecture.md, Architecture-Decisions.md |

---

# Purpose

This document defines the approved technology stack for AI Job Agent Version 2.

It establishes the frameworks, libraries, languages, tools, and infrastructure components used throughout the project. Technology selections are intended to maximize maintainability, scalability, developer productivity, and long-term support.

---

# Design Principles

Technology choices should satisfy the following goals:

- Production-ready
- Open-source where practical
- Strong community support
- Long-term maintainability
- Type safety where available
- Excellent documentation
- Cross-platform compatibility
- AI-provider independence

---

# Frontend Stack

| Technology | Purpose |
|------------|---------|
| React | User interface |
| TypeScript | Static typing |
| Vite | Build tool and development server |
| React Router | Client-side routing |
| TanStack Query | Server-state management and caching |
| React Hook Form | Form management |
| Zod | Runtime schema validation |
| Tailwind CSS | Utility-first styling |
| shadcn/ui | Reusable UI components |
| Recharts | Charts and analytics visualizations |

---

# Backend Stack

| Technology | Purpose |
|------------|---------|
| Python | Primary backend language |
| FastAPI | REST API framework |
| Pydantic | Data validation |
| SQLAlchemy | ORM |
| Alembic | Database migrations |
| Uvicorn | ASGI server |
| HTTPX | HTTP client for external services |

---

# Database

| Technology | Purpose |
|------------|---------|
| PostgreSQL | Primary relational database |

Design goals:

- ACID compliance
- Strong indexing support
- Mature ecosystem
- Transactional consistency

---

# AI Stack

| Technology | Purpose |
|------------|---------|
| OpenRouter | Cloud model gateway |
| Ollama | Local model execution |
| AI Abstraction Layer | Provider independence |
| JSON Schema Validation | Structured AI output validation |

Supported design:

- Multiple providers
- Multiple models
- Fallback routing
- Retry logic
- Provider failover

---

# Browser Automation

| Technology | Purpose |
|------------|---------|
| Playwright | Browser automation |

Responsibilities:

- Authentication (where supported)
- Job application workflows
- Form completion
- File uploads
- Diagnostics on failure

---

# Background Processing

| Technology | Purpose |
|------------|---------|
| Async Python Tasks | Long-running operations |
| Scheduler | Scheduled automation |
| Worker Processes | AI and browser automation execution |

---

# Authentication

Recommended technologies:

- JWT for access tokens
- Secure password hashing
- Role-based authorization (future extensibility)

---

# File Handling

Supported document types:

- PDF
- DOCX (future)
- TXT (where applicable)

Generated outputs:

- ATS-optimized resumes
- Cover letters
- Exported profile data

---

# Development Tools

| Tool | Purpose |
|------|---------|
| VS Code | Primary IDE |
| Git | Version control |
| GitHub | Source repository |
| Docker | Containerization |
| Docker Compose | Local multi-service development |
| OpenCode | AI-assisted development |

---

# Testing Stack

| Technology | Purpose |
|------------|---------|
| Pytest | Backend testing |
| Playwright Test | End-to-end testing |
| React Testing Library | Frontend component testing |

---

# Code Quality

Recommended tools:

- Ruff (Python linting)
- Black (Python formatting)
- ESLint (TypeScript linting)
- Prettier (Frontend formatting)

---

# Logging & Monitoring

Recommended technologies:

- Structured JSON logging
- Prometheus-compatible metrics (future)
- Grafana dashboards (future)

---

# Deployment

Recommended runtime:

- Docker containers
- Nginx or Traefik reverse proxy
- Linux production environment

---

# External Integrations

Supported categories:

- AI providers
- Job providers
- Email services
- Object storage (future)

All integrations must be implemented behind adapters to avoid coupling business logic to vendor-specific APIs.

---

# Version Policy

- Prefer stable releases over experimental versions.
- Upgrade dependencies regularly after compatibility testing.
- Avoid pinning to unsupported framework versions.

---

# Technology Evaluation Criteria

New technologies should be evaluated against:

- Community support
- Documentation quality
- Security history
- Long-term maintenance
- Performance
- Licensing
- Compatibility with existing architecture

---

# Related Documents

- System-Architecture.md
- Deployment-Architecture.md
- Architecture-Decisions.md
- Module-Architecture.md

---

End of Document
# Backend Architecture

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Backend Architecture |
| Version | 2.0 |
| Status | Approved |
| Related Documents | System-Architecture.md, Module-Architecture.md, Services.md, Repositories.md |

---

# Purpose

This document defines the internal backend architecture for AI Job Agent Version 2.

It establishes:

- Project structure
- Layered architecture
- Module boundaries
- Dependency Injection
- Request lifecycle
- Background processing
- Error handling strategy
- Configuration management
- Coding conventions

This document is the primary implementation blueprint for the FastAPI backend.

---

# Architecture Goals

The backend shall be:

- Modular
- Testable
- Scalable
- Maintainable
- Provider-independent
- AI-provider independent
- Secure
- Easy to extend
- Production ready

---

# Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend language |
| FastAPI | REST API |
| SQLAlchemy | ORM |
| Alembic | Database migrations |
| Pydantic | Validation |
| PostgreSQL | Database |
| HTTPX | External API client |

---

# High-Level Architecture

```text
                HTTP Request
                      │
                      ▼
              FastAPI Router
                      │
                      ▼
          Request Validation
                      │
                      ▼
              Authentication
                      │
                      ▼
                Service Layer
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
 Repository Layer          AI Orchestrator
         │                         │
         ▼                         ▼
 PostgreSQL Database        AI Providers
         │
         ▼
     HTTP Response
```

Business logic must never reside in routers.

---

# Project Structure

```text
backend/

├── app/
│
├── api/
│   ├── auth/
│   ├── profile/
│   ├── resumes/
│   ├── jobs/
│   ├── applications/
│   └── admin/
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── dependencies.py
│   ├── logging.py
│   └── exceptions.py
│
├── services/
│
├── repositories/
│
├── models/
│
├── schemas/
│
├── providers/
│
├── ai/
│
├── workers/
│
├── scheduler/
│
├── utils/
│
└── tests/
```

Each directory has a single responsibility.

---

# Layered Architecture

## API Layer

Responsibilities:

- Route definitions
- Request parsing
- Response serialization
- Authentication hooks

The API layer must not contain business logic.

---

## Service Layer

Responsibilities:

- Business rules
- Workflow orchestration
- Validation beyond schema checks
- Transaction coordination

Services coordinate repositories and external providers.

---

## Repository Layer

Responsibilities:

- Database access
- CRUD operations
- Query optimization
- Transaction support

Repositories abstract persistence from business logic.

---

## Provider Layer

Responsibilities:

- External job providers
- AI providers
- Email providers
- Future third-party integrations

All providers implement defined interfaces.

---

## AI Layer

Responsibilities:

- Prompt construction
- Provider routing
- Retry logic
- Output validation
- Response normalization

The rest of the application interacts only with this abstraction.

---

# Request Lifecycle

```text
Client
   │
   ▼
Router
   │
   ▼
Authentication
   │
   ▼
Validation
   │
   ▼
Service
   │
   ▼
Repository
   │
   ▼
Database
   │
   ▼
Service
   │
   ▼
Response Model
   │
   ▼
Client
```

---

# Dependency Injection

Dependencies should be injected rather than instantiated directly.

Examples include:

- Database sessions
- Current user
- Configuration
- Repositories
- Services
- AI provider clients

Benefits:

- Easier testing
- Loose coupling
- Improved maintainability

---

# Configuration Management

Configuration should be environment-driven.

Typical settings include:

- Database URL
- API keys
- AI provider configuration
- Scheduler settings
- Logging level
- File storage paths
- Security settings

Configuration must not be hardcoded.

---

# Background Processing

Long-running tasks should execute outside the request-response cycle.

Examples:

- Resume generation
- Company research
- Job discovery
- Browser automation
- Scheduled jobs
- Notifications

Background workers should update task status for client visibility.

---

# Transaction Management

Transactions should be:

- Atomic
- Consistent
- Isolated
- Durable (ACID)

Business operations involving multiple database changes should commit only after all validations succeed.

---

# Error Handling

Errors should be categorized as:

- Validation errors
- Authentication errors
- Authorization errors
- Business rule violations
- Provider failures
- AI failures
- Database failures
- Unexpected internal errors

Internal implementation details should not be exposed to clients.

---

# Logging

Structured logs should include:

- Timestamp
- Request ID
- User ID (when available)
- Module
- Operation
- Duration
- Outcome

Sensitive information must never be logged.

---

# Security

The backend shall enforce:

- Authentication
- Authorization
- Input validation
- Output sanitization where appropriate
- HTTPS
- Secure password hashing
- Rate limiting
- Audit logging

---

# Module Communication

Modules communicate through public service interfaces only.

Allowed:

```text
API
 ↓
Service
 ↓
Repository
```

Not allowed:

```text
Router
 ↓
Database

Service
 ↓
Another Module's Database

Repository
 ↓
AI Provider
```

---

# Coding Standards

Backend code should:

- Follow PEP 8
- Use type hints
- Prefer composition over inheritance
- Keep functions focused
- Avoid global mutable state
- Use descriptive names
- Include docstrings for public APIs

---

# Testing Strategy

The backend should support:

- Unit tests
- Integration tests
- API tests
- Provider mocks
- AI provider mocks
- Database transaction tests

Each layer should be testable in isolation.

---

# Performance Guidelines

The backend should:

- Minimize database queries
- Avoid N+1 query problems
- Use pagination for large collections
- Execute long-running work asynchronously
- Cache reusable data where appropriate

---

# Observability

Operational visibility should include:

- Health endpoints
- Metrics
- Structured logs
- Error tracking
- Background task monitoring
- Database monitoring

---

# Acceptance Criteria

The backend architecture is considered complete when:

- Business logic is isolated in services.
- Database access occurs only through repositories.
- External providers are abstracted behind interfaces.
- Background work is asynchronous where appropriate.
- Configuration is environment-based.
- All layers are independently testable.

---

# Related Documents

- System-Architecture.md
- Module-Architecture.md
- Services.md
- Repositories.md
- Background-Jobs.md
- Error-Handling.md

---

End of Document
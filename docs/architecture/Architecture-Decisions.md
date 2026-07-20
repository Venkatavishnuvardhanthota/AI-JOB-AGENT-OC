# Architecture Decision Records (ADR)

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Architecture Decision Records |
| Version | 2.0 |
| Status | Approved |
| Related Documents | System-Architecture.md, Module-Architecture.md |

---

# Purpose

This document records significant architectural decisions made for AI Job Agent Version 2.

Each Architecture Decision Record (ADR) documents:

- Context
- Decision
- Alternatives Considered
- Consequences
- Status

Architectural decisions are intended to remain stable over time. If a decision changes, a new ADR should supersede the previous one rather than editing history.

---

# ADR Index

| ADR | Title | Status |
|------|-------|--------|
| ADR-001 | Clean Architecture | Accepted |
| ADR-002 | FastAPI Backend | Accepted |
| ADR-003 | React Frontend | Accepted |
| ADR-004 | PostgreSQL Database | Accepted |
| ADR-005 | Repository Pattern | Accepted |
| ADR-006 | Provider Adapter Pattern | Accepted |
| ADR-007 | AI Abstraction Layer | Accepted |
| ADR-008 | Playwright Automation | Accepted |
| ADR-009 | Background Scheduler | Accepted |
| ADR-010 | Immutable Resume Versioning | Accepted |
| ADR-011 | Career Profile as Source of Truth | Accepted |
| ADR-012 | UUID Primary Keys | Accepted |
| ADR-013 | Stateless REST API | Accepted |
| ADR-014 | Asynchronous AI Workflows | Accepted |
| ADR-015 | Configuration via Environment | Accepted |

---

# ADR-001 — Clean Architecture

## Status

Accepted

## Context

The project contains multiple domains including AI orchestration, browser automation, scheduling, resume generation, and job discovery. Without clear boundaries, these concerns would become tightly coupled and difficult to maintain.

## Decision

Adopt **Clean Architecture** with distinct layers:

- Presentation
- API
- Application
- Domain
- Infrastructure

Dependencies must always point inward toward the domain layer.

## Alternatives Considered

- Layered MVC
- Monolithic service layer
- Feature-first architecture without domain separation

## Consequences

### Positive

- Improved maintainability
- Easier testing
- Clear dependency boundaries
- Better long-term scalability

### Negative

- More initial boilerplate
- Additional abstractions for small features

---

# ADR-002 — FastAPI Backend

## Status

Accepted

## Context

The backend requires high performance, strong typing, automatic API documentation, and asynchronous capabilities.

## Decision

Use **FastAPI** as the primary backend framework.

## Alternatives Considered

- Django
- Flask
- Express.js
- NestJS

## Consequences

### Positive

- Native async support
- Automatic OpenAPI generation
- Strong validation with Pydantic
- Excellent Python ecosystem integration

### Negative

- Team members must understand async programming concepts

---

# ADR-003 — React Frontend

## Status

Accepted

## Context

The application requires a responsive single-page interface with reusable components and strong TypeScript support.

## Decision

Use:

- React
- TypeScript
- Vite

## Alternatives Considered

- Angular
- Vue
- Next.js
- Svelte

## Consequences

### Positive

- Large ecosystem
- Strong developer tooling
- Type safety
- Component reuse

---

# ADR-004 — PostgreSQL Database

## Status

Accepted

## Context

The system stores structured relational data including users, resumes, applications, providers, schedules, and logs.

## Decision

Use PostgreSQL as the primary database.

## Alternatives Considered

- MySQL
- SQLite
- MongoDB

## Consequences

### Positive

- Mature relational database
- ACID transactions
- Rich indexing options
- Strong SQL support

---

# ADR-005 — Repository Pattern

## Status

Accepted

## Context

Business logic should not depend on database implementation details.

## Decision

All persistence operations shall be accessed through repository interfaces.

## Alternatives Considered

- Direct ORM usage in services
- Active Record pattern

## Consequences

### Positive

- Easier testing
- Database abstraction
- Cleaner business logic

---

# ADR-006 — Provider Adapter Pattern

## Status

Accepted

## Context

Each job provider exposes different APIs, page structures, authentication mechanisms, and data formats.

## Decision

Implement one adapter per provider using a shared provider interface.

## Consequences

### Positive

- Consistent internal model
- Easier provider expansion
- Isolated provider-specific changes

### Negative

- Slight increase in implementation effort

---

# ADR-007 — AI Abstraction Layer

## Status

Accepted

## Context

The application must support multiple AI providers and models without changing business logic.

## Decision

Introduce an AI abstraction layer between the application and AI providers.

Responsibilities include:

- Provider selection
- Model routing
- Prompt execution
- Retry logic
- Output validation
- Fallback handling

## Alternatives Considered

- Direct provider SDK usage
- Provider-specific services

## Consequences

### Positive

- Vendor independence
- Easier experimentation
- Simplified business services

---

# ADR-008 — Playwright for Browser Automation

## Status

Accepted

## Context

Many job platforms require browser-based interactions rather than public APIs.

## Decision

Use Playwright as the browser automation framework.

## Alternatives Considered

- Selenium
- Puppeteer

## Consequences

### Positive

- Reliable modern browser automation
- Cross-browser support
- Strong automation API

---

# ADR-009 — Background Scheduler

## Status

Accepted

## Context

Job discovery and application preparation must run independently of active user sessions.

## Decision

Introduce a dedicated scheduler and background worker system.

## Consequences

### Positive

- Supports unattended execution
- Improved responsiveness
- Separation of interactive and background workloads

---

# ADR-010 — Immutable Resume Versioning

## Status

Accepted

## Context

Users need to compare, restore, and audit AI-generated resumes over time.

## Decision

Generated resumes shall be immutable.

Editing a resume creates a new version rather than overwriting an existing one.

## Consequences

### Positive

- Full history
- Easy rollback
- Better auditability

---

# ADR-011 — Career Profile as Source of Truth

## Status

Accepted

## Context

Multiple modules require access to user information.

Duplicated profile data creates consistency problems.

## Decision

The Career Profile is the single authoritative source of verified user information.

All AI-generated documents must reference this profile.

## Consequences

### Positive

- Consistent data
- Reduced duplication
- Simplified maintenance

---

# ADR-012 — UUID Primary Keys

## Status

Accepted

## Context

Entities may eventually be created across distributed services.

## Decision

Use UUIDs as primary identifiers for major business entities.

## Alternatives Considered

- Auto-increment integers

## Consequences

### Positive

- Globally unique identifiers
- Better support for distributed systems

---

# ADR-013 — Stateless REST API

## Status

Accepted

## Context

Horizontal scaling and load balancing are project goals.

## Decision

Backend APIs shall remain stateless.

Session-specific information should not be stored in application memory.

## Consequences

### Positive

- Easier scaling
- Simpler deployments
- Improved reliability

---

# ADR-014 — Asynchronous AI Workflows

## Status

Accepted

## Context

AI requests may take significantly longer than standard CRUD operations.

## Decision

Long-running AI tasks shall execute asynchronously.

Clients should receive progress updates where appropriate.

## Consequences

### Positive

- Better user experience
- Improved throughput
- Reduced request blocking

---

# ADR-015 — Configuration via Environment

## Status

Accepted

## Context

Secrets and deployment settings vary across environments.

## Decision

Configuration shall be provided through environment variables or dedicated configuration systems.

Secrets shall never be committed to source control.

## Consequences

### Positive

- Improved security
- Easier deployment
- Environment portability

---

# Decision Governance

A new ADR shall be created when:

- Introducing a new architectural pattern
- Replacing a major framework
- Changing persistence strategy
- Modifying deployment architecture
- Introducing new cross-cutting concerns

Existing ADRs should not be rewritten to hide historical decisions. Instead, create a new ADR referencing the superseded decision.

---

# Related Documents

- System-Architecture.md
- Module-Architecture.md
- Data-Flow.md
- Deployment-Architecture.md
- Technology-Stack.md
- AI_CONTEXT.md

---

End of Document
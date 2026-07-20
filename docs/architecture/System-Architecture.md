# System Architecture

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | System Architecture |
| Version | 2.0 |
| Status | Approved for Implementation |
| Related Documents | AI_CONTEXT.md, PRD.md, Architecture-Decisions.md |

---

# Purpose

This document defines the high-level architecture of AI Job Agent Version 2.

It describes how the major components interact, the architectural style, system boundaries, and guiding principles. It is the primary technical blueprint for implementation.

---

# Architectural Goals

The architecture is designed to achieve the following objectives:

- Modular and maintainable design
- AI-provider independence
- Job-provider independence
- Clear separation of responsibilities
- Scalability
- Testability
- Security by design
- Extensibility without major refactoring
- High observability
- Production readiness

---

# Architectural Principles

The system follows these principles:

1. Clean Architecture
2. Domain-driven modularization
3. Dependency inversion
4. Single Responsibility Principle
5. Interface-driven development
6. Composition over inheritance
7. Event-aware workflows where appropriate
8. Stateless APIs
9. Configuration over hardcoding
10. AI as an infrastructure service—not business logic

---

# High-Level Architecture

```text
                        +-----------------------+
                        |        Browser        |
                        |  React + TypeScript   |
                        +----------+------------+
                                   |
                                   |
                             HTTPS / REST
                                   |
                                   ▼
+-------------------------------------------------------------+
|                     FastAPI Backend                          |
|-------------------------------------------------------------|
| Authentication                                               |
| Career Profile                                               |
| Resume Studio                                                |
| AI Orchestrator                                              |
| Job Discovery                                                |
| Match Engine                                                 |
| Company Intelligence                                         |
| Application Pipeline                                         |
| Automation Scheduler                                         |
| Analytics                                                    |
| Notifications                                                 |
+-----------------------+--------------------------------------+
                        |
                        |
         +--------------+---------------+
         |                              |
         ▼                              ▼
+------------------+          +--------------------+
| PostgreSQL       |          | Background Workers |
|                  |          | Scheduler          |
| User Data        |          | AI Tasks           |
| Jobs             |          | Browser Tasks      |
| Applications     |          | Reports            |
+------------------+          +---------+----------+
                                         |
                +------------------------+-------------------------+
                |                        |                         |
                ▼                        ▼                         ▼
        AI Providers              Job Providers           Browser Automation
(OpenRouter, Ollama, etc.)   (LinkedIn, Naukri, etc.)      Playwright
```

---

# Layered Architecture

The application follows a layered architecture.

```text
Presentation Layer
        │
        ▼
API Layer
        │
        ▼
Application Layer
        │
        ▼
Domain Layer
        │
        ▼
Infrastructure Layer
```

Each layer has a clearly defined responsibility.

---

# Presentation Layer

Responsible for:

- User Interface
- Forms
- Navigation
- Validation
- Dashboards
- Settings
- Resume Preview
- Analytics

Technology:

- React
- TypeScript
- Vite

The presentation layer contains **no business logic**.

---

# API Layer

Responsible for:

- REST endpoints
- Request validation
- Authentication
- Authorization
- Response formatting
- Error mapping

Technology:

- FastAPI

The API layer orchestrates requests but does not implement business rules.

---

# Application Layer

Responsible for coordinating use cases.

Examples:

- Generate Resume
- Discover Jobs
- Prepare Application
- Match Jobs
- Run Scheduler
- Import Resume

Responsibilities:

- Coordinate domain services
- Execute workflows
- Manage transactions
- Invoke repositories
- Call AI services

---

# Domain Layer

The domain layer contains the core business logic.

Examples:

- Match scoring
- Resume selection
- Validation
- Business rules
- Scheduling logic
- Application lifecycle

The domain layer must not depend on:

- FastAPI
- PostgreSQL
- React
- AI providers
- Playwright

---

# Infrastructure Layer

Responsible for external systems.

Includes:

- Database
- AI Providers
- Job Providers
- Browser Automation
- Email
- File Storage
- Logging
- Monitoring

Infrastructure can depend on external libraries.

Business logic must not.

---

# Core Modules

The system consists of the following modules:

## Authentication

Responsibilities

- Login
- Registration
- Sessions
- Authorization

---

## Career Profile

Responsibilities

- Professional information
- Skills
- Experience
- Education
- Projects
- Certifications
- Job preferences

Acts as the single source of truth.

---

## Resume Studio

Responsibilities

- Resume generation
- Resume versions
- Templates
- Export
- Resume comparison

---

## AI Orchestrator

Responsibilities

- Prompt management
- Provider selection
- Model routing
- Retry logic
- Output validation
- Structured responses

The rest of the system never communicates directly with AI providers.

---

## Job Discovery

Responsibilities

- Search providers
- Normalize jobs
- Deduplicate jobs
- Store search results

---

## Match Engine

Responsibilities

- Calculate match score
- Explain score
- Skill gap analysis
- Ranking

---

## Company Intelligence

Responsibilities

- Company summaries
- Hiring insights
- Basic research
- Company metadata

---

## Application Pipeline

Responsibilities

- Resume selection
- Cover letter generation
- AI-generated responses
- Validation
- Review queue
- Submission
- Tracking

---

## Scheduler

Responsibilities

- Execute scheduled jobs
- Trigger automation
- Retry failed executions
- Maintain execution history

---

## Analytics

Responsibilities

- Dashboard metrics
- Match statistics
- Interview rate
- Offer rate
- Provider statistics

---

## Notification Service

Responsibilities

- In-app notifications
- Email notifications
- Scheduler notifications
- Error notifications

---

# External Systems

The application integrates with:

## AI Providers

Examples:

- OpenRouter
- Ollama
- Future providers

All communication occurs through the AI abstraction layer.

---

## Job Providers

Examples:

- LinkedIn
- Naukri
- Foundit
- Greenhouse
- Lever
- Workday
- Ashby
- Y Combinator Jobs

Each provider implements the same interface.

---

## Browser Automation

Technology:

Playwright

Responsibilities:

- Login
- Form filling
- Resume upload
- Cover letter upload
- Navigation
- Application submission

---

# Data Flow Overview

```text
User
 │
 ▼
Frontend
 │
 ▼
API
 │
 ▼
Application Service
 │
 ├────────► Database
 │
 ├────────► AI Orchestrator
 │              │
 │              ▼
 │       AI Provider
 │
 ├────────► Job Provider
 │
 └────────► Playwright
```

---

# Design Constraints

The architecture must satisfy the following constraints:

- No module directly accesses another module's database tables.
- Modules communicate through services or defined interfaces.
- External providers are isolated behind adapters.
- Business rules remain provider-independent.
- AI provider changes require no business logic changes.
- New providers require no modification to existing providers.
- Configuration is environment-driven.
- Secrets are never hardcoded.

---

# Cross-Cutting Concerns

Applied consistently across all modules:

- Authentication
- Authorization
- Validation
- Logging
- Monitoring
- Error handling
- Configuration
- Dependency injection
- Transactions
- Audit logging

---

# Error Handling Strategy

Errors are categorized as:

- Validation Errors
- Authentication Errors
- Authorization Errors
- Business Rule Violations
- AI Errors
- Provider Errors
- Infrastructure Errors
- Unexpected Errors

Errors should propagate in a controlled manner and return meaningful responses.

---

# Logging Strategy

All major operations should generate structured logs.

Typical log events include:

- User login
- Job discovery
- Resume generation
- AI requests
- Scheduler execution
- Application submission
- Provider failures

Sensitive data must be excluded or appropriately protected.

---

# Scalability Strategy

The architecture supports future scaling through:

- Stateless API servers
- Independent background workers
- Modular providers
- Asynchronous AI operations
- Horizontal deployment
- Database indexing
- Caching where appropriate

---

# Security Principles

The architecture enforces:

- Least privilege
- Secure secret management
- HTTPS
- Input validation
- Output encoding where applicable
- Authentication
- Authorization
- Audit logging
- Secure file handling

---

# Architecture Quality Attributes

The design prioritizes:

- Maintainability
- Extensibility
- Reliability
- Scalability
- Security
- Testability
- Observability
- Performance
- Simplicity

---

# Related Documents

- AI_CONTEXT.md
- PRD.md
- Functional-Requirements.md
- Business-Rules.md
- Non-Functional-Requirements.md
- Architecture-Decisions.md
- Module-Architecture.md
- Deployment-Architecture.md

---

End of Document
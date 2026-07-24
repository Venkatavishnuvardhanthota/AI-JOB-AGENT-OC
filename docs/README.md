# AI Job Agent Documentation

**Project:** AI Job Agent v2

**Version:** 2.0

**Status:** Production Ready — v2.0.0 Released

---

# Purpose

This directory contains the complete technical and product documentation for AI Job Agent Version 2.

These documents are the authoritative source of truth for the project.

All implementation, testing, reviews, and future development should follow these specifications.

If implementation and documentation ever disagree, the discrepancy should be resolved intentionally by updating one or both—not by silently diverging.

---

# Documentation Principles

The documentation follows these principles:

- Single source of truth
- AI-first development
- Production-ready architecture
- Modular design
- Version controlled
- Traceable requirements
- Consistent terminology
- Testable specifications

---

# Audience

These documents are intended for:

- Developers
- AI coding agents (OpenCode)
- Reviewers
- Future contributors
- Project maintainers

---

# Repository Structure

```text
docs/
│
├── README.md
├── AI_CONTEXT.md
├── AGENTS.md
├── SUMMARY.md
│
├── 01-product/
├── 02-architecture/
├── 03-api/
├── 04-database/
├── 05-frontend/
├── 06-backend/
├── 07-ai/
├── 08-providers/
├── 09-testing/
├── 10-security/
├── 11-devops/
├── 12-operations/
└── 13-opencode/
```

---

# Document Overview

## Product

Defines what the application should do.

Contains:

- Product vision
- User journeys
- Functional requirements
- Business rules

---

## Architecture

Defines how the system is built.

Contains:

- Overall architecture
- Technical architecture
- AI architecture
- Provider architecture
- ADRs
- Sequence diagrams
- State machines

---

## API

Defines every backend endpoint.

Contains:

- REST APIs
- Authentication
- Error responses
- WebSocket events
- OpenAPI specification

---

## Database

Defines all persistent data.

Contains:

- Tables
- Relationships
- Constraints
- Indexes
- Migration strategy

---

## Frontend

Defines the user interface.

Contains:

- Screens
- Components
- Wireframes
- Design system
- Accessibility

---

## Backend

Defines backend modules and services.

Contains:

- Services
- Scheduler
- Background jobs
- Internal architecture

---

## AI

Defines AI behavior.

Contains:

- Prompt templates
- Model routing
- Output schemas
- Validation
- Evaluation

---

## Providers

Defines integration with job providers.

Each provider has its own specification.

Examples:

- LinkedIn
- Greenhouse
- Lever
- Ashby
- Wellfound
- Workday

---

## Testing

Defines testing strategy.

Contains:

- Unit testing
- Integration testing
- End-to-end testing
- Test catalogue

---

## Security

Defines security architecture.

Contains:

- Threat model
- Authentication
- Authorization
- Secret management

---

## DevOps

Defines deployment.

Contains:

- Docker
- CI/CD
- Monitoring
- Logging
- Backup

---

## Operations

Defines maintenance procedures.

Contains:

- Runbooks
- Troubleshooting
- Recovery

---

## OpenCode

Defines how OpenCode should build the project.

Contains:

- Build guide
- Coding standards
- Prompt templates
- Review checklist

---

# Requirement Traceability

Every important requirement will receive a unique identifier.

Examples:

- FR-001 (Functional Requirement)
- NFR-001 (Non-functional Requirement)
- BR-001 (Business Rule)
- API-001 (API Endpoint)
- DB-001 (Database Object)
- UI-001 (User Interface)
- TC-001 (Test Case)
- ADR-001 (Architecture Decision)

These identifiers enable traceability from requirements through implementation and testing.

---

# Versioning

Documentation follows semantic versioning aligned with the project.

Major versions represent significant architectural changes.

Minor versions introduce compatible enhancements.

Patch versions correct documentation errors or clarify existing behavior.

---

# Contributing

When adding or modifying functionality:

1. Update the relevant documentation.
2. Update affected diagrams if necessary.
3. Ensure requirement identifiers remain stable.
4. Keep cross-references accurate.
5. Verify that implementation matches documentation.

---

# Source of Truth

This documentation is the primary reference for:

- Product behavior
- Architecture
- APIs
- Database schema
- User interface
- AI behavior
- Coding standards

Implementation should conform to these documents unless an intentional design change is approved.

---

# Next Documents

After this file, read documents in the following order:

1. AI_CONTEXT.md
2. AGENTS.md
3. SUMMARY.md
4. Product documentation
5. Architecture documentation
6. API documentation
7. Database documentation
8. Frontend documentation
9. Backend documentation
10. AI documentation
11. Provider documentation
12. Testing documentation
13. Security documentation
14. DevOps documentation
15. Operations documentation

---

End of Document
# Service Layer Specification

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Service Layer Specification |
| Version | 2.0 |
| Status | Approved |
| Related Documents | Backend-Architecture.md, Repositories.md, Module-Architecture.md |

---

# Purpose

This document defines the Service Layer for AI Job Agent Version 2.

The Service Layer contains all business logic.

Its responsibilities include:

- Business rule enforcement
- Workflow orchestration
- Transaction management
- Validation beyond schema validation
- Coordination between repositories
- Coordination with AI providers
- Coordination with external providers

The Service Layer is the heart of the backend.

---

# Design Principles

Services shall:

- Be stateless
- Contain business logic only
- Never expose database implementation details
- Never contain HTTP routing logic
- Never return ORM models directly
- Be independently testable
- Depend on interfaces rather than implementations

---

# Service Architecture

```text
API Router
     │
     ▼
Service
     │
 ┌───┴─────────────┐
 ▼                 ▼
Repository     External Provider
 ▼                 ▼
Database      AI / Job Provider
```

---

# Service Catalog

| Service | Responsibility |
|----------|---------------|
| AuthenticationService | Authentication and account management |
| CareerProfileService | Career profile management |
| ResumeService | Resume generation and versioning |
| AIOrchestratorService | AI provider abstraction |
| JobDiscoveryService | Job search and normalization |
| MatchEngineService | Match scoring |
| CompanyResearchService | Company intelligence |
| ApplicationService | Job applications |
| CoverLetterService | Cover letter generation |
| SchedulerService | Scheduled automation |
| NotificationService | Notifications |
| AuditService | Audit logging |

---

# AuthenticationService

## Responsibilities

- Register users
- Login
- Logout
- Token refresh
- Password management
- Session validation

## Dependencies

- UserRepository
- TokenProvider
- PasswordHasher
- AuditService

## Public Methods

```
register()

login()

logout()

refresh_token()

change_password()

delete_account()

get_current_user()
```

---

# CareerProfileService

## Responsibilities

- Create profile
- Update profile
- Validate profile
- Import resume
- Export profile
- Calculate completeness

## Dependencies

- CareerProfileRepository
- ResumeParser
- AIOrchestratorService
- AuditService

## Public Methods

```
create_profile()

update_profile()

get_profile()

delete_profile()

calculate_completeness()

import_resume()

export_profile()
```

---

# ResumeService

## Responsibilities

- Generate resumes from career profiles
- Optimize resumes for job postings
- Resume preview and export
- Origin tracking (master / uploaded / AI generated / AI tailored)
- Archive resumes

## Dependencies

- ResumeVersionRepository
- CareerProfileService
- AIOrchestratorService

## Public Methods

```
list_resumes()

get_resume()

create_resume()

update_resume()

delete_resume()

archive_resume()

restore_resume()

set_default_resume()

add_section()

update_section()

delete_section()

import_resume()

export_resume()

reorder_sections()

generate_from_profile()

optimize_for_job()

analyze_ats()

analyze_health()

analyze_resume()

export_resume_pdf()

export_resume_docx()
```

---

# AIOrchestratorService

## Responsibilities

- Route AI requests
- Choose provider
- Retry failed requests
- Validate output
- Fallback handling
- Response normalization

## Dependencies

- AI Providers
- Prompt Builder
- Output Validator

## Public Methods

```
generate()

select_provider()

retry()

validate()

fallback()

health_check()
```

---

# JobDiscoveryService

## Responsibilities

- Search providers
- Normalize jobs
- Remove duplicates
- Store jobs
- Refresh cache

## Dependencies

- JobRepository
- Provider Framework
- MatchEngineService

## Public Methods

```
search_jobs()

refresh_jobs()

normalize_jobs()

save_jobs()

deduplicate_jobs()
```

---

# MatchEngineService

## Responsibilities

- Calculate match score
- Explain score
- Detect skill gaps
- Rank jobs

## Dependencies

- CareerProfileService
- JobRepository
- AIOrchestratorService

## Public Methods

```
calculate_score()

generate_explanation()

detect_skill_gap()

rank_jobs()
```

---

# CompanyResearchService

## Responsibilities

- Company summaries
- Industry analysis
- Culture overview
- Cache research

## Dependencies

- CompanyRepository
- AIOrchestratorService

## Public Methods

```
research_company()

refresh_company()

get_cached_summary()
```

---

# ApplicationService

## Responsibilities

- Prepare applications
- Validate applications
- Submit applications
- Track status
- Timeline management

## Dependencies

- ApplicationRepository
- ResumeService
- CoverLetterService
- AIOrchestratorService
- Playwright Provider

## Public Methods

```
prepare_application()

submit_application()

cancel_application()

update_status()

get_timeline()

upload_attachment()
```

---

# CoverLetterService

## Responsibilities

- Generate cover letters
- Version cover letters
- Template handling

## Dependencies

- AIOrchestratorService
- CareerProfileService

## Public Methods

```
generate_cover_letter()

preview_cover_letter()

regenerate_cover_letter()
```

---

# SchedulerService

## Responsibilities

- Execute schedules
- Queue jobs
- Retry failed jobs
- Maintain history

## Dependencies

- SchedulerRepository
- Background Workers

## Public Methods

```
run()

schedule()

pause()

resume()

cancel()

retry_failed()
```

---

# NotificationService

## Responsibilities

- Create notifications
- Mark as read
- Deliver notifications
- Archive notifications

## Dependencies

- NotificationRepository

## Public Methods

```
create()

send()

mark_read()

archive()
```

---

# AuditService

## Responsibilities

- Record audit events
- Store immutable logs
- Query audit history

## Dependencies

- AuditRepository

## Public Methods

```
log_event()

get_history()

search()
```

---

# Service Communication

Services communicate through public methods only.

Allowed

```text
ResumeService
      │
      ▼
CareerProfileService
```

Allowed

```text
ApplicationService
      │
      ▼
ResumeService
```

Not Allowed

```text
ResumeService

↓

ApplicationRepository
```

Cross-module data access must always go through the owning service.

---

# Transaction Management

Services own transactions.

Example

```
Prepare Application

↓

Generate Resume

↓

Generate Cover Letter

↓

Store Records

↓

Commit
```

If any operation fails, the transaction should roll back where practical.

---

# Error Handling

Services should throw domain-specific exceptions.

Examples

```
ProfileIncompleteError

ResumeGenerationError

ProviderUnavailableError

ApplicationAlreadyExistsError

InvalidJobError
```

HTTP-specific exceptions belong in the API layer, not the service layer.

---

# Logging

Each service operation should log:

- Operation name
- User ID (when available)
- Duration
- Outcome
- Correlation ID

Sensitive information must never be logged.

---

# Testing

Each service should support:

- Unit testing
- Repository mocking
- Provider mocking
- AI provider mocking
- Transaction testing

Services should be testable without requiring HTTP requests.

---

# Performance Guidelines

Services should:

- Minimize database round trips
- Avoid duplicate queries
- Use batch operations where appropriate
- Delegate long-running work to background workers
- Reuse cached data when appropriate

---

# Acceptance Criteria

The Service Layer is considered complete when:

- Business logic resides only in services.
- Services coordinate repositories and providers.
- Transactions are managed consistently.
- Services are independently testable.
- External dependencies are abstracted.
- Public methods provide stable contracts.

---

# Related Documents

- Backend-Architecture.md
- Repositories.md
- Background-Jobs.md
- Error-Handling.md
- Module-Architecture.md

---

End of Document
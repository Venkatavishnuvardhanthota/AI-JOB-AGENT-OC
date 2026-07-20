# Repository Layer Specification

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Repository Layer Specification |
| Version | 2.0 |
| Status | Approved |
| Related Documents | Backend-Architecture.md, Services.md, Schema.md |

---

# Purpose

This document defines the Repository Layer for AI Job Agent Version 2.

The Repository Layer is responsible for all database access.

Its responsibilities include:

- CRUD operations
- Query execution
- Transaction participation
- Database abstraction
- Persistence logic
- Query optimization

Repositories isolate business logic from database implementation details.

---

# Design Principles

Repositories shall:

- Contain persistence logic only
- Never contain business rules
- Never call external APIs
- Never call AI providers
- Never contain HTTP logic
- Return domain models or DTOs
- Be independently testable
- Depend only on the database layer

---

# Repository Architecture

```text
Service Layer
      │
      ▼
Repository
      │
      ▼
ORM (SQLAlchemy)
      │
      ▼
PostgreSQL
```

Repositories provide a stable interface between business logic and persistence.

---

# Repository Catalog

| Repository | Responsibility |
|------------|----------------|
| UserRepository | User accounts |
| CareerProfileRepository | Career profile |
| EducationRepository | Education |
| ExperienceRepository | Experience |
| ProjectRepository | Projects |
| SkillRepository | Skills |
| CertificationRepository | Certifications |
| LanguageRepository | Languages |
| JobPreferenceRepository | Job preferences |
| ResumeRepository | Resume versions |
| JobRepository | Jobs |
| CompanyRepository | Company insights |
| CoverLetterRepository | Cover letters |
| ApplicationRepository | Applications |
| AnswerRepository | AI answers |
| AttachmentRepository | Attachments |
| SchedulerRepository | Scheduled jobs |
| NotificationRepository | Notifications |
| AuditRepository | Audit logs |

---

# Common Repository Contract

Every repository should support applicable CRUD operations.

Typical interface:

```text
create()

get_by_id()

list()

update()

delete()

exists()

count()
```

Repositories may expose additional query methods specific to their entity.

---

# UserRepository

## Responsibilities

- Create users
- Find by ID
- Find by email
- Update account
- Soft delete account

### Public Methods

```text
create()

get_by_id()

get_by_email()

update()

soft_delete()

exists_by_email()
```

---

# CareerProfileRepository

## Responsibilities

- Store verified profile
- Load complete profile
- Update profile

### Public Methods

```text
create()

get_by_user()

update()

delete()

get_complete_profile()
```

---

# EducationRepository

### Methods

```text
create()

list_by_profile()

update()

delete()
```

---

# ExperienceRepository

### Methods

```text
create()

list_by_profile()

update()

delete()
```

---

# ProjectRepository

### Methods

```text
create()

list_by_profile()

update()

delete()

exists_by_name()
```

---

# SkillRepository

### Methods

```text
create()

list_by_profile()

update()

delete()

exists()
```

---

# CertificationRepository

### Methods

```text
create()

list_by_profile()

update()

delete()
```

---

# LanguageRepository

### Methods

```text
create()

list_by_profile()

update()

delete()
```

---

# JobPreferenceRepository

### Methods

```text
get()

update()

create()
```

---

# ResumeRepository

## Responsibilities

- Store resume versions
- Archive resumes
- Retrieve versions
- Compare versions

### Public Methods

```text
create()

list_versions()

get_version()

archive()

restore()

duplicate()

latest_version()
```

---

# JobRepository

## Responsibilities

- Store jobs
- Search jobs
- Normalize provider data
- Detect duplicates

### Public Methods

```text
create()

bulk_create()

search()

get()

update()

delete_expired()

find_duplicates()
```

---

# CompanyRepository

### Methods

```text
create()

get()

update()

refresh()
```

---

# CoverLetterRepository

### Methods

```text
create()

get()

list()

delete()
```

---

# ApplicationRepository

## Responsibilities

- Store applications
- Update status
- Track timeline

### Public Methods

```text
create()

get()

list()

update_status()

get_timeline()

exists()

delete()
```

---

# AnswerRepository

### Methods

```text
create()

list()

update()

delete()
```

---

# AttachmentRepository

### Methods

```text
upload()

list()

delete()

get()
```

---

# SchedulerRepository

### Methods

```text
create()

update()

get()

list()

next_jobs()

disable()
```

---

# NotificationRepository

### Methods

```text
create()

list()

mark_read()

archive()
```

---

# AuditRepository

### Methods

```text
log()

list()

search()
```

Audit records are immutable.

No update method should exist.

---

# Query Guidelines

Repositories should:

- Return only required data
- Support pagination
- Support filtering
- Support sorting
- Use indexes efficiently
- Avoid N+1 query patterns

Complex reporting queries should be implemented separately from standard CRUD operations when appropriate.

---

# Transactions

Repositories participate in transactions.

Services own transaction boundaries.

Example

```text
Service

↓

Repository A

↓

Repository B

↓

Commit
```

Repositories should not commit independently unless explicitly designed for isolated operations.

---

# Error Handling

Repositories should raise persistence-related exceptions.

Examples

```text
EntityNotFoundError

DuplicateEntityError

ForeignKeyViolationError

DatabaseConnectionError
```

Business exceptions belong in the Service Layer.

---

# Caching

Repositories may support caching for:

- Company insights
- Frequently accessed configuration
- Read-heavy reference data

Caching behavior should be transparent to the Service Layer.

---

# Performance Guidelines

Repositories should:

- Use indexed queries
- Avoid unnecessary joins
- Support bulk operations
- Batch inserts where appropriate
- Minimize database round trips
- Use lazy or eager loading appropriately based on query needs

---

# Testing

Repositories should support:

- Unit tests with mocked sessions
- Integration tests with PostgreSQL
- Transaction rollback tests
- Constraint validation tests
- Query performance validation

---

# Acceptance Criteria

The Repository Layer is considered complete when:

- All database access is encapsulated in repositories.
- Repositories contain no business logic.
- Services own transaction boundaries.
- Repository interfaces are consistent.
- Queries support pagination, filtering, and sorting where appropriate.
- Repositories are independently testable.

---

# Related Documents

- Backend-Architecture.md
- Services.md
- Schema.md
- Tables.md
- Indexing.md

---

End of Document
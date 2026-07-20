# Database Indexing Strategy

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Database Indexing Strategy |
| Version | 2.0 |
| Status | Approved |
| Related Documents | ERD.md, Schema.md, Tables.md |

---

# Purpose

This document defines the indexing strategy for AI Job Agent Version 2.

The indexing strategy is designed to:

- Improve query performance
- Reduce lookup time
- Optimize joins
- Support filtering and sorting
- Scale with increasing data volume
- Minimize unnecessary indexes
- Maintain write performance

This document specifies logical indexing requirements. Actual SQL implementation should follow these guidelines while considering production workload and query analysis.

---

# Indexing Principles

Indexes should be created for:

- Primary keys
- Foreign keys
- Frequently filtered columns
- Frequently sorted columns
- Frequently joined columns
- Unique business identifiers
- Searchable text fields (where applicable)

Indexes should **not** be added automatically to every column, as excessive indexing increases storage usage and slows INSERT, UPDATE, and DELETE operations.

---

# Primary Key Indexes

Every table shall have a primary key index.

| Table | Primary Key |
|---------|-------------|
| users | id |
| career_profiles | id |
| education | id |
| experience | id |
| projects | id |
| skills | id |
| certifications | id |
| languages | id |
| job_preferences | id |
| resume_versions | id |
| jobs | id |
| company_insights | id |
| cover_letters | id |
| applications | id |
| application_answers | id |
| attachments | id |
| scheduler_jobs | id |
| notifications | id |
| audit_logs | id |

---

# Foreign Key Indexes

All foreign keys should have indexes.

| Table | Foreign Key |
|---------|-------------|
| career_profiles | user_id |
| education | profile_id |
| experience | profile_id |
| projects | profile_id |
| skills | profile_id |
| certifications | profile_id |
| languages | profile_id |
| job_preferences | profile_id |
| resume_versions | user_id |
| resume_versions | generated_for_job_id |
| company_insights | job_id |
| cover_letters | user_id |
| cover_letters | job_id |
| applications | user_id |
| applications | job_id |
| applications | resume_id |
| applications | cover_letter_id |
| application_answers | application_id |
| attachments | application_id |
| scheduler_jobs | user_id |
| notifications | user_id |
| audit_logs | user_id |
| audit_logs | entity_id |

---

# Unique Indexes

The following fields require unique indexes.

| Table | Columns |
|---------|----------|
| users | email |
| career_profiles | user_id |
| skills | (profile_id, name) |
| resume_versions | (user_id, version) |
| jobs | (provider, provider_job_id) |
| applications | (user_id, job_id) |
| job_preferences | profile_id |

---

# Composite Indexes

Composite indexes improve common filtering patterns.

## jobs

Recommended indexes:

```
(provider, posted_at)

(location, employment_type)

(company, posted_at)

(posted_at, employment_type)

(provider, company)
```

---

## applications

Recommended indexes:

```
(user_id, status)

(user_id, submitted_at)

(status, submitted_at)

(job_id, status)
```

---

## resume_versions

Recommended indexes:

```
(user_id, created_at)

(user_id, archived)
```

---

## notifications

Recommended indexes:

```
(user_id, is_read)

(user_id, created_at)
```

---

## scheduler_jobs

Recommended indexes:

```
(user_id, enabled)

(enabled, next_run)
```

---

## audit_logs

Recommended indexes:

```
(user_id, created_at)

(entity, entity_id)

(event_type, created_at)
```

---

# Search Indexes

The application performs keyword searching on selected text fields.

Recommended searchable columns:

## jobs

- title
- company
- description

## projects

- name
- description

## experience

- company
- title
- description

## skills

- name

Depending on search requirements, PostgreSQL full-text search or an external search engine may be used.

---

# Sorting Optimization

Frequently sorted fields should be indexed.

Examples:

Jobs

```
posted_at

salary_min

salary_max
```

Applications

```
submitted_at

status
```

Notifications

```
created_at
```

Resume Versions

```
created_at
```

---

# Pagination Optimization

List endpoints commonly paginate using:

```
ORDER BY created_at DESC

LIMIT

OFFSET
```

Indexes on ordering columns help maintain consistent performance.

For very large datasets, cursor-based pagination may be preferred over OFFSET.

---

# Partial Indexes

Partial indexes may be used where supported.

Examples:

Applications

```
status = 'Submitted'
```

Notifications

```
is_read = FALSE
```

Scheduler Jobs

```
enabled = TRUE
```

These indexes reduce size while improving common queries.

---

# JSONB Indexing

The schema uses JSONB for selected flexible fields.

Examples:

- technologies
- preferred_titles
- preferred_locations
- metadata

When these fields are queried frequently, GIN indexes should be considered.

---

# Index Naming Convention

Recommended format:

```
idx_<table>_<column>

idx_jobs_posted_at

idx_applications_status

idx_resume_versions_user
```

Composite indexes:

```
idx_jobs_provider_posted_at

idx_applications_user_status
```

Unique indexes:

```
uq_users_email

uq_jobs_provider_provider_job
```

---

# Monitoring Index Usage

Index effectiveness should be reviewed periodically.

Monitor for:

- Unused indexes
- Duplicate indexes
- Sequential scans on frequently queried tables
- Slow query execution
- High write overhead caused by excessive indexing

Adjust indexes based on production query patterns rather than assumptions.

---

# Maintenance

Routine maintenance should include:

- Rebuilding fragmented indexes where appropriate
- Updating database statistics
- Reviewing execution plans
- Removing obsolete indexes after validation

Maintenance windows should minimize user impact.

---

# Performance Guidelines

The indexing strategy should support:

- Fast authentication lookups
- Efficient profile retrieval
- Job search filtering
- Resume history retrieval
- Application tracking
- Scheduler execution
- Notification delivery
- Audit log queries

---

# Acceptance Criteria

The indexing strategy is considered complete when:

- Every primary key is indexed.
- Every foreign key has an appropriate index.
- Business uniqueness is enforced.
- Frequently queried columns are indexed.
- Composite indexes support common query patterns.
- Index usage is reviewed as part of ongoing database maintenance.

---

# Related Documents

- ERD.md
- Schema.md
- Tables.md
- Migrations.md

---

End of DocumentS
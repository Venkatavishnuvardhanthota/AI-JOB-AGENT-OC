# Database Schema

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Database Schema |
| Version | 2.0 |
| Status | Approved |
| Related Documents | ERD.md, Tables.md, Migrations.md |

---

# Purpose

This document defines the logical database schema for AI Job Agent Version 2.

It specifies:

- Tables
- Columns
- Data types
- Primary keys
- Foreign keys
- Constraints
- Default values
- Relationships

This document serves as the authoritative schema specification for the application database.

---

# Database Standard

Database Engine

```
PostgreSQL
```

Primary Key

```
UUID
```

Timestamp

```
TIMESTAMPTZ
```

Soft Delete

```
deleted_at TIMESTAMPTZ NULL
```

Audit Fields

```
created_at
updated_at
```

---

# Naming Conventions

Tables

```
snake_case
plural nouns
```

Examples

```
users
applications
resume_versions
career_profiles
```

Columns

```
snake_case
```

Foreign Keys

```
<entity>_id
```

Examples

```
user_id
job_id
resume_id
```

---

# users

## Purpose

Stores authenticated user accounts.

| Column | Type | Constraints |
|---------|------|-------------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | TEXT | NOT NULL |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| deleted_at | TIMESTAMPTZ | NULL |

---

# career_profiles

Stores verified professional information.

| Column | Type | Constraints |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK users(id), UNIQUE |
| professional_summary | TEXT | NULL |
| portfolio_url | TEXT | NULL |
| linkedin_url | TEXT | NULL |
| github_url | TEXT | NULL |
| website_url | TEXT | NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Relationship

```
One User
↓

One Career Profile
```

---

# education

| Column | Type |
|---------|------|
| id | UUID |
| profile_id | UUID FK |
| institution | VARCHAR(255) |
| degree | VARCHAR(255) |
| field_of_study | VARCHAR(255) |
| start_date | DATE |
| end_date | DATE |
| grade | VARCHAR(50) |
| description | TEXT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

---

# experience

| Column | Type |
|---------|------|
| id | UUID |
| profile_id | UUID FK |
| company | VARCHAR(255) |
| title | VARCHAR(255) |
| location | VARCHAR(255) |
| employment_type | VARCHAR(100) |
| start_date | DATE |
| end_date | DATE |
| currently_working | BOOLEAN |
| description | TEXT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

---

# projects

| Column | Type |
|---------|------|
| id | UUID |
| profile_id | UUID FK |
| name | VARCHAR(255) |
| description | TEXT |
| technologies | JSONB |
| github_url | TEXT |
| demo_url | TEXT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

---

# skills

| Column | Type |
|---------|------|
| id | UUID |
| profile_id | UUID FK |
| name | VARCHAR(150) |
| category | VARCHAR(100) |
| proficiency | VARCHAR(50) |
| years_experience | NUMERIC(4,1) |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

Unique Constraint

```
(profile_id, name)
```

---

# certifications

| Column | Type |
|---------|------|
| id | UUID |
| profile_id | UUID FK |
| name | VARCHAR(255) |
| issuer | VARCHAR(255) |
| credential_id | VARCHAR(255) |
| issue_date | DATE |
| expiration_date | DATE |
| credential_url | TEXT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

---

# languages

| Column | Type |
|---------|------|
| id | UUID |
| profile_id | UUID FK |
| language | VARCHAR(100) |
| proficiency | VARCHAR(100) |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

---

# job_preferences

| Column | Type |
|---------|------|
| id | UUID |
| profile_id | UUID FK UNIQUE |
| preferred_titles | JSONB |
| preferred_locations | JSONB |
| employment_types | JSONB |
| work_modes | JSONB |
| minimum_salary | NUMERIC(12,2) |
| preferred_currency | VARCHAR(10) |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

---

# resume_versions

| Column | Type |
|---------|------|
| id | UUID |
| user_id | UUID FK |
| version | INTEGER |
| title | VARCHAR(255) |
| template | VARCHAR(100) |
| content | JSONB |
| generated_for_job_id | UUID FK NULL |
| archived | BOOLEAN |
| created_at | TIMESTAMPTZ |

Constraint

```
(user_id, version)
UNIQUE
```

---

# jobs

| Column | Type |
|---------|------|
| id | UUID |
| provider | VARCHAR(100) |
| provider_job_id | VARCHAR(255) |
| title | VARCHAR(255) |
| company | VARCHAR(255) |
| location | VARCHAR(255) |
| description | TEXT |
| employment_type | VARCHAR(100) |
| salary_min | NUMERIC(12,2) |
| salary_max | NUMERIC(12,2) |
| currency | VARCHAR(10) |
| application_url | TEXT |
| posted_at | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |

Constraint

```
(provider, provider_job_id)
UNIQUE
```

---

# company_insights

| Column | Type |
|---------|------|
| id | UUID |
| job_id | UUID FK |
| summary | TEXT |
| industry | VARCHAR(150) |
| company_size | VARCHAR(100) |
| headquarters | VARCHAR(255) |
| culture | TEXT |
| generated_at | TIMESTAMPTZ |

---

# cover_letters

| Column | Type |
|---------|------|
| id | UUID |
| user_id | UUID FK |
| job_id | UUID FK |
| template | VARCHAR(100) |
| content | TEXT |
| created_at | TIMESTAMPTZ |

---

# applications

| Column | Type |
|---------|------|
| id | UUID |
| user_id | UUID FK |
| job_id | UUID FK |
| resume_id | UUID FK |
| cover_letter_id | UUID FK NULL |
| status | VARCHAR(100) |
| submitted_at | TIMESTAMPTZ NULL |
| notes | TEXT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

Constraint

```
(user_id, job_id)
UNIQUE
```

---

# application_answers

| Column | Type |
|---------|------|
| id | UUID |
| application_id | UUID FK |
| question | TEXT |
| answer | TEXT |
| approved | BOOLEAN |
| created_at | TIMESTAMPTZ |

---

# attachments

| Column | Type |
|---------|------|
| id | UUID |
| application_id | UUID FK |
| filename | VARCHAR(255) |
| storage_path | TEXT |
| mime_type | VARCHAR(100) |
| file_size | BIGINT |
| uploaded_at | TIMESTAMPTZ |

---

# scheduler_jobs

| Column | Type |
|---------|------|
| id | UUID |
| user_id | UUID FK |
| name | VARCHAR(255) |
| schedule | TEXT |
| enabled | BOOLEAN |
| last_run | TIMESTAMPTZ |
| next_run | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |

---

# notifications

| Column | Type |
|---------|------|
| id | UUID |
| user_id | UUID FK |
| title | VARCHAR(255) |
| message | TEXT |
| notification_type | VARCHAR(100) |
| is_read | BOOLEAN |
| created_at | TIMESTAMPTZ |

---

# audit_logs

| Column | Type |
|---------|------|
| id | UUID |
| user_id | UUID FK NULL |
| event_type | VARCHAR(100) |
| entity | VARCHAR(100) |
| entity_id | UUID NULL |
| outcome | VARCHAR(50) |
| metadata | JSONB |
| created_at | TIMESTAMPTZ |

Audit records are immutable and must not be updated after creation.

---

# Common Constraints

The schema enforces:

- UUID primary keys
- Foreign key integrity
- Unique business constraints
- NOT NULL where appropriate
- Default timestamps
- Immutable audit records
- Immutable resume versions

---

# Schema Evolution

Schema changes shall:

- Be implemented through migrations.
- Preserve existing data.
- Be backward compatible whenever practical.
- Include rollback procedures where feasible.

---

# Related Documents

- ERD.md
- Tables.md
- Indexing.md
- Migrations.md

---

End of Document
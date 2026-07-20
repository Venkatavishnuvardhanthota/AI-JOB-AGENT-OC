# Entity Relationship Diagram (ERD)

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Entity Relationship Diagram |
| Version | 2.0 |
| Status | Approved |
| Related Documents | Schema.md, Tables.md, System-Architecture.md |

---

# Purpose

This document defines the logical Entity Relationship Diagram (ERD) for AI Job Agent Version 2.

It identifies the primary entities, their ownership, cardinality, and relationships. The ERD serves as the foundation for the physical database schema and data integrity rules.

---

# Database Design Principles

The database shall:

- Use PostgreSQL as the primary datastore.
- Use UUIDs as primary keys.
- Normalize data to reduce redundancy.
- Enforce referential integrity with foreign keys.
- Store immutable history where required (e.g., resume versions).
- Support efficient querying through indexing.
- Maintain auditability for important user actions.

---

# High-Level ERD

```text
                    +----------------+
                    |     Users      |
                    +----------------+
                           |
                           | 1
                           |
                           | 1
                    +----------------+
                    | Career Profile |
                    +----------------+
                           |
      +----------+---------+----------+-----------+
      |          |         |          |           |
      |          |         |          |           |
      ▼          ▼         ▼          ▼           ▼

 Education  Experience  Projects   Skills   Certifications
      |          |         |          |           |
      +----------+---------+----------+-----------+
                           |
                           ▼
                    Resume Versions
                           |
                           ▼
                    Applications
                           |
          +----------------+----------------+
          |                                 |
          ▼                                 ▼
         Jobs                         Cover Letters
          |
          ▼
 Company Insights

Applications
      |
      ▼
AI Answers

Applications
      |
      ▼
Attachments

Users
      |
      ▼
Scheduler Jobs

Users
      |
      ▼
Notifications

Users
      |
      ▼
Audit Logs
```

---

# Primary Entities

| Entity | Purpose |
|---------|---------|
| Users | User accounts |
| Career Profile | Verified professional profile |
| Education | Education history |
| Experience | Employment history |
| Projects | Personal and professional projects |
| Skills | Technical and soft skills |
| Certifications | Certifications and licenses |
| Languages | Spoken languages |
| Resume Versions | Generated resume history |
| Jobs | Normalized job listings |
| Applications | Job applications |
| Cover Letters | Generated cover letters |
| AI Answers | Generated application responses |
| Company Insights | Cached company research |
| Attachments | Uploaded application files |
| Scheduler Jobs | Scheduled automation tasks |
| Notifications | User notifications |
| Audit Logs | Immutable audit history |

---

# Core Relationships

## Users

```
User
 ├── 1 Career Profile
 ├── Many Resume Versions
 ├── Many Applications
 ├── Many Notifications
 ├── Many Scheduler Jobs
 └── Many Audit Logs
```

---

## Career Profile

```
Career Profile

├── Many Education Records

├── Many Experience Records

├── Many Projects

├── Many Skills

├── Many Certifications

├── Many Languages
```

---

## Resume

```
Resume Version

belongs to

User

generated from

Career Profile
```

Each generated resume is immutable.

---

## Jobs

```
Job

may have

Many Applications

belongs to

One Provider
```

---

## Applications

```
Application

belongs to

One User

One Job

One Resume Version
```

Optional relationships

```
One Cover Letter

Many AI Answers

Many Attachments
```

---

## Company Insights

```
Company Insight

belongs to

One Job

may be reused by

Many Users
```

---

## Scheduler

```
Scheduler Job

belongs to

One User
```

---

## Notifications

```
Notification

belongs to

One User
```

---

## Audit Logs

```
Audit Log

belongs to

One User
```

Audit records are immutable.

---

# Cardinality Summary

| Parent | Child | Relationship |
|----------|--------|-------------|
| User | Career Profile | 1 : 1 |
| Career Profile | Education | 1 : N |
| Career Profile | Experience | 1 : N |
| Career Profile | Projects | 1 : N |
| Career Profile | Skills | 1 : N |
| Career Profile | Certifications | 1 : N |
| Career Profile | Languages | 1 : N |
| User | Resume Versions | 1 : N |
| User | Applications | 1 : N |
| Job | Applications | 1 : N |
| Resume Version | Applications | 1 : N |
| Application | Attachments | 1 : N |
| Application | AI Answers | 1 : N |
| Application | Timeline Events | 1 : N |
| User | Notifications | 1 : N |
| User | Scheduler Jobs | 1 : N |
| User | Audit Logs | 1 : N |

---

# Ownership Rules

Every entity has a single owner.

| Entity | Owner |
|----------|--------|
| Career Profile | User |
| Resume Version | User |
| Education | Career Profile |
| Experience | Career Profile |
| Projects | Career Profile |
| Skills | Career Profile |
| Certifications | Career Profile |
| Languages | Career Profile |
| Applications | User |
| Attachments | Application |
| AI Answers | Application |
| Notifications | User |
| Scheduler Jobs | User |

---

# Data Integrity Rules

The database shall enforce:

- Foreign key constraints.
- Unique primary keys.
- Required relationships.
- Cascading behavior where appropriate.
- Immutable resume versions.
- Immutable audit records.
- Duplicate prevention for configurable entities (e.g., skills).

---

# Cascade Strategy

| Parent | Child | Strategy |
|---------|-------|----------|
| User | Career Profile | Cascade delete (subject to retention policy) |
| Career Profile | Education | Cascade |
| Career Profile | Experience | Cascade |
| Career Profile | Projects | Cascade |
| Career Profile | Skills | Cascade |
| Career Profile | Certifications | Cascade |
| Career Profile | Languages | Cascade |
| Application | Attachments | Cascade |
| Application | AI Answers | Cascade |

Entities that represent historical records (e.g., audit logs) should follow the application's retention policy rather than automatic deletion.

---

# Future Expansion

The model is designed to accommodate future additions, including:

- Multiple resumes per application
- Interview tracking
- Recruiter contacts
- Company notes
- Team collaboration
- Organizations and workspaces
- AI evaluation history
- Additional job providers

New entities should integrate without requiring breaking changes to existing relationships.

---

# Related Documents

- Schema.md
- Tables.md
- Indexing.md
- Migrations.md
- System-Architecture.md

---

End of Document
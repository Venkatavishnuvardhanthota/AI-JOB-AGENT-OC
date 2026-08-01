# Database Tables

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Database Tables |
| Version | 2.0 |
| Status | Approved |
| Related Documents | ERD.md, Schema.md, Indexing.md |

---

# Purpose

This document serves as the **database data dictionary** for AI Job Agent Version 2.

For every table it defines:

- Business purpose
- Ownership
- Lifecycle
- Relationships
- Column descriptions
- Validation rules
- Constraints
- Business notes

The actual SQL types are defined in **Schema.md**. This document focuses on the meaning and usage of the data.

---

# Table Overview

| Table | Purpose |
|---------|---------|
| users | User authentication and account information |
| career_profiles | Verified professional profile |
| education | Educational history |
| experience | Professional work experience |
| projects | Personal and professional projects |
| skills | Technical and soft skills |
| certifications | Certifications and licenses |
| languages | Spoken languages |
| job_preferences | User job search preferences |
| resume_versions | Generated resume history |
| jobs | Normalized job listings |
| company_insights | AI-generated company research |
| cover_letters | Generated cover letters |
| applications | Job application records |
| application_answers | AI-generated application responses |
| attachments | Uploaded files |
| scheduler_jobs | Scheduled automation tasks |
| notifications | User notifications |
| audit_logs | Immutable audit records |

---

# users

## Purpose

Stores user authentication information and account metadata.

## Owner

Authentication Module

## Relationships

```
1 User
│
├── 1 Career Profile
├── Many Resume Versions
├── Many Applications
├── Many Notifications
├── Many Scheduler Jobs
└── Many Audit Logs
```

### Important Columns

| Column | Description |
|---------|-------------|
| email | Login identifier |
| password_hash | Secure password hash |
| is_active | Account status |

### Validation

- Email must be unique.
- Password hashes only.
- Email cannot be null.

---

# career_profiles

## Purpose

Stores the user's verified professional information.

This table is the **single source of truth** for resume generation.

## Owner

Career Profile Module

### Contains

- Professional summary
- Headline, current role, desired role
- Employment status, notice period
- Current / expected salary and salary preference (`paid_only`, `paid_preferred`, `unpaid_acceptable`)
- Willingness to relocate, visa sponsorship requirement
- Portfolio links (portfolio, LinkedIn, GitHub, website)

### Business Rules

- One profile per user.
- AI cannot modify this table without user confirmation.
- `paid_only` salary preference requires an expected salary.

---

# education

## Purpose

Stores education history.

### Examples

- University
- College
- Diploma
- Certification programs

### Validation

- Institution required
- Degree required
- Location and CGPA optional
- End date cannot precede start date
- `currently_studying` leaves end date empty

---

# experience

## Purpose

Stores work history.

### Includes

- Company
- Position
- Employment dates
- Employment type (`full_time`, `part_time`, `contract`, `internship`, `freelance`, `self_employed`, `temporary`)
- Responsibilities (list)
- Achievements (list)
- Technologies used (list)

### Business Rules

- Multiple experience records allowed.
- Current employment has no end date (`currently_working` requires `end_date` to be empty).
- Description supports multiple responsibilities.

---

# projects

## Purpose

Stores user projects.

Projects may include:

- Personal
- Academic
- Professional
- Open Source

### Business Rules

- Project names should be unique within a profile.
- GitHub, demo, and live links are optional and URL-validated.

---

# skills

## Purpose

Stores user skills.

### Categories

- Programming
- Framework
- Database
- Cloud
- DevOps
- Soft Skill
- Language
- Other

### Business Rules

Duplicate skills are not permitted within a single profile (case-insensitive).

### Attributes

- Category, string `proficiency`, `skill_level`, `years_experience`, `display_order`

---

# certifications

## Purpose

Stores certifications.

Examples

- AWS
- Azure
- Google Cloud
- Coursera
- Udemy

Expiration dates are optional and must not precede the issue date.

### Attributes

- Issuer, `credential_id`, `credential_url`, `issue_date`, `expiration_date`

---

# languages

## Purpose

Stores spoken languages.

### Example Levels

- Native
- Fluent
- Professional Working
- Intermediate
- Beginner

### Business Rules

- Names are title-cased and trimmed.
- Duplicate languages not permitted within a profile (case-insensitive).

---

# social_links

## Purpose

Stores links to professional social profiles.

### Platform Values

- `linkedin`, `github`, `portfolio`, `website`, `other`

### Business Rules

- One link per platform per profile.
- URLs validated.
- Response includes a computed display title.
- Platform enforced by check constraint `ck_social_link_platform`; legacy non-normalized values are coerced to `other` on read and sanitized by migration `8c9d0e1f2a3b`.

---

# achievements

## Purpose

Stores user achievements.

### Examples

- Awards
- Hackathon wins
- Publications
- Certifications of merit

### Validation

- Title required (max 255 characters).
- Optional date, organization, type, description, URL.

---

# job_preferences

## Purpose

Stores user search preferences.

### Includes

- Preferred titles
- Locations
- Remote preference
- Employment types
- Salary expectations

Used by:

- Match Engine
- Job Discovery
- Scheduler

---

# resume_versions

## Purpose

Stores immutable resume versions.

Each generation creates a new record.

### Business Rules

- Never update generated content.
- Never overwrite existing versions.
- Archive instead of delete.

---

# jobs

## Purpose

Stores normalized jobs collected from providers.

### Source Providers

Examples

- LinkedIn
- Greenhouse
- Workday
- Lever
- Ashby

### Business Rules

- Duplicate provider jobs prevented.
- Provider-specific fields normalized.
- Historical jobs may be retained according to retention policy.

---

# company_insights

## Purpose

Stores AI-generated company research.

### Includes

- Industry
- Company size
- Headquarters
- Culture summary
- AI summary

### Business Rules

Insights may be regenerated when stale.

---

# cover_letters

## Purpose

Stores generated cover letters.

### Business Rules

- Generated from verified Career Profile.
- Multiple cover letters allowed for different jobs.

---

# applications

## Purpose

Tracks every application.

### Status Examples

- Draft
- Ready for Review
- Submitted
- Interview
- Offer
- Rejected

### Business Rules

One user should not have duplicate applications for the same job unless explicitly allowed by system policy.

---

# application_answers

## Purpose

Stores AI-generated responses.

### Examples

- Why do you want to work here?
- Tell us about yourself.
- Describe a challenge.

### Business Rules

- Generated answers require user approval before submission.
- Answers remain associated with the application for auditability.

---

# attachments

## Purpose

Stores uploaded files.

Examples

- Resume
- Portfolio
- Certificates
- Additional documents

### Validation

- File type validation
- Maximum size validation
- Virus scanning (future enhancement)

---

# scheduler_jobs

## Purpose

Stores scheduled automation tasks.

Examples

- Daily job search
- Weekly resume review
- Automated application runs

### Business Rules

- Disabled jobs are never executed.
- Execution history is tracked separately if implemented.

---

# notifications

## Purpose

Stores user notifications.

### Types

- Success
- Warning
- Error
- Information
- Reminder

### Business Rules

Notifications may be archived or purged according to the retention policy.

---

# audit_logs

## Purpose

Stores immutable audit events.

### Example Events

- Login
- Resume generated
- Application submitted
- Password changed
- Profile updated

### Business Rules

- Never edited.
- Never reused.
- Written only by the application.
- Retained according to audit retention requirements.

---

# Common Validation Rules

All tables should enforce:

- Foreign key integrity
- Required fields
- Valid enum values
- Maximum field lengths
- Timestamp consistency
- UUID identifiers

---

# Data Ownership

| Module | Owns Tables |
|---------|-------------|
| Authentication | users |
| Career Profile | career_profiles, education, experience, projects, skills, certifications, languages, social_links, achievements, job_preferences |
| Resume Studio | resume_versions |
| Job Discovery | jobs, company_insights |
| Application Pipeline | applications, application_answers, attachments, cover_letters |
| Scheduler | scheduler_jobs |
| Notifications | notifications |
| Audit | audit_logs |

---

# Lifecycle Summary

| Table | Create | Update | Delete |
|---------|--------|--------|--------|
| users | Yes | Yes | Soft Delete |
| career_profiles | Yes | Yes | Cascade with User |
| resume_versions | Yes | No | Archive |
| jobs | Yes | Limited | Retention Policy |
| applications | Yes | Status Updates | Retention Policy |
| audit_logs | Yes | Never | Retention Policy |

---

# Related Documents

- ERD.md
- Schema.md
- Indexing.md
- Migrations.md

---

End of Document
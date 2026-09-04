# Career Profile API

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Career Profile API |
| Version | 2.0 |
| Status | Approved |
| Base Path | /api/v1/profile |
| Related Documents | API-Overview.md, Functional-Requirements.md, Business-Rules.md |

---

# Purpose

This document defines the REST API for managing a user's Career Profile.

The Career Profile is the **single source of truth** for all verified user information used throughout the application.

No AI-generated content may introduce information that is not present in the verified Career Profile unless explicitly confirmed and saved by the user.

---

# Responsibilities

The Career Profile API manages:

- Personal Information
- Professional Summary
- Education
- Work Experience
- Projects
- Skills
- Certifications
- Languages
- Job Preferences
- Portfolio Links
- Resume Import
- Profile Completeness
- Profile Export

---

# Authentication

All endpoints require authentication.

Authorization Header

```
Authorization: Bearer <access_token>
```

---

# Endpoint Overview

| Method | Endpoint | Purpose |
|----------|----------|----------|
| GET | / | Get complete profile |
| PATCH | / | Update profile |
| GET | /completeness | Calculate profile completeness |
| GET | /education | List education |
| POST | /education | Add education |
| PATCH | /education/{id} | Update education |
| DELETE | /education/{id} | Delete education |
| GET | /experience | List experience |
| POST | /experience | Add experience |
| PATCH | /experience/{id} | Update experience |
| DELETE | /experience/{id} | Delete experience |
| GET | /projects | List projects |
| POST | /projects | Add project |
| PATCH | /projects/{id} | Update project |
| DELETE | /projects/{id} | Delete project |
| GET | /skills | List skills (alphabetical, case-insensitive) |
| POST | /skills | Add skill |
| PUT | /skills | Replace the full skill list (bulk) |
| PATCH | /skills/{id} | Update skill |
| DELETE | /skills/{id} | Delete skill |
| GET | /certifications | List certifications |
| POST | /certifications | Add certification |
| PATCH | /certifications/{id} | Update certification |
| DELETE | /certifications/{id} | Delete certification |
| GET | /languages | List languages |
| POST | /languages | Add language |
| PATCH | /languages/{id} | Update language |
| DELETE | /languages/{id} | Delete language |
| GET | /social-links | List social links |
| POST | /social-links | Add social link |
| PATCH | /social-links/{id} | Update social link |
| DELETE | /social-links/{id} | Delete social link |
| GET | /achievements | List achievements |
| POST | /achievements | Add achievement |
| PATCH | /achievements/{id} | Update achievement |
| DELETE | /achievements/{id} | Delete achievement |
| PATCH | /preferences | Update job preferences |

---

# GET /

## Purpose

Retrieve the authenticated user's complete Career Profile.

### Success Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "headline": "Senior Software Engineer",
    "professional_summary": "...",
    "total_years_experience": 6.0,
    "current_role": "Software Engineer",
    "desired_role": "Senior Backend Engineer",
    "employment_status": "employed",
    "current_salary": 120000.0,
    "expected_salary": 150000.0,
    "salary_preference": "paid_only",
    "willing_to_relocate": true,
    "visa_sponsorship_requirement": false,
    "notice_period": "30 days",
    "portfolio_url": null,
    "linkedin_url": "https://linkedin.com/in/...",
    "github_url": null,
    "website_url": null,
    "profile_completeness": 72,
    "education": [],
    "experience": [],
    "projects": [],
    "skills": [],
    "certifications": [],
    "languages": [],
    "social_links": [],
    "achievements": [],
    "preferences": {},
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  }
}
```

---

# PATCH /

## Purpose

Update selected profile fields.

### Example

```json
{
  "headline": "Senior Software Engineer",
  "expected_salary": 150000,
  "salary_preference": "paid_only"
}
```

Only supplied fields are modified. Invalid URLs return `422`.

### Salary Preference

`salary_preference` accepts one of:

- `paid_only`
- `paid_preferred`
- `unpaid_acceptable`

Setting `paid_only` requires `expected_salary` to be present.

---

# GET /completeness

## Purpose

Calculate Career Profile completeness.

### Example Response

```json
{
  "success": true,
  "data": {
    "percentage": 87,
    "breakdown": {
      "headline": 5,
      "professional_summary": 8,
      "education": 8,
      "experience": 8,
      "skills": 8,
      "achievements": 5,
      "social_links": 5
    },
    "missing_sections": [
      "languages",
      "certifications"
    ]
  }
}
```

The `breakdown` contains per-field scores in points; the weights total 100, so `percentage` is the sum of earned points.

---

# POST /import-resume

## Purpose

Extract profile information from an uploaded resume.

### Request

```
multipart/form-data
```

Field

```
resume
```

Supported formats

- PDF
- DOCX (future)

### Processing Flow

```
Resume Upload
      │
      ▼
Text Extraction
      │
      ▼
AI Extraction
      │
      ▼
Structured Profile
      │
      ▼
User Review
      │
      ▼
Save
```

### Business Rules

- Imported information shall **never** overwrite existing profile data automatically.
- User confirmation is required before persistence.
- AI confidence alone is insufficient for saving extracted information.

---

# GET /export

## Purpose

Export the complete Career Profile.

Supported formats

- JSON
- PDF (future)

---

# Education

## POST /education

### Example

```json
{
  "institution": "ABC University",
  "degree": "Bachelor of Technology",
  "field_of_study": "Computer Science",
  "location": "Boston, USA",
  "cgpa": "8.6",
  "start_date": "2023-08-01",
  "end_date": "2027-05-30",
  "currently_studying": false
}
```

### Validation

Required

- Institution
- Degree

Optional

- Location
- CGPA
- Dates (`end_date` must be on or after `start_date`)

---

## PATCH /education/{id}

Updates a single education record.

---

## DELETE /education/{id}

Deletes a single education record.

---

# Experience

## POST /experience

Example

```json
{
  "company": "OpenAI",
  "title": "Software Engineer",
  "location": "San Francisco",
  "employment_type": "full_time",
  "start_date": "2025-01-01",
  "currently_working": true,
  "responsibilities": [
    "Built scalable backend services."
  ],
  "achievements": [
    "Reduced p95 latency by 40%."
  ],
  "technologies_used": [
    "Python",
    "FastAPI"
  ]
}
```

Validation

- Company required
- Title required
- `end_date` must be empty when `currently_working` is true
- `end_date` must be on or after `start_date` otherwise

---

## PATCH /experience/{id}

Update experience.

---

## DELETE /experience/{id}

Delete experience.

---

# Projects

## POST /projects

```json
{
  "name": "AI Job Agent",
  "description": "Automated job application platform.",
  "technologies": [
    "FastAPI",
    "React",
    "PostgreSQL"
  ],
  "github_url": "",
  "demo_url": ""
}
```

Validation

- Project name required
- Description required

---

## PATCH /projects/{id}

Update project.

---

## DELETE /projects/{id}

Delete project.

---

# Skills

## POST /skills

```json
{
  "name": "Python"
}
```

Validation

- Name required (trimmed)
- Duplicate skills are prevented (case-insensitive, returns `409 CONFLICT`)

---

## PUT /skills

Replaces the entire skill list atomically (deletes existing skills, inserts the given names).

```json
{
  "skills": ["Python", "SQL", "Docker"]
}
```

Validation

- `skills` must be a non-empty list (at least 1 item; `422` if empty)
- Names are trimmed; blank/whitespace-only entries are dropped
- Duplicates are removed case-insensitively
- If no valid names remain, `422` with `At least one skill name is required.`

Response — the full new skill list, sorted alphabetically (case-insensitive).

---

## PATCH /skills/{id}

Update skill.

---

## DELETE /skills/{id}

Delete skill.

---

# Certifications

## POST /certifications

```json
{
  "name": "AWS Certified Cloud Practitioner",
  "issuer": "Amazon Web Services",
  "credential_id": "ABC123",
  "credential_url": "https://aws.com/cert/ABC123",
  "issue_date": "2026-01-10",
  "expiration_date": "2029-01-10"
}
```

Validation

- `expiration_date` must be on or after `issue_date`
- `credential_url` must be a valid URL

---

## PATCH /certifications/{id}

Update certification.

---

## DELETE /certifications/{id}

Delete certification.

---

# Languages

## POST /languages

Example

```json
{
  "language": "English",
  "proficiency": "Professional Working"
}
```

Validation

- Language names are title-cased and trimmed
- Duplicate languages are prevented per profile (case-insensitive, returns `409 CONFLICT`)

---

## PATCH /languages/{id}

Update language.

---

## DELETE /languages/{id}

Delete language.

---

# Social Links

## POST /social-links

Example

```json
{
  "platform": "linkedin",
  "url": "https://linkedin.com/in/...",
  "display_order": 1
}
```

Validation

- Platform must be one of `linkedin` / `github` / `portfolio` / `website` / `other` (normalized case-insensitively; unknown values are rejected with `422`)
- URL must be valid
- One link per platform per profile (`409 CONFLICT` on duplicates)

Response includes a computed `title` (e.g. `LinkedIn`, `GitHub`, `Portfolio`, `Personal Website`).

Reads are defensive: legacy rows with non-normalized `platform` values (e.g. `sq`) are coerced to `other` in responses and never crash serialization; a DB check constraint (`ck_social_link_platform`) prevents new invalid values.

---

## PATCH /social-links/{id}

Update social link.

---

## DELETE /social-links/{id}

Delete social link.

---

# Achievements

## POST /achievements

Example

```json
{
  "title": "Regional Hackathon Winner",
  "organization": "Hack Corp",
  "achievement_type": "Hackathon Winner",
  "date": "2026-03-15",
  "description": "Led a team of 4 to first place.",
  "url": "https://example.com/win"
}
```

Validation

- Title required (max 255 characters)
- URL must be valid

---

## PATCH /achievements/{id}

Update achievement.

---

## DELETE /achievements/{id}

Delete achievement.

---

# PATCH /preferences

## Purpose

Update job preferences.

Example

```json
{
  "job_titles": [
    "Backend Developer",
    "Software Engineer"
  ],
  "locations": [
    "Remote",
    "Bangalore"
  ],
  "employment_type": [
    "Full-Time"
  ],
  "work_mode": [
    "Remote",
    "Hybrid"
  ],
  "minimum_salary": 1200000
}
```

---

# Validation Rules

The API validates:

- Required fields
- Maximum lengths
- Date consistency
- Duplicate records
- Supported URLs
- Enum values
- File types
- File size

---

# Business Rules

- Career Profile is the authoritative user profile.
- AI cannot fabricate profile information.
- Deleted information must not appear in newly generated documents.
- Imported resume data requires explicit user approval.
- Resume generation uses only verified profile information.

---

# Error Codes

| Code | Description |
|------|-------------|
| PROFILE_NOT_FOUND | Profile does not exist |
| PROFILE_VALIDATION_ERROR | Validation failed |
| DUPLICATE_SKILL | Skill already exists |
| DUPLICATE_PROJECT | Project already exists |
| DUPLICATE_LANGUAGE | Language already exists |
| DUPLICATE_SOCIAL_LINK | Social link platform already exists |
| INVALID_FILE | Unsupported file type |
| FILE_TOO_LARGE | Uploaded file exceeds limit |
| IMPORT_FAILED | Resume extraction failed |

---

# Audit Events

The following events should be recorded:

- Profile created
- Profile updated
- Resume imported
- Education added
- Experience updated
- Project deleted
- Skill modified
- Preferences updated
- Profile exported

---

# Related Documents

- API-Overview.md
- Functional-Requirements.md
- Business-Rules.md
- User-Journeys.md
- AI-Architecture.md

---

End of Document
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
| PUT | / | Replace profile |
| PATCH | / | Update profile |
| GET | /completeness | Calculate profile completeness |
| POST | /import-resume | Import resume |
| GET | /export | Export profile |
| POST | /education | Add education |
| PATCH | /education/{id} | Update education |
| DELETE | /education/{id} | Delete education |
| POST | /experience | Add experience |
| PATCH | /experience/{id} | Update experience |
| DELETE | /experience/{id} | Delete experience |
| POST | /projects | Add project |
| PATCH | /projects/{id} | Update project |
| DELETE | /projects/{id} | Delete project |
| POST | /skills | Add skill |
| PATCH | /skills/{id} | Update skill |
| DELETE | /skills/{id} | Delete skill |
| POST | /certifications | Add certification |
| PATCH | /certifications/{id} | Update certification |
| DELETE | /certifications/{id} | Delete certification |
| POST | /languages | Add language |
| PATCH | /languages/{id} | Update language |
| DELETE | /languages/{id} | Delete language |
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
    "personal_information": {},
    "summary": "",
    "education": [],
    "experience": [],
    "projects": [],
    "skills": [],
    "certifications": [],
    "languages": [],
    "preferences": {},
    "portfolio_links": {}
  }
}
```

---

# PUT /

## Purpose

Replace the complete Career Profile.

### Notes

Use only when replacing the full profile.

For normal edits, PATCH is preferred.

---

# PATCH /

## Purpose

Update selected profile fields.

### Example

```json
{
  "summary": "Backend Developer with experience building AI-powered applications."
}
```

Only supplied fields are modified.

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
    "missing_sections": [
      "Languages",
      "Certifications"
    ]
  }
}
```

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
  "start_date": "2023-08-01",
  "end_date": "2027-05-30",
  "grade": "8.6 CGPA"
}
```

### Validation

Required

- Institution
- Degree

Optional

- Grade
- Description

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
  "start_date": "2025-01-01",
  "currently_working": true,
  "description": [
    "Built scalable backend services."
  ]
}
```

Validation

- Company required
- Title required

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
  "name": "Python",
  "category": "Programming Language",
  "level": "Advanced"
}
```

Validation

- Name required
- Duplicate skills should be prevented.

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
  "issue_date": "2026-01-10"
}
```

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

---

## PATCH /languages/{id}

Update language.

---

## DELETE /languages/{id}

Delete language.

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
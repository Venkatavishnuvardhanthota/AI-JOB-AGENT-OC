# Resume API

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Resume API |
| Version | 2.0 |
| Status | Approved |
| Base Path | /api/v1/resumes |
| Related Documents | API-Overview.md, Career-Profile.md, Functional-Requirements.md |

---

# Purpose

This document defines the REST API for Resume Studio.

Resume Studio is responsible for:

- AI-powered resume generation
- Resume versioning
- Template selection
- Resume preview
- Resume download
- Resume comparison
- Resume restoration
- Resume archival

The Resume API always generates resumes from the verified Career Profile.

---

# Authentication

All endpoints require authentication.

```
Authorization: Bearer <access_token>
```

---

# Endpoint Overview

| Method | Endpoint | Purpose |
|---------|----------|----------|
| GET | / | List resumes (`?origin=master\|ai_generated\|ai_tailored\|uploaded`, comma-separated) |
| POST | / | Create a resume (`origin=master`, manual) |
| POST | /generate | Generate from Career Profile (`origin=ai_generated`) |
| POST | /upload | Upload PDF/DOCX (`origin=uploaded`) |
| POST | /import | Import resume JSON |
| GET | /{resume_id} | Get resume |
| PATCH | /{resume_id} | Update metadata |
| DELETE | /{resume_id} | Delete resume |
| POST | /{resume_id}/archive | Archive resume |
| POST | /{resume_id}/restore | Restore archived resume |
| POST | /{resume_id}/optimize | Tailor resume to a job (`origin=ai_tailored`) |
| GET | /{resume_id}/export | Export resume JSON |
| GET | /{resume_id}/download/{format} | Download as `json`, `pdf`, or `docx` |
| GET | /{resume_id}/sections | List sections |
| POST | /{resume_id}/sections | Add section |
| PATCH | /{resume_id}/sections/{section_id} | Update section |
| DELETE | /{resume_id}/sections/{section_id} | Delete section |
| PUT | /{resume_id}/sections/reorder | Reorder sections |
| GET | /{resume_id}/ats | ATS analysis |
| GET | /{resume_id}/health | Resume health score |
| POST | /{resume_id}/analyze | ATS + health analysis against a job |

Removed in v2.1.1: `POST /{resume_id}/versions`, `GET /{resume_id}/versions`,
`POST /{resume_id}/duplicate`, `POST /compare`, `GET /templates`.

---

# Resume Origins

Every resume carries an `origin` value surfaced in list responses and used as an
origin badge in the UI:

| Origin | Meaning |
|--------|---------|
| `master` | Manually created |
| `uploaded` | Created from an uploaded or imported file |
| `ai_generated` | Generated from the Career Profile |
| `ai_tailored` | Optimized/tailored for a specific job |

The library "My Resumes" tab queries `origin=master` (the API expands this to
master + uploaded); the "AI Generated" tab queries `origin=ai_generated,ai_tailored`.

---

# Resume Lifecycle

```text
Career Profile
      │
      ▼
Resume Generation
      │
      ▼
AI Processing
      │
      ▼
Validation
      │
      ▼
Resume Version
      │
      ▼
Preview
      │
      ▼
Download
```

---

# GET /

## Purpose

Return all resume versions.

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Backend Developer Resume",
      "template": "Modern",
      "version": 5,
      "created_at": "2026-07-20T10:30:00Z",
      "status": "active"
    }
  ]
}
```

---

# POST /generate

## Purpose

Generate a new AI-optimized resume.

### Request

```json
{
  "job_id": "uuid",
  "template": "Modern",
  "title": "Backend Developer Resume"
}
```

### Generation Flow

```text
Career Profile
      │
      ▼
Target Job
      │
      ▼
Prompt Builder
      │
      ▼
AI Provider
      │
      ▼
Output Validation
      │
      ▼
Resume Version
```

### Business Rules

- Resume content must originate from the verified Career Profile.
- AI may rewrite wording but shall not invent qualifications.
- Generation creates a new immutable version.

### Success Response

**201 Created**

```json
{
  "success": true,
  "data": {
    "resume_id": "uuid",
    "version": 6,
    "status": "generated"
  }
}
```

### Possible Errors

| Status | Reason |
|---------|--------|
|400|Invalid request|
|404|Job not found|
|422|Validation failed|
|503|AI provider unavailable|

---

# GET /{resume_id}

## Purpose

Retrieve a resume.

### Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "version": 6,
    "template": "Modern",
    "title": "Backend Developer Resume",
    "content": {},
    "created_at": "..."
  }
}
```

---

# PATCH /{resume_id}

## Purpose

Update editable metadata.

Editable fields include:

- Title
- Tags
- Notes

Resume content is immutable after generation.

---

# DELETE /{resume_id}

## Purpose

Archive a resume.

### Business Rules

- Archived resumes remain recoverable.
- Resume history is preserved.
- Active applications continue referencing archived versions.

---

# POST /{resume_id}/restore

## Purpose

Restore an archived resume.

### Response

```json
{
  "success": true,
  "message": "Resume restored successfully."
}
```

---

# POST /{resume_id}/optimize

## Purpose

Tailor an existing resume to a target job.

Creates a new resume with `origin=ai_tailored` and `status=active`; the original
is left untouched. `enhance_with_ai` (default `true`) rewrites sections via the
AI provider; AI output is parsed defensively and falls back to original content.

### Request

```json
{
  "job_id": "uuid",
  "target_role": "Senior Backend Engineer",
  "enhance_with_ai": true
}
```

---

# Resume Versioning

Every resume receives:

- Unique ID
- Version number
- Creation/update timestamps
- Origin (see above)
- Generation metadata (for AI-generated/tailored resumes)

Version snapshotting, comparison, duplication, and template selection were
removed in v2.1.1; the library exposes one list of resumes with origin badges.

# GET /{resume_id}/preview

## Purpose

Return a preview of the generated resume.

### Response

```json
{
  "success": true,
  "data": {
    "html": "<html>...</html>"
  }
}
```

Preview rendering is read-only.

---

# GET /{resume_id}/download

## Purpose

Download a generated resume.

### Path Parameters

| Parameter | Description |
|-----------|-------------|
| format | `json`, `pdf`, or `docx` |

Example

```
GET /api/v1/resumes/{resume_id}/download/pdf
```

---

# Resume Versioning

Every resume receives:

- Unique ID
- Version number
- Creation/update timestamps
- Origin (see above)
- Generation metadata (for AI-generated/tailored resumes)

Version snapshotting, comparison, duplication, and template selection were
removed in v2.1.1; the library exposes one list of resumes with origin badges.

---

# Validation Rules

Validation includes:

- Career Profile completeness
- Required sections
- Valid template
- Existing target job (if supplied)
- AI output schema
- Unsupported content detection

---

# Business Rules

- Career Profile is the only authoritative source.
- AI must not fabricate experience, education, certifications, or skills.
- Every generation creates a new version.
- Existing versions remain unchanged.
- Downloads always reference a specific version.
- Resume deletion archives instead of permanently removing by default.

---

# Error Codes

| Code | Description |
|------|-------------|
| RESUME_NOT_FOUND | Resume not found |
| INVALID_TEMPLATE | Unknown template |
| PROFILE_INCOMPLETE | Career Profile incomplete |
| GENERATION_FAILED | AI generation failed |
| VALIDATION_FAILED | Resume validation failed |
| DOWNLOAD_FAILED | Resume download failed |

---

# Audit Events

The following events should be recorded:

- Resume generated
- Resume previewed
- Resume downloaded
- Resume archived
- Resume restored
- Resume duplicated
- Template changed

---

# Related Documents

- API-Overview.md
- Career-Profile.md
- Functional-Requirements.md
- AI-Architecture.md
- Prompt-Engineering.md

---

End of Document
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
| GET | / | List resumes |
| POST | /generate | Generate resume |
| GET | /{resume_id} | Get resume |
| PATCH | /{resume_id} | Update metadata |
| DELETE | /{resume_id} | Archive resume |
| POST | /{resume_id}/restore | Restore archived resume |
| POST | /{resume_id}/duplicate | Duplicate resume |
| GET | /{resume_id}/preview | Preview resume |
| GET | /{resume_id}/download | Download resume |
| GET | /compare | Compare resume versions |
| GET | /templates | List templates |
| POST | /templates/select | Select template |

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

# POST /{resume_id}/duplicate

## Purpose

Create a duplicate of an existing resume.

### Use Cases

- Creating role-specific variants
- Testing different templates
- Manual editing

---

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

### Query Parameters

| Parameter | Description |
|-----------|-------------|
| format | pdf (default), docx (future) |

Example

```
GET /api/v1/resumes/{resume_id}/download?format=pdf
```

---

# GET /compare

## Purpose

Compare two resume versions.

### Example

```
GET /compare?left=uuid1&right=uuid2
```

### Response

```json
{
  "success": true,
  "data": {
    "left_version": 4,
    "right_version": 5,
    "changes": [
      {
        "section": "Professional Summary",
        "change": "Updated wording for Backend Developer role."
      }
    ]
  }
}
```

---

# GET /templates

## Purpose

List available resume templates.

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "modern",
      "name": "Modern"
    },
    {
      "id": "professional",
      "name": "Professional"
    }
  ]
}
```

---

# POST /templates/select

## Purpose

Set the default resume template.

### Request

```json
{
  "template": "Modern"
}
```

---

# Resume Versioning

Every generated resume receives:

- Unique ID
- Version number
- Creation timestamp
- Generation metadata
- Template information

Versions are immutable.

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
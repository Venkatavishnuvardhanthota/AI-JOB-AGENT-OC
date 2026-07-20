# Applications API

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Applications API |
| Version | 2.0 |
| Status | Approved |
| Base Path | /api/v1/applications |
| Related Documents | API-Overview.md, Resume.md, Jobs.md, Functional-Requirements.md |

---

# Purpose

This document defines the REST API for preparing, reviewing, submitting, tracking, and managing job applications.

The Applications API coordinates:

- Application preparation
- Resume selection
- Cover letter generation
- AI-generated application answers
- Manual review
- Manual submission
- Automated submission
- Status tracking
- Timeline history
- Attachments

---

# Authentication

All endpoints require authentication.

```
Authorization: Bearer <access_token>
```

---

# Responsibilities

The Applications API manages:

- Application creation
- Application review
- Submission
- Status updates
- Timeline history
- Resume selection
- Cover letter selection
- Attachments
- AI-generated responses
- Notes

---

# Endpoint Overview

| Method | Endpoint | Purpose |
|---------|----------|----------|
| GET | / | List applications |
| POST | /prepare | Prepare application |
| GET | /{application_id} | Get application |
| PATCH | /{application_id} | Update application |
| POST | /{application_id}/submit | Submit application |
| POST | /{application_id}/cancel | Cancel application |
| GET | /{application_id}/timeline | Timeline |
| GET | /{application_id}/status | Status |
| POST | /{application_id}/answers | Generate AI answers |
| POST | /{application_id}/cover-letter | Generate cover letter |
| POST | /{application_id}/attachments | Upload attachment |
| DELETE | /{application_id}/attachments/{attachment_id} | Remove attachment |

---

# Application Lifecycle

```text
Job
 │
 ▼
Prepare Application
 │
 ▼
Generate Resume
 │
 ▼
Generate Cover Letter
 │
 ▼
Generate AI Answers
 │
 ▼
Review Queue
 │
 ▼
Submit
 │
 ▼
Track Status
 │
 ▼
Completed
```

---

# GET /

## Purpose

Return all applications.

### Query Parameters

| Parameter | Description |
|------------|-------------|
| status | Application status |
| company | Company name |
| search | Keyword search |
| page | Page number |
| page_size | Results per page |
| sort | Sort field |

---

### Example Response

```json
{
  "success": true,
  "data": [
    {
      "application_id": "uuid",
      "company": "Example Inc",
      "job_title": "Backend Developer",
      "status": "Submitted",
      "submitted_at": "2026-07-20T10:00:00Z"
    }
  ]
}
```

---

# POST /prepare

## Purpose

Prepare an application package.

### Request

```json
{
  "job_id": "uuid",
  "resume_id": "uuid",
  "generate_cover_letter": true,
  "generate_ai_answers": true
}
```

---

### Processing Flow

```text
Job
 │
 ▼
Resume Selection
 │
 ▼
Cover Letter Generation
 │
 ▼
AI Question Answers
 │
 ▼
Validation
 │
 ▼
Review Queue
```

---

### Success Response

```json
{
  "success": true,
  "data": {
    "application_id": "uuid",
    "status": "Ready for Review"
  }
}
```

---

# GET /{application_id}

## Purpose

Retrieve complete application details.

### Response

```json
{
  "success": true,
  "data": {
    "application_id": "uuid",
    "job": {},
    "resume": {},
    "cover_letter": {},
    "answers": [],
    "attachments": [],
    "status": "Ready for Review"
  }
}
```

---

# PATCH /{application_id}

## Purpose

Update editable application metadata.

Editable fields include:

- Notes
- Labels
- Priority
- Review status

Generated documents are updated through their own APIs.

---

# POST /{application_id}/submit

## Purpose

Submit the prepared application.

Submission may occur:

- Manually
- Through browser automation
- Through supported provider integrations

---

### Success Response

```json
{
  "success": true,
  "data": {
    "status": "Submitted",
    "submitted_at": "2026-07-20T12:45:00Z"
  }
}
```

---

# POST /{application_id}/cancel

## Purpose

Cancel a prepared application before submission.

### Business Rules

- Submitted applications cannot be cancelled through this endpoint.
- Cancellation preserves application history.

---

# GET /{application_id}/status

## Purpose

Return the current application status.

Example

```json
{
  "success": true,
  "data": {
    "status": "Interview",
    "last_updated": "2026-07-25T14:10:00Z"
  }
}
```

---

# GET /{application_id}/timeline

## Purpose

Return the complete application timeline.

### Example Response

```json
{
  "success": true,
  "data": [
    {
      "event": "Application Prepared",
      "timestamp": "..."
    },
    {
      "event": "Submitted",
      "timestamp": "..."
    },
    {
      "event": "Interview Scheduled",
      "timestamp": "..."
    }
  ]
}
```

---

# POST /{application_id}/answers

## Purpose

Generate AI-powered answers for application questions.

### Request

```json
{
  "questions": [
    "Why do you want to work here?"
  ]
}
```

### Business Rules

- Answers are generated using verified Career Profile information.
- AI responses require user review before submission.
- Generated answers are stored with the application for traceability.

---

# POST /{application_id}/cover-letter

## Purpose

Generate a job-specific cover letter.

### Request

```json
{
  "template": "Professional"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "cover_letter_id": "uuid",
    "status": "Generated"
  }
}
```

---

# POST /{application_id}/attachments

## Purpose

Upload additional application attachments.

Supported file types:

- PDF
- DOCX
- ZIP (optional configuration)

Maximum upload size is configurable.

---

# DELETE /{application_id}/attachments/{attachment_id}

## Purpose

Remove an uploaded attachment before submission.

---

# Supported Application Statuses

- Draft
- Ready for Review
- Submitted
- Under Review
- Assessment
- Interview
- Offer
- Rejected
- Withdrawn
- Closed

---

# Validation Rules

Validation includes:

- Valid job reference
- Valid resume reference
- Required documents present
- File type validation
- File size validation
- Duplicate submission prevention

---

# Business Rules

- Every application references exactly one job.
- Every submitted application references a specific resume version.
- Cover letters are optional unless required by the job.
- AI-generated answers require user approval before submission.
- Application history is immutable.
- Duplicate submissions to the same job should be prevented unless explicitly overridden.

---

# Error Codes

| Code | Description |
|------|-------------|
| APPLICATION_NOT_FOUND | Application does not exist |
| INVALID_STATUS | Invalid application status |
| SUBMISSION_FAILED | Submission failed |
| DUPLICATE_APPLICATION | Application already exists |
| ATTACHMENT_INVALID | Invalid attachment |
| ATTACHMENT_TOO_LARGE | Attachment exceeds limit |
| ANSWER_GENERATION_FAILED | AI answer generation failed |
| COVER_LETTER_GENERATION_FAILED | Cover letter generation failed |

---

# Audit Events

The following events should be recorded:

- Application prepared
- Resume selected
- Cover letter generated
- AI answers generated
- Attachment uploaded
- Attachment removed
- Application submitted
- Application cancelled
- Status changed
- Timeline updated

---

# Related Documents

- API-Overview.md
- Resume.md
- Jobs.md
- Career-Profile.md
- Functional-Requirements.md
- Application-Pipeline.md

---

End of Document
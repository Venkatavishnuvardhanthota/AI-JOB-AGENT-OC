# API Overview

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | API Overview |
| Version | 2.0 |
| Status | Approved |
| Related Documents | System-Architecture.md, Functional-Requirements.md, Module-Architecture.md |

---

# Purpose

This document defines the REST API standards for AI Job Agent Version 2.

It establishes:

- API design principles
- Versioning strategy
- Authentication
- Request/response standards
- Error handling
- Pagination
- Filtering
- Sorting
- Idempotency
- API lifecycle

Individual endpoints are documented separately in dedicated API documents.

---

# API Goals

The API shall be:

- RESTful
- Stateless
- Versioned
- Secure
- Consistent
- Predictable
- Well documented
- Easy to extend
- Easy to test

---

# Base URL

Development

```
http://localhost:8000/api/v1
```

Production

```
https://<your-domain>/api/v1
```

All endpoints are versioned.

Future breaking changes shall introduce:

```
/api/v2
```

---

# API Categories

| Category | Document |
|----------|----------|
| Authentication | Authentication.md |
| Career Profile | Career-Profile.md |
| Resume Studio | Resume.md |
| Jobs | Jobs.md |
| Applications | Applications.md |

---

# REST Principles

The API follows REST conventions.

| Method | Purpose |
|---------|----------|
| GET | Retrieve data |
| POST | Create resources |
| PUT | Replace resources |
| PATCH | Partial update |
| DELETE | Delete resources |

---

# Resource Naming

Use nouns.

Good

```
/users
/resumes
/jobs
/applications
```

Avoid

```
/getJobs
/createResume
/deleteProfile
```

---

# Versioning

Current version

```
v1
```

Breaking changes require

```
v2
```

Minor improvements remain inside the current version.

---

# Authentication

Authentication uses Bearer Tokens.

Example

```
Authorization: Bearer <access_token>
```

Unauthenticated requests return

```
401 Unauthorized
```

Forbidden requests return

```
403 Forbidden
```

---

# Content Type

Requests

```
Content-Type: application/json
```

Responses

```
application/json
```

Multipart uploads are used only for file upload endpoints.

---

# Request Format

Example

```json
{
  "title": "Backend Developer",
  "location": "Remote"
}
```

---

# Standard Success Response

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully."
}
```

---

# Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Required field missing."
  }
}
```

---

# HTTP Status Codes

| Code | Meaning |
|------|----------|
| 200 | Success |
| 201 | Resource Created |
| 202 | Accepted |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

# Pagination

List endpoints shall support pagination.

Example

```
GET /jobs?page=1&page_size=25
```

Response

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_items": 280,
    "total_pages": 12
  }
}
```

---

# Sorting

Example

```
GET /jobs?sort=match_score
```

Descending

```
GET /jobs?sort=-match_score
```

---

# Filtering

Examples

```
GET /jobs?location=Remote
```

```
GET /jobs?employment_type=Full-Time
```

```
GET /jobs?minimum_match=80
```

Multiple filters may be combined.

---

# Search

Example

```
GET /jobs?search=python
```

Search behavior should be documented per endpoint.

---

# Field Selection (Future)

Example

```
GET /jobs?fields=id,title,company
```

---

# Idempotency

The following operations should be idempotent where applicable:

- Resume generation requests using an idempotency key
- Application submission requests
- Scheduler execution triggers

Clients may send:

```
Idempotency-Key:
```

to avoid duplicate processing.

---

# Validation

Every request shall be validated before business logic executes.

Validation includes:

- Required fields
- Data types
- Length constraints
- Business rules
- Authorization

---

# Rate Limiting

Sensitive endpoints may be rate limited.

Examples

- Login
- Password reset
- AI generation
- Resume upload

When exceeded

```
429 Too Many Requests
```

---

# File Uploads

Supported upload endpoints use

```
multipart/form-data
```

Supported file types

- PDF
- DOCX (future)

Maximum file size is configurable.

---

# Long-Running Operations

Operations such as:

- Resume generation
- Company research
- AI analysis
- Job discovery

should execute asynchronously when appropriate.

Clients should receive progress or status updates.

---

# Error Categories

Standard error codes include:

- VALIDATION_ERROR
- AUTHENTICATION_ERROR
- AUTHORIZATION_ERROR
- RESOURCE_NOT_FOUND
- DUPLICATE_RESOURCE
- BUSINESS_RULE_VIOLATION
- AI_PROVIDER_ERROR
- PROVIDER_UNAVAILABLE
- INTERNAL_ERROR

---

# API Security

The API shall enforce:

- Authentication
- Authorization
- HTTPS
- Input validation
- Output sanitization where applicable
- Rate limiting
- Audit logging

---

# API Documentation

Every endpoint document shall include:

- Purpose
- Route
- Method
- Authentication
- Request schema
- Response schema
- Error responses
- Business rules
- Examples

---

# API Lifecycle

```
Client
   │
   ▼
Validation
   │
   ▼
Authentication
   │
   ▼
Authorization
   │
   ▼
Business Service
   │
   ▼
Repository
   │
   ▼
Database
   │
   ▼
Response
```

---

# Backward Compatibility

Breaking API changes require a new version.

Non-breaking additions may be introduced within the current version.

Deprecated endpoints should remain available during the defined deprecation period before removal.

---

# Acceptance Criteria

The API design is considered complete when:

- All endpoints follow consistent naming.
- Requests and responses use standardized formats.
- Authentication and authorization are enforced.
- Error handling is predictable.
- Versioning strategy is documented.
- Endpoint-specific behavior is documented in dedicated API files.

---

# Related Documents

- Authentication.md
- Career-Profile.md
- Resume.md
- Jobs.md
- Applications.md
- Functional-Requirements.md
- System-Architecture.md

---

End of Document
# API Integration

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | API Integration |
| Version | 2.0 |
| Status | Approved |
| Related Documents | Frontend-Architecture.md, State-Management.md, API/API-Overview.md |

---

# Purpose

This document defines how the frontend communicates with the backend APIs.

It standardizes:

- API client architecture
- Authentication
- Request lifecycle
- Response handling
- Error handling
- File uploads
- Query integration
- Retry policies
- Request cancellation
- Type safety

All communication with the backend must follow this specification.

---

# Design Principles

API integration shall be:

- Centralized
- Type-safe
- Predictable
- Testable
- Secure
- Resilient
- Observable

Components should never communicate with the backend directly.

---

# Architecture

```text
React Component
        │
        ▼
Feature Hook
        │
        ▼
TanStack Query
        │
        ▼
API Client
        │
        ▼
Authentication Layer
        │
        ▼
FastAPI Backend
```

Every request should pass through the centralized API client.

---

# API Client

The API client is responsible for:

- Base URL configuration
- Authentication headers
- JSON serialization
- Error normalization
- Timeout handling
- Retry coordination
- Request cancellation
- Response typing

Business logic must never exist inside the API client.

---

# Folder Structure

```text
src/

api/

├── client.ts
├── auth.ts
├── profile.ts
├── resumes.ts
├── jobs.ts
├── applications.ts
├── scheduler.ts
├── notifications.ts
└── settings.ts
```

Each module should expose typed API functions for its feature.

---

# Request Lifecycle

```text
Component

↓

Feature Hook

↓

TanStack Query

↓

API Client

↓

HTTP Request

↓

Backend

↓

HTTP Response

↓

API Client

↓

TanStack Query Cache

↓

Component
```

---

# Authentication

Authenticated requests should automatically include:

```
Authorization: Bearer <token>
```

The authentication mechanism should be transparent to feature components.

---

# Token Refresh

When an access token expires:

```text
API Request

↓

401 Unauthorized

↓

Refresh Token

↓

Success?

├── Yes → Retry Request
└── No → Logout User
```

Only one refresh operation should occur at a time to avoid duplicate refresh requests.

---

# Request Configuration

Each request should support:

- Headers
- Query parameters
- Path parameters
- Request body
- Timeout
- Cancellation
- Multipart uploads

Reasonable defaults should be applied centrally.

---

# Typed Requests

Every request should have:

- Typed request model
- Typed response model
- Typed error model

Avoid using untyped data structures for API communication.

---

# Query Integration

TanStack Query should manage:

- Data fetching
- Caching
- Refetching
- Mutations
- Background synchronization

Feature hooks should wrap query usage to avoid duplication.

---

# Query Keys

Examples:

```text
["profile"]

["jobs"]

["jobs", filters]

["applications"]

["resume", id]

["notifications"]
```

Query keys should remain stable and deterministic.

---

# Mutations

Mutations include:

- Create profile
- Update profile
- Generate resume
- Submit application
- Save job
- Archive resume
- Mark notification as read

Mutations should invalidate only affected queries.

---

# Optimistic Updates

Suitable operations include:

- Save job
- Remove saved job
- Archive resume
- Toggle scheduler
- Mark notification as read

Rollback should occur automatically if the server rejects the change.

---

# Error Handling

The API client should normalize all errors into a common format.

Example:

```text
ApiError

↓

status

code

message

details

requestId
```

Feature components should not interpret raw HTTP responses directly.

---

# HTTP Status Handling

## 200–299

Successful request.

---

## 400

Display validation feedback.

---

## 401

Attempt token refresh.

If refresh fails:

- Clear session
- Redirect to login

---

## 403

Display authorization error.

---

## 404

Display resource not found.

---

## 409

Display conflict information.

Examples:

- Duplicate application
- Duplicate email

---

## 429

Display rate limit message.

Allow retry when appropriate.

---

## 500+

Display generic error.

Offer retry when practical.

---

# Retry Policy

Automatic retries should be limited to transient failures.

Retryable examples:

- Network interruption
- Timeout
- Temporary service unavailable

Non-retryable examples:

- Validation failure
- Authentication failure
- Authorization failure
- Business rule violations

Retry limits and delays should be configurable.

---

# Request Cancellation

Long-running requests should support cancellation.

Examples:

- Job search
- Resume generation status polling
- Company search
- Dashboard refresh

Cancellation prevents unnecessary network activity and stale updates.

---

# Timeout Strategy

Every request should define a timeout.

Suggested categories:

| Request Type | Typical Timeout |
|--------------|-----------------|
| Standard API | Short |
| File Upload | Medium |
| AI Generation | Long |
| Browser Automation Status | Long |

Timeout values should be configurable rather than hardcoded.

---

# File Uploads

Supported uploads include:

- Resume
- Cover letter
- Portfolio
- Certificates
- Supporting documents

Requirements:

- Multipart requests
- Progress indicators
- Size validation
- Type validation
- Graceful failure handling

---

# Download Handling

Supported downloads include:

- Resume PDF
- Resume DOCX
- Cover letter
- Reports

Downloads should preserve filenames supplied by the backend where appropriate.

---

# Pagination

Server-driven pagination should include:

- Current page
- Page size
- Total records
- Total pages

The frontend should avoid requesting unnecessary data.

---

# Filtering

Filters should be transmitted as query parameters.

Examples:

```text
location=Remote

experience=Entry

employment=Full-Time

salaryMin=60000
```

Filter state should remain synchronized with the URL when appropriate.

---

# Sorting

Sorting should use explicit parameters.

Examples:

```text
sort=match

sort=postedAt

sort=salary
```

The backend remains responsible for sorting correctness.

---

# API Versioning

The frontend should target a specific API version.

Example:

```text
/api/v1/
```

Version-specific behavior should be isolated within the API layer.

---

# Logging

Development builds may log:

- Request start
- Request end
- Duration
- Status code

Production logging should avoid exposing sensitive information.

---

# Security

The API client shall:

- Never expose API keys
- Never store secrets
- Send authentication only to trusted endpoints
- Validate upload types before transmission
- Handle expired sessions safely

All authorization decisions remain the responsibility of the backend.

---

# Testing

API integration tests should verify:

- Successful requests
- Error handling
- Token refresh
- Query invalidation
- Optimistic updates
- File uploads
- Request cancellation
- Retry behavior

External services should be mocked during automated tests.

---

# Acceptance Criteria

The API integration layer is considered complete when:

- All requests use the centralized API client.
- Authentication is handled automatically.
- Errors are normalized.
- Requests and responses are fully typed.
- TanStack Query manages server state.
- File uploads and downloads are supported.
- API communication is independently testable.

---

# Related Documents

- Frontend-Architecture.md
- State-Management.md
- Routing.md
- API/API-Overview.md
- Backend/Backend-Architecture.md

---

End of Document
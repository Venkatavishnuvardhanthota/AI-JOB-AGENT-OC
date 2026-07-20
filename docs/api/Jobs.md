# Jobs API

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Jobs API |
| Version | 2.0 |
| Status | Approved |
| Base Path | /api/v1/jobs |
| Related Documents | API-Overview.md, Functional-Requirements.md, Business-Rules.md |

---

# Purpose

This document defines the REST API for job discovery, job management, AI-powered job matching, company insights, bookmarking, recommendations, and provider integration.

The Jobs API provides a normalized interface regardless of which external job provider supplies the data.

---

# Authentication

All endpoints require authentication.

```
Authorization: Bearer <access_token>
```

---

# Responsibilities

The Jobs API manages:

- Job search
- Job retrieval
- AI match scoring
- Job recommendations
- Saved jobs
- Company insights
- Duplicate detection
- Job filtering
- Job sorting
- Provider normalization

---

# Endpoint Overview

| Method | Endpoint | Purpose |
|---------|----------|----------|
| GET | /search | Search jobs |
| GET | /recommended | AI recommendations |
| GET | /saved | List saved jobs |
| POST | /saved | Save job |
| DELETE | /saved/{job_id} | Remove saved job |
| GET | /{job_id} | Job details |
| GET | /{job_id}/match | Match analysis |
| GET | /{job_id}/company | Company insights |
| GET | /providers | List providers |
| POST | /refresh | Refresh cached jobs |

---

# GET /search

## Purpose

Search available jobs.

### Query Parameters

| Parameter | Description |
|------------|-------------|
| search | Keywords |
| location | Location |
| remote | Remote only |
| employment_type | Full-Time, Internship, Contract |
| experience_level | Entry, Mid, Senior |
| provider | Job provider |
| page | Page number |
| page_size | Results per page |
| sort | Sorting field |

### Example

```
GET /api/v1/jobs/search?search=python&location=Remote&page=1
```

### Success Response

```json
{
  "success": true,
  "data": [
    {
      "job_id": "uuid",
      "title": "Backend Developer",
      "company": "Example Inc",
      "location": "Remote",
      "match_score": 91,
      "provider": "LinkedIn"
    }
  ]
}
```

---

# GET /recommended

## Purpose

Return AI-ranked job recommendations.

Recommendations are generated using:

- Career Profile
- Skills
- Experience
- Job Preferences
- Match Engine

### Example Response

```json
{
  "success": true,
  "data": [
    {
      "job_id": "uuid",
      "match_score": 96,
      "reason": "Excellent match for your Python and FastAPI experience."
    }
  ]
}
```

---

# GET /saved

## Purpose

Return bookmarked jobs.

### Response

```json
{
  "success": true,
  "data": [
    {
      "job_id": "uuid",
      "saved_at": "2026-07-20T08:00:00Z"
    }
  ]
}
```

---

# POST /saved

## Purpose

Bookmark a job.

### Request

```json
{
  "job_id": "uuid"
}
```

### Business Rules

- Duplicate bookmarks are ignored.
- Only authenticated users may save jobs.

---

# DELETE /saved/{job_id}

## Purpose

Remove a bookmarked job.

### Success

**204 No Content**

---

# GET /{job_id}

## Purpose

Retrieve complete job details.

### Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Backend Developer",
    "company": "Example Inc",
    "description": "...",
    "requirements": [],
    "location": "Remote",
    "salary": {
      "min": 1200000,
      "max": 1800000,
      "currency": "INR"
    },
    "employment_type": "Full-Time",
    "provider": "LinkedIn",
    "posted_at": "2026-07-18T09:00:00Z",
    "application_url": "https://..."
  }
}
```

---

# GET /{job_id}/match

## Purpose

Return detailed AI match analysis.

### Response

```json
{
  "success": true,
  "data": {
    "score": 92,
    "confidence": 0.94,
    "strengths": [
      "Python",
      "FastAPI"
    ],
    "skill_gaps": [
      "AWS"
    ],
    "summary": "Strong overall fit with one notable skill gap."
  }
}
```

---

# GET /{job_id}/company

## Purpose

Return AI-generated company insights.

### Response

```json
{
  "success": true,
  "data": {
    "company": "Example Inc",
    "industry": "Software",
    "size": "500-1000",
    "summary": "AI-generated overview of the company.",
    "culture": "Collaborative",
    "headquarters": "Bangalore"
  }
}
```

---

# GET /providers

## Purpose

Return supported job providers.

### Response

```json
{
  "success": true,
  "data": [
    {
      "name": "LinkedIn",
      "status": "enabled"
    },
    {
      "name": "Greenhouse",
      "status": "enabled"
    },
    {
      "name": "Workday",
      "status": "enabled"
    }
  ]
}
```

---

# POST /refresh

## Purpose

Trigger a refresh of cached job listings.

### Behavior

- Starts an asynchronous refresh.
- Returns immediately with a task identifier.

### Response

```json
{
  "success": true,
  "data": {
    "task_id": "uuid",
    "status": "queued"
  }
}
```

---

# Filtering

Supported filters include:

- Location
- Remote
- Employment type
- Experience level
- Salary range
- Match score
- Provider
- Posted date

Filters may be combined.

---

# Sorting

Supported sort fields:

- Match score
- Posted date
- Company
- Salary
- Title

Descending order is indicated with a leading `-`.

Example

```
GET /search?sort=-match_score
```

---

# Pagination

All list endpoints support:

```text
page
page_size
```

Responses include pagination metadata.

---

# Business Rules

- Jobs from different providers are normalized into a common schema.
- Duplicate jobs should be detected and merged where appropriate.
- Match scores are generated using the current verified Career Profile.
- Job recommendations are personalized for the authenticated user.
- Company insights are informational and may be AI-generated.

---

# Error Codes

| Code | Description |
|------|-------------|
| JOB_NOT_FOUND | Job does not exist |
| INVALID_PROVIDER | Unsupported provider |
| SEARCH_FAILED | Job search failed |
| MATCH_FAILED | Match analysis failed |
| COMPANY_RESEARCH_FAILED | Company insight generation failed |
| DUPLICATE_BOOKMARK | Job already saved |

---

# Audit Events

The following events should be recorded:

- Job searched
- Job viewed
- Job bookmarked
- Bookmark removed
- Match analysis requested
- Company insights viewed
- Recommendations generated
- Provider refresh initiated

---

# Related Documents

- API-Overview.md
- Functional-Requirements.md
- Business-Rules.md
- AI-Architecture.md
- Provider-Framework.md
- Company-Intelligence.md

---

End of Document
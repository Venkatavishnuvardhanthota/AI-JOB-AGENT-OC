# Data Flow

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Data Flow |
| Version | 2.0 |
| Status | Approved |
| Related Documents | System-Architecture.md, Module-Architecture.md, Sequence-Diagrams.md |

---

# Purpose

This document describes how data flows through AI Job Agent Version 2.

It defines:

- Data producers
- Data consumers
- Processing stages
- Storage points
- External interactions
- Validation checkpoints

The goal is to ensure every workflow follows a consistent, traceable, and secure path from input to output.

---

# High-Level Data Flow

```text
                User
                  │
                  ▼
           React Frontend
                  │
                  ▼
            FastAPI Backend
                  │
      ┌───────────┼────────────┐
      ▼           ▼            ▼
Career Profile  Job Search   Scheduler
      │           │            │
      └──────┬────┴────────────┘
             ▼
      Application Services
             │
             ▼
      AI Orchestrator
             │
     ┌───────┼─────────┐
     ▼       ▼         ▼
AI Models  Job APIs  Playwright
     │       │         │
     └───────┼─────────┘
             ▼
        PostgreSQL
             │
             ▼
      Dashboard & Reports
```

---

# Data Flow Principles

Every workflow shall follow these principles:

- Validate input before processing.
- Use the Career Profile as the authoritative user data source.
- Store only normalized data.
- Avoid duplicate records.
- Record important events.
- Never expose sensitive information unnecessarily.
- Treat AI output as untrusted until validated.

---

# Workflow DF-001 — User Registration

## Input

- Registration form
- Email
- Password
- Basic profile information

## Processing

1. Validate input.
2. Check for duplicate account.
3. Hash password.
4. Create user record.
5. Initialize profile.
6. Generate audit entry.

## Output

- User account
- Initial Career Profile
- Authentication response

---

# Workflow DF-002 — User Login

## Input

- Credentials

## Processing

1. Validate credentials.
2. Authenticate user.
3. Create session/token.
4. Record login event.

## Output

- Authenticated session

---

# Workflow DF-003 — Career Profile Update

```text
User
 │
 ▼
Career Profile Form
 │
 ▼
Validation
 │
 ▼
Business Rules
 │
 ▼
Database
 │
 ▼
Profile Updated
```

## Processing Steps

1. Receive update request.
2. Validate fields.
3. Apply business rules.
4. Persist changes.
5. Update timestamps.
6. Record audit log.

---

# Workflow DF-004 — Resume Import

## Input

- Uploaded resume

## Processing

```text
Resume
   │
   ▼
File Validation
   │
   ▼
Text Extraction
   │
   ▼
AI Extraction
   │
   ▼
Structured Data
   │
   ▼
User Review
   │
   ▼
Career Profile
```

## Validation

- Supported file type
- Maximum file size
- Readable content

## Important Rule

Extracted data shall **not** be persisted until confirmed by the user.

---

# Workflow DF-005 — Resume Generation

```text
Career Profile
       │
       ▼
Target Job
       │
       ▼
AI Orchestrator
       │
       ▼
Prompt Builder
       │
       ▼
AI Provider
       │
       ▼
Validation
       │
       ▼
Resume Version
       │
       ▼
Database
```

## Inputs

- Career Profile
- Job Description
- Resume Template

## Outputs

- Resume PDF
- Resume Version
- Resume Metadata

---

# Workflow DF-006 — Job Discovery

```text
Scheduler / User
        │
        ▼
Provider Adapter
        │
        ▼
Raw Jobs
        │
        ▼
Normalization
        │
        ▼
Duplicate Removal
        │
        ▼
Database
        │
        ▼
Match Engine
```

## Processing

1. Search providers.
2. Retrieve jobs.
3. Normalize fields.
4. Remove duplicates.
5. Store jobs.
6. Trigger matching.

---

# Workflow DF-007 — Match Engine

## Inputs

- Career Profile
- Job
- AI Analysis

## Processing

```text
Job
 │
 ▼
Skill Comparison
 │
 ▼
Experience Comparison
 │
 ▼
Preference Comparison
 │
 ▼
AI Analysis
 │
 ▼
Match Score
```

## Outputs

- Match percentage
- Skill gaps
- Explanation
- Confidence score

---

# Workflow DF-008 — Company Intelligence

## Inputs

- Company name
- Job metadata

## Processing

1. Gather company information.
2. Summarize relevant details.
3. Validate AI response.
4. Cache results if appropriate.

## Outputs

- Company summary
- Industry
- Hiring insights
- Additional metadata

---

# Workflow DF-009 — Application Preparation

```text
Career Profile
       │
       ▼
Resume Studio
       │
       ▼
Cover Letter
       │
       ▼
AI Answers
       │
       ▼
Validation
       │
       ▼
Application Package
```

## Outputs

- Resume
- Cover Letter
- AI-generated responses
- Metadata

---

# Workflow DF-010 — Manual Submission

```text
Prepared Application
        │
        ▼
Review Queue
        │
        ▼
User Approval
        │
        ▼
Playwright
        │
        ▼
Job Website
        │
        ▼
Submission Result
```

## Postconditions

- Application status updated.
- Timeline recorded.
- Notification generated.

---

# Workflow DF-011 — Scheduled Automation

```text
Scheduler
     │
     ▼
Search Jobs
     │
     ▼
Match Jobs
     │
     ▼
Prepare Applications
     │
     ▼
Manual Review?
     │
 ┌───┴────────────┐
 ▼                ▼
Yes              No
 │                │
 ▼                ▼
Review Queue   Auto Submit
 │                │
 └──────┬─────────┘
        ▼
Notifications
```

---

# Workflow DF-012 — Application Tracking

## Sources

- Browser automation
- User updates
- Provider updates (future)

## Processing

1. Receive status.
2. Validate transition.
3. Store timeline.
4. Update dashboard.

---

# Workflow DF-013 — Analytics

```text
Applications
Jobs
Resumes
Scheduler
Logs
      │
      ▼
Analytics Engine
      │
      ▼
Dashboard
```

## Metrics

- Applications submitted
- Interviews
- Offers
- Match scores
- Provider success
- Automation performance

---

# AI Data Flow

```text
Business Module
        │
        ▼
AI Orchestrator
        │
        ▼
Prompt Builder
        │
        ▼
AI Provider
        │
        ▼
Response Validation
        │
        ▼
Structured Result
        │
        ▼
Business Module
```

Business modules must never communicate directly with AI providers.

---

# Database Flow

```text
API
 │
 ▼
Application Service
 │
 ▼
Repository
 │
 ▼
Database
 │
 ▼
Repository
 │
 ▼
Application Service
 │
 ▼
API Response
```

Direct database access from controllers or UI is prohibited.

---

# Error Flow

```text
Operation
    │
    ▼
Validation
    │
 ┌──┴─────────────┐
 │                │
Pass            Fail
 │                │
 ▼                ▼
Continue      Error Response
 │                │
 ▼                ▼
Audit Log    Audit Log
```

All errors should be classified, logged, and returned with meaningful context where appropriate.

---

# Audit Flow

The following events shall generate audit records:

- User registration
- Login
- Profile updates
- Resume generation
- Job discovery
- Match calculation
- Application preparation
- Application submission
- Scheduler execution
- Configuration changes

Each audit record should include:

- Timestamp
- User ID (if applicable)
- Event type
- Outcome
- Correlation ID (if available)

---

# Data Ownership

| Data | Owning Module |
|------|---------------|
| User Accounts | Authentication |
| Career Profile | Career Profile |
| Resume Versions | Resume Studio |
| AI Requests | AI Orchestrator |
| Job Listings | Job Discovery |
| Match Scores | Match Engine |
| Company Data | Company Intelligence |
| Applications | Application Pipeline |
| Scheduler Runs | Scheduler |
| Notifications | Notifications |
| Analytics | Analytics |
| Audit Records | Audit & Logging |

---

# Data Integrity Rules

- Every entity shall have a unique identifier.
- Foreign key relationships shall remain valid.
- Duplicate jobs shall be detected before storage.
- Resume versions are immutable.
- AI-generated data shall be validated before persistence.
- Audit records shall not be modified after creation.

---

# Related Documents

- System-Architecture.md
- Module-Architecture.md
- Sequence-Diagrams.md
- Deployment-Architecture.md
- Technology-Stack.md
- Functional-Requirements.md
- Business-Rules.md

---

End of Document
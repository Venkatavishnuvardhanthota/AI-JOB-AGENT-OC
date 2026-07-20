# Sequence Diagrams

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Sequence Diagrams |
| Version | 2.0 |
| Status | Approved |
| Related Documents | System-Architecture.md, Module-Architecture.md, Data-Flow.md |

---

# Purpose

This document describes the runtime interaction between the major components of AI Job Agent Version 2.

Each sequence diagram represents one complete business workflow and illustrates:

- Participants
- Request flow
- Validation
- AI interactions
- Database interactions
- External providers
- Responses

---

# Participants

| Abbreviation | Component |
|-------------|-----------|
| User | End User |
| UI | React Frontend |
| API | FastAPI |
| Auth | Authentication Module |
| Profile | Career Profile |
| Resume | Resume Studio |
| AI | AI Orchestrator |
| Jobs | Job Discovery |
| Match | Match Engine |
| Company | Company Intelligence |
| Pipeline | Application Pipeline |
| Scheduler | Background Scheduler |
| Browser | Playwright |
| DB | PostgreSQL |
| Provider | Job Provider |
| LLM | AI Provider |

---

# SD-001 User Login

```text
User
 │
 ▼
UI
 │
 │ Login Request
 ▼
API
 │
 ▼
Authentication
 │
 │ Validate Credentials
 ▼
Database
 │
 │ User Found
 ▼
Authentication
 │
 │ Create Session
 ▼
API
 │
 ▼
UI
 │
 ▼
Dashboard
```

---

# SD-002 Career Profile Update

```text
User
 │
 ▼
UI
 │
 ▼
API
 │
 ▼
Career Profile Service
 │
 │ Validate Data
 ▼
Business Rules
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
API
 │
 ▼
UI
```

---

# SD-003 Resume Import

```text
User
 │
 ▼
Upload Resume
 │
 ▼
API
 │
 ▼
Resume Service
 │
 ▼
Text Extraction
 │
 ▼
AI Orchestrator
 │
 ▼
AI Provider
 │
 ▼
Structured Resume
 │
 ▼
User Review
 │
 ▼
Career Profile
 │
 ▼
Database
```

Important Rule:

User confirmation is required before any extracted data is stored.

---

# SD-004 Resume Generation

```text
User
 │
 ▼
Generate Resume
 │
 ▼
API
 │
 ▼
Resume Studio
 │
 │
 ▼
Career Profile
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
Structured Resume
 │
 ▼
Validation
 │
 ▼
Resume Version
 │
 ▼
Database
 │
 ▼
PDF Generation
 │
 ▼
User
```

---

# SD-005 Job Discovery

```text
User / Scheduler
 │
 ▼
Job Discovery
 │
 ▼
Provider Adapter
 │
 ▼
Job Provider
 │
 ▼
Raw Jobs
 │
 ▼
Normalization
 │
 ▼
Duplicate Detection
 │
 ▼
Database
 │
 ▼
Match Engine
```

---

# SD-006 Match Score Calculation

```text
Job
 │
 ▼
Match Engine
 │
 ▼
Career Profile
 │
 ▼
AI Orchestrator
 │
 ▼
AI Provider
 │
 ▼
Explanation
 │
 ▼
Score Calculation
 │
 ▼
Database
 │
 ▼
Dashboard
```

---

# SD-007 Company Research

```text
User
 │
 ▼
Company Intelligence
 │
 ▼
AI Orchestrator
 │
 ▼
AI Provider
 │
 ▼
Company Summary
 │
 ▼
Validation
 │
 ▼
Database (Cache)
 │
 ▼
Dashboard
```

---

# SD-008 Application Preparation

```text
Selected Job
 │
 ▼
Application Pipeline
 │
 ▼
Resume Studio
 │
 ▼
AI Orchestrator
 │
 ▼
Cover Letter
 │
 ▼
Application Answers
 │
 ▼
Validation
 │
 ▼
Application Package
 │
 ▼
Database
```

---

# SD-009 Manual Application Submission

```text
User
 │
 ▼
Review Queue
 │
 ▼
Approve
 │
 ▼
Application Pipeline
 │
 ▼
Playwright
 │
 ▼
Job Website
 │
 ▼
Submission Result
 │
 ▼
Database
 │
 ▼
Notification
```

---

# SD-010 Automatic Submission

```text
Scheduler
 │
 ▼
Job Discovery
 │
 ▼
Match Engine
 │
 ▼
Application Pipeline
 │
 ▼
Playwright
 │
 ▼
Job Website
 │
 ▼
Submission Status
 │
 ▼
Database
 │
 ▼
Notification Service
```

---

# SD-011 Scheduler Execution

```text
Scheduler
 │
 ▼
Load Schedule
 │
 ▼
Validate Schedule
 │
 ▼
Execute Workflow
 │
 ▼
Job Discovery
 │
 ▼
Match Engine
 │
 ▼
Prepare Applications
 │
 ▼
Review Queue / Auto Submit
 │
 ▼
Execution Log
```

---

# SD-012 Notification Flow

```text
Business Event
 │
 ▼
Notification Service
 │
 ├────────► In-App Notification
 │
 ├────────► Email Notification
 │
 └────────► Future Channels
```

---

# SD-013 Analytics Update

```text
Application Completed
 │
 ▼
Analytics Module
 │
 ▼
Metrics Aggregation
 │
 ▼
Database
 │
 ▼
Dashboard
```

---

# SD-014 AI Request Lifecycle

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
Provider Selection
 │
 ▼
AI Provider
 │
 ▼
Raw Response
 │
 ▼
Validation
 │
 ▼
Structured Response
 │
 ▼
Business Module
```

The AI Orchestrator is the only module permitted to communicate directly with AI providers.

---

# SD-015 Provider Failure Recovery

```text
Business Module
 │
 ▼
Provider Adapter
 │
 ▼
Provider
 │
 │
 ├──────── Success ───────► Continue
 │
 └──────── Failure
            │
            ▼
      Retry Policy
            │
      ┌─────┴─────┐
      ▼           ▼
 Retry OK     Retry Failed
      │           │
      ▼           ▼
 Continue    Record Failure
                 │
                 ▼
          Notify User (if required)
```

---

# SD-016 Authentication Failure

```text
User
 │
 ▼
Login Request
 │
 ▼
Authentication
 │
 │
 ├──────── Valid Credentials
 │              │
 │              ▼
 │          Dashboard
 │
 └──────── Invalid Credentials
                │
                ▼
         Failed Login Event
                │
                ▼
          Error Response
```

---

# SD-017 Error Handling Flow

```text
Operation
 │
 ▼
Validation
 │
 ├──────── Success
 │         │
 │         ▼
 │     Continue Workflow
 │
 └──────── Failure
           │
           ▼
     Error Classification
           │
           ▼
      Structured Response
           │
           ▼
      Audit & Logging
```

---

# SD-018 Complete End-to-End Workflow

```text
User
 │
 ▼
Login
 │
 ▼
Career Profile
 │
 ▼
Job Discovery
 │
 ▼
Match Engine
 │
 ▼
Company Research
 │
 ▼
Resume Generation
 │
 ▼
Cover Letter Generation
 │
 ▼
Application Preparation
 │
 ▼
Review Queue
 │
 ▼
Submission
 │
 ▼
Application Tracking
 │
 ▼
Analytics Dashboard
```

---

# Sequence Diagram Standards

All future sequence diagrams shall:

- Begin with a triggering actor.
- Clearly identify module boundaries.
- Show validation before persistence.
- Show AI interactions through the AI Orchestrator only.
- Show external providers through adapters.
- End with a measurable business outcome.
- Avoid direct module-to-module database access.

---

# Related Documents

- System-Architecture.md
- Module-Architecture.md
- Data-Flow.md
- Deployment-Architecture.md
- Technology-Stack.md
- Architecture-Decisions.md

---

End of Document
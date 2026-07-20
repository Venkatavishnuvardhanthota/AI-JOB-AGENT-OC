# Business Rules

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Business Rules |
| Version | 2.0 |
| Status | Approved for Implementation |
| Related Documents | PRD.md, Functional-Requirements.md, AI_CONTEXT.md |

---

# Purpose

This document defines the business rules governing AI Job Agent Version 2.

Business Rules (BR) describe mandatory constraints that every feature must follow regardless of implementation.

These rules are the highest-level behavioral constraints after the Product Requirements Document.

Business Rule identifiers are permanent.

---

# Rule Categories

| Prefix | Category |
|---------|----------|
| BR-001 – BR-019 | User Profile |
| BR-020 – BR-039 | Resume Generation |
| BR-040 – BR-059 | AI Behavior |
| BR-060 – BR-079 | Job Matching |
| BR-080 – BR-099 | Application Workflow |
| BR-100 – BR-119 | Automation |
| BR-120 – BR-139 | Data Integrity |
| BR-140 – BR-159 | Security |
| BR-160 – BR-179 | System Behavior |

---

# Career Profile Rules

## BR-001 Career Profile Source of Truth

The Career Profile is the single authoritative source of user information.

No module may maintain conflicting copies of user profile data.

---

## BR-002 Verified Information Only

AI-generated content shall use only information verified by the user.

---

## BR-003 No Fabrication

The system shall never invent:

- skills
- education
- certifications
- projects
- work experience
- achievements
- publications

---

## BR-004 User Confirmation

Information extracted from uploaded resumes shall not be stored until confirmed by the user.

---

## BR-005 Optional Sections

Optional profile fields shall never prevent users from using the application.

---

## BR-006 Profile Updates

Changes made to the Career Profile become immediately available to AI modules.

---

## BR-007 Deleted Information

Deleted profile information shall not appear in newly generated documents.

---

# Resume Rules

## BR-020 Resume Versioning

Every AI-generated resume shall create a new immutable version.

Existing versions shall never be overwritten.

---

## BR-021 Master Resume

One Master Resume shall exist as the primary reference.

---

## BR-022 Resume Selection

The AI shall select the most appropriate resume based on the target job.

---

## BR-023 Resume Editing

Users may edit generated resumes before submission.

---

## BR-024 ATS Compatibility

Generated resumes shall prioritize ATS-friendly formatting.

---

## BR-025 Restore

Users shall restore any previous resume version.

---

## BR-026 Archive

Archived resumes remain available but are excluded from default selections.

---

# AI Rules

## BR-040 Explainability

AI recommendations shall include an explanation where practical.

Examples include:

- Match score reasoning
- Skill gaps
- Resume tailoring rationale

---

## BR-041 Truthfulness

The AI shall prioritize factual accuracy over persuasive language.

---

## BR-042 Transparency

Users shall be informed when content is AI-generated.

---

## BR-043 Prompt Versioning

Every production prompt shall have a version identifier.

---

## BR-044 Model Independence

Business logic shall never depend on a specific AI model or provider.

---

## BR-045 Output Validation

AI outputs shall be validated before use.

---

## BR-046 Retry Strategy

Recoverable AI failures may be retried.

---

## BR-047 Fallback Models

Fallback models may be used when the preferred model is unavailable.

---

## BR-048 Logging

AI requests shall record:

- timestamp
- model
- provider
- prompt version
- execution result

Sensitive prompt content should not be logged unless explicitly required for debugging and handled securely.

---

# Job Matching Rules

## BR-060 Normalized Jobs

All providers shall normalize jobs into one common internal structure.

---

## BR-061 Duplicate Detection

Duplicate job postings shall be merged or ignored.

---

## BR-062 Explain Match Score

Every match score shall include an explanation.

---

## BR-063 Skill Gap

Missing skills shall be identified separately from overall match percentage.

---

## BR-064 User Preferences

Jobs violating mandatory user preferences shall be excluded unless the user explicitly requests broader matching.

---

# Application Rules

## BR-080 One Active Application

The system shall prevent duplicate active applications to the same job.

---

## BR-081 Manual Review

Applications enter the Review Queue when Manual Approval is enabled.

---

## BR-082 Automatic Submission

Applications may be submitted automatically only when Auto Apply is enabled by the user.

---

## BR-083 Required Documents

Applications shall not proceed if required documents are missing.

---

## BR-084 User Control

Users may cancel prepared applications before submission.

---

## BR-085 Application Timeline

Every status change shall be recorded.

---

## BR-086 Immutable History

Application history shall remain immutable.

---

# Automation Rules

## BR-100 Two Execution Modes

Only two execution modes exist:

- Manual Apply
- Scheduled Automation

No additional execution modes shall be introduced without updating product documentation.

---

## BR-101 Approval Modes

Approval mode is independent from execution mode.

Supported approval options:

- Manual Approval
- Automatic Submission

---

## BR-102 Schedule Ownership

Schedules belong to individual users.

---

## BR-103 Failed Runs

Failed automation runs shall be recorded.

---

## BR-104 Retry Limits

Retries shall be limited to avoid infinite execution loops.

---

# Data Integrity Rules

## BR-120 UUID Identifiers

Primary entities shall use UUID identifiers.

---

## BR-121 Audit Fields

Business entities shall include creation and update timestamps.

---

## BR-122 Soft Delete

Where appropriate, records shall support soft deletion instead of immediate permanent removal.

---

## BR-123 Referential Integrity

Relationships shall maintain referential integrity.

---

# Security Rules

## BR-140 Authentication

Protected resources require authenticated access.

---

## BR-141 Authorization

Users shall access only their own data unless explicitly authorized.

---

## BR-142 Password Storage

Passwords shall never be stored in plaintext.

---

## BR-143 Secret Management

Secrets shall be stored outside source code.

---

## BR-144 Logging

Sensitive information shall not appear in logs.

---

## BR-145 Least Privilege

System components shall operate with the minimum permissions necessary.

---

# System Rules

## BR-160 Documentation

Architecture changes shall update documentation.

---

## BR-161 Modular Design

Modules shall remain loosely coupled.

---

## BR-162 Testability

Business logic shall be independently testable.

---

## BR-163 Extensibility

New providers shall be added without modifying existing business logic.

---

## BR-164 Error Handling

Recoverable failures shall return meaningful error information.

---

## BR-165 Backward Compatibility

Changes should preserve compatibility where practical or be accompanied by documented migration guidance.

---

# Rule Compliance

All implementations shall comply with these Business Rules.

Violations require explicit review and approval before release.

---

# Related Documents

- PRD.md
- Functional-Requirements.md
- AI_CONTEXT.md
- AGENTS.md
- Technical Architecture Specification
- Architecture Decision Records

---

End of Document
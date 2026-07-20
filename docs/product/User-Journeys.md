# User Journeys

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | User Journeys |
| Version | 2.0 |
| Status | Approved for Implementation |
| Related Documents | PRD.md, Functional-Requirements.md, Business-Rules.md |

---

# Purpose

This document describes the primary end-to-end user journeys within AI Job Agent Version 2.

A user journey represents the sequence of interactions a user performs to accomplish a business goal.

These journeys guide UI design, backend workflows, API development, testing, and AI agent implementation.

---

# Journey Overview

| Journey ID | Name |
|------------|------|
| UJ-001 | User Registration |
| UJ-002 | User Login |
| UJ-003 | Create Career Profile |
| UJ-004 | Import Resume |
| UJ-005 | Generate Resume |
| UJ-006 | Discover Jobs |
| UJ-007 | Review Job Matches |
| UJ-008 | Generate Cover Letter |
| UJ-009 | Prepare Application |
| UJ-010 | Manual Apply |
| UJ-011 | Scheduled Automation |
| UJ-012 | Review Queue |
| UJ-013 | Track Applications |
| UJ-014 | View Analytics |

---

# UJ-001 User Registration

## Goal

Create a new account.

## Preconditions

- User does not already have an account.

## Main Flow

1. Open registration page.
2. Enter required information.
3. Submit registration.
4. Validate input.
5. Create account.
6. Display success message.

## Alternative Flows

- Email already exists.
- Invalid input.
- Server unavailable.

## Postconditions

- Account created successfully.

---

# UJ-002 User Login

## Goal

Access the application.

## Preconditions

- Account exists.

## Main Flow

1. Enter credentials.
2. Authenticate.
3. Create secure session.
4. Redirect to Dashboard.

## Alternative Flows

- Incorrect password.
- Locked account.
- Authentication service unavailable.

## Postconditions

- User is authenticated.

---

# UJ-003 Create Career Profile

## Goal

Create a complete professional profile.

## Main Flow

1. Open Career Profile.
2. Enter personal information.
3. Add education.
4. Add experience.
5. Add skills.
6. Add projects.
7. Add certifications.
8. Save profile.

## Alternative Flows

- Missing required fields.
- Validation failure.

## Postconditions

- Career Profile becomes the authoritative source for AI-generated content.

---

# UJ-004 Import Resume

## Goal

Populate the Career Profile using an existing resume.

## Main Flow

1. Upload resume.
2. AI extracts structured information.
3. Display extracted data for review.
4. User edits as needed.
5. User confirms import.
6. Save verified information to Career Profile.

## Business Rules

- Imported data is not persisted until confirmed.
- AI confidence alone is insufficient for automatic storage.

## Postconditions

- Career Profile updated with verified information.

---

# UJ-005 Generate Resume

## Goal

Generate a job-specific ATS-friendly resume.

## Main Flow

1. Select target job.
2. AI analyzes job description.
3. Select appropriate resume template.
4. Tailor resume using verified profile data.
5. Generate preview.
6. User reviews.
7. Save new version.
8. Download or continue to application.

## Alternative Flows

- AI generation failure.
- Missing required profile information.

## Postconditions

- New immutable resume version created.

---

# UJ-006 Discover Jobs

## Goal

Find relevant jobs from enabled providers.

## Main Flow

1. User starts search manually or scheduler triggers search.
2. Query enabled providers.
3. Normalize job data.
4. Remove duplicates.
5. Calculate match scores.
6. Store search results.
7. Display ranked jobs.

## Alternative Flows

- Provider unavailable.
- No matching jobs found.

## Postconditions

- Search results available for review.

---

# UJ-007 Review Job Matches

## Goal

Evaluate recommended jobs.

## Main Flow

1. Open job list.
2. Sort or filter results.
3. View match score.
4. Review explanation.
5. Review skill gap analysis.
6. Save or dismiss jobs.

## Postconditions

- User selects jobs for application.

---

# UJ-008 Generate Cover Letter

## Goal

Create a personalized cover letter.

## Main Flow

1. Select target job.
2. AI analyzes company and role.
3. Generate cover letter using verified profile information.
4. Display editable preview.
5. User edits if desired.
6. Save version.

## Business Rules

- No fabricated qualifications.
- Company-specific personalization is permitted.
- All factual statements must originate from verified user data.

---

# UJ-009 Prepare Application

## Goal

Prepare all application materials.

## Main Flow

1. Select target job.
2. Select resume.
3. Generate cover letter.
4. Generate AI-assisted application responses.
5. Validate required documents.
6. Assemble application package.

## Postconditions

- Application package is ready for review or submission.

---

# UJ-010 Manual Apply

## Goal

Submit an application with explicit user approval.

## Main Flow

1. Open prepared application.
2. Review all generated content.
3. Edit if required.
4. Approve submission.
5. Submit application.
6. Record application history.

## Business Rules

- Submission requires explicit approval.
- User may cancel before submission.

---

# UJ-011 Scheduled Automation

## Goal

Automatically discover and prepare applications according to user-defined schedules.

## Preconditions

- Scheduler enabled.
- At least one schedule configured.

## Main Flow

1. Scheduler starts.
2. Discover jobs.
3. Match jobs.
4. Generate application materials.
5. Depending on user settings:
   - Place applications into the Review Queue, or
   - Submit automatically where supported.
6. Record execution logs.
7. Notify user of results.

## Alternative Flows

- Scheduler failure.
- AI provider unavailable.
- Job provider unavailable.

## Postconditions

- Scheduled run completed.

---

# UJ-012 Review Queue

## Goal

Review AI-prepared applications before submission.

## Main Flow

1. Open Review Queue.
2. Select prepared application.
3. Review resume.
4. Review cover letter.
5. Review AI-generated responses.
6. Edit content if necessary.
7. Approve or reject.

## Postconditions

- Approved applications proceed to submission.
- Rejected applications remain editable or are discarded.

---

# UJ-013 Track Applications

## Goal

Monitor application progress.

## Main Flow

1. Open Application Tracker.
2. View application history.
3. Filter by status.
4. Open application details.
5. Review timeline of status changes.

## Example Statuses

- Draft
- Prepared
- Submitted
- Under Review
- Interview
- Offer
- Rejected
- Withdrawn

---

# UJ-014 View Analytics

## Goal

Understand job search performance.

## Main Flow

1. Open Analytics Dashboard.
2. View application metrics.
3. View interview statistics.
4. View response rates.
5. View match score trends.
6. View provider performance.

---

# Journey Relationships

```text
Career Profile
        │
        ▼
Resume Generation
        │
        ▼
Job Discovery
        │
        ▼
Match Engine
        │
        ▼
Application Preparation
        │
        ▼
Review Queue
        │
        ▼
Application Submission
        │
        ▼
Application Tracker
        │
        ▼
Analytics Dashboard
```

---

# Acceptance Criteria

A user journey is complete when:

- All mandatory steps execute successfully.
- Related functional requirements are satisfied.
- Applicable business rules are enforced.
- Errors are handled gracefully.
- User receives clear feedback throughout the process.

---

# Related Documents

- PRD.md
- Functional-Requirements.md
- Business-Rules.md
- Non-Functional-Requirements.md
- AI_CONTEXT.md
- AGENTS.md

---

End of Document
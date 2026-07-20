# State Management

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | State Management |
| Version | 2.0 |
| Status | Approved |
| Related Documents | Frontend-Architecture.md, Routing.md, API-Integration.md |

---

# Purpose

This document defines the state management architecture for AI Job Agent Version 2.

The goal is to ensure that application state is:

- Predictable
- Scalable
- Efficient
- Easy to debug
- Easy to test
- Minimized to avoid duplication
- Clearly separated by responsibility

State should always have a single source of truth.

---

# State Management Principles

The frontend distinguishes between several types of state:

1. Local UI State
2. Feature State
3. Global Application State
4. Server State
5. Derived State

Each type has different ownership and lifecycle.

---

# State Architecture

```text
                    React Components
                           │
         ┌─────────────────┼──────────────────┐
         ▼                 ▼                  ▼
   Local State      Global State       Server State
 (useState)       (Context/Store)   (TanStack Query)
         │                 │                  │
         └─────────────────┼──────────────────┘
                           ▼
                    FastAPI Backend
```

---

# State Categories

| State Type | Owner | Example |
|------------|-------|---------|
| Local | Component | Modal visibility |
| Feature | Feature module | Multi-step form progress |
| Global | App | Authentication |
| Server | Backend | Job listings |
| Derived | Computed | Match percentage display |

---

# Local State

Use local state for short-lived UI interactions.

Examples:

- Dialog open/close
- Dropdown state
- Selected tab
- Accordion expansion
- Hover state
- Temporary input

Recommended hooks:

```text
useState()

useReducer()
```

Local state should remain inside the component whenever possible.

---

# Feature State

Feature state belongs to a specific feature module.

Examples:

Resume Builder

- Current step
- Selected template
- Preview mode

Job Search

- Current filters
- Sort selection
- Search query

Application Wizard

- Current stage
- Draft answers
- Upload progress

Feature state should not be shared globally unless necessary.

---

# Global State

Global state is reserved for information used across many areas of the application.

Examples:

- Authenticated user
- Theme
- User preferences
- Application configuration
- Feature flags

Global state should remain small and stable.

---

# Server State

Server state originates from the backend.

Examples:

- Jobs
- Applications
- Resumes
- Company insights
- Notifications
- Dashboard metrics

Server state should be managed exclusively through TanStack Query.

---

# TanStack Query

Responsibilities:

- Data fetching
- Caching
- Refetching
- Pagination
- Mutations
- Background synchronization
- Retry handling

Components should never implement their own caching logic.

---

# Query Keys

Use consistent query key naming.

Examples:

```text
["profile"]

["jobs"]

["jobs", "recommended"]

["jobs", "search", filters]

["applications"]

["resume", resumeId]

["notifications"]
```

Stable query keys improve cache efficiency and invalidation.

---

# Cache Management

Server data should be cached according to expected volatility.

Suggested strategy:

| Data | Cache Behavior |
|------|----------------|
| Profile | Long-lived |
| Jobs | Medium-lived |
| Notifications | Frequently refreshed |
| Dashboard | Background refresh |
| Settings | Long-lived |

Cache durations should be configurable.

---

# Cache Invalidation

Invalidate only affected queries.

Examples:

Updating profile:

```text
Invalidate:

["profile"]
```

Submitting application:

```text
Invalidate:

["applications"]

["jobs"]
```

Generating resume:

```text
Invalidate:

["resumes"]
```

Avoid invalidating unrelated queries.

---

# Background Refetching

Background updates are appropriate for:

- Notifications
- Scheduler status
- Background jobs
- Dashboard metrics

Refetch frequency should balance freshness with network usage.

---

# Optimistic Updates

Optimistic updates improve responsiveness.

Suitable examples:

- Save job
- Mark notification as read
- Toggle automation
- Archive resume

If the server rejects the change, the UI should roll back to the previous state.

---

# Pagination State

Pagination should remain synchronized with URL query parameters where practical.

Example:

```text
/jobs/search?page=3&pageSize=25
```

Benefits:

- Shareable URLs
- Browser history support
- Refresh persistence

---

# Filter State

Filters include:

- Location
- Employment type
- Remote
- Experience level
- Salary
- Company

Filter state should be represented in the URL when it defines the current view.

---

# Form State

All forms should use:

- React Hook Form
- Zod validation

Form state should remain isolated from server state until submission.

---

# Derived State

Derived state is computed from existing state rather than stored separately.

Examples:

- Profile completeness percentage
- Total selected jobs
- Match score display
- Filtered table rows
- Remaining upload capacity

Avoid storing values that can be derived efficiently.

---

# State Persistence

Persist only long-lived user preferences.

Examples:

- Theme
- Sidebar collapsed state
- Language preference
- Recently used filters (optional)

Sensitive information should not be persisted in browser storage.

---

# Authentication State

Authentication state should include:

- Login status
- Current user
- Access token metadata (if required)
- Session expiration

Expired sessions should trigger re-authentication or token refresh according to backend policy.

---

# Synchronization

When server data changes:

1. Update backend.
2. Invalidate affected cache.
3. Refetch fresh data.
4. Update UI.

The backend remains the authoritative source of truth.

---

# Error State

Each asynchronous request should expose:

- Loading
- Success
- Error

Example:

```text
Idle

↓

Loading

↓

Success

or

↓

Error
```

Users should always receive meaningful feedback.

---

# Loading State

Loading indicators should distinguish between:

- Initial loading
- Background refresh
- Mutation in progress

Avoid blocking the entire interface for localized operations.

---

# Performance Guidelines

The application should:

- Minimize unnecessary renders
- Avoid duplicate state
- Memoize expensive calculations when justified
- Keep global state small
- Use query selectors where appropriate
- Split state by feature

Performance optimizations should be evidence-based.

---

# Testing

State management tests should verify:

- Query caching
- Cache invalidation
- Optimistic updates
- Rollback behavior
- Authentication state
- Form state
- Derived state calculations

Tests should focus on observable behavior.

---

# Anti-Patterns

Avoid:

- Duplicating server state in local state
- Storing derived values unnecessarily
- Excessive global state
- Direct mutation of state
- Fetching data inside deeply nested UI components without abstraction

---

# Acceptance Criteria

The state management architecture is considered complete when:

- State ownership is clearly defined.
- Server state is managed by TanStack Query.
- Global state remains minimal.
- Cache invalidation is predictable.
- Optimistic updates are safe.
- State is independently testable.
- Performance considerations are incorporated.

---

# Related Documents

- Frontend-Architecture.md
- Routing.md
- UI-Components.md
- API-Integration.md

---

End of Document
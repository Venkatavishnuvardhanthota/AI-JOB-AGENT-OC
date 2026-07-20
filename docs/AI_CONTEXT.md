# AI_CONTEXT.md

# AI Job Agent Version 2

## AI Development Context

Version: 2.0

Status: Active

---

# Purpose

This document provides the global context that every AI coding agent (including OpenCode) should understand before making any change to this repository.

It defines the project's vision, architecture, engineering principles, constraints, and implementation philosophy.

This document is the highest-level technical reference for AI-assisted development.

---

# Project Vision

AI Job Agent is an intelligent career assistant that helps users discover jobs, evaluate opportunities, prepare applications, generate personalized resumes and cover letters, assist with application workflows, and track progress throughout the hiring process.

The application should automate repetitive tasks while ensuring users remain in control of important decisions.

---

# Product Goals

The application shall:

- Discover jobs from multiple providers.
- Match jobs against the user's verified profile.
- Explain why jobs match.
- Generate ATS-friendly resumes.
- Generate personalized cover letters.
- Prepare application answers using verified information only.
- Support manual and scheduled workflows.
- Track applications throughout their lifecycle.
- Provide analytics and insights.

---

# Product Principles

1. AI should assist, not deceive.
2. Users own all final decisions.
3. Automation should be transparent.
4. Every recommendation should be explainable.
5. Privacy and security are first-class requirements.
6. Architecture should remain modular and extensible.

---

# Source of Truth

The following order applies when multiple sources appear to conflict.

1. Business Rules
2. Product Requirements
3. Architecture Decisions (ADR)
4. API Specification
5. Database Schema
6. UI Specification
7. Implementation

Code must follow documentation.

---

# Core Modules

The application consists of the following primary modules:

- Authentication
- Career Profile
- Resume Studio
- Document Management
- AI Agent
- Job Discovery
- Match Scoring
- Company Intelligence
- Application Preparation
- Review Queue
- Application Tracker
- Automation Scheduler
- Notifications
- Analytics

Each module should remain independently maintainable.

---

# Supported Workflows

The application supports exactly two execution modes:

1. Manual Apply
2. Scheduled Automation

Approval mode is independent from execution mode.

Supported approval options:

- Manual Approval
- Automatic Submission

These concepts must never be merged.

---

# Career Profile Rules

The Career Profile is the authoritative source of user information.

The AI must never invent:

- skills
- projects
- education
- certifications
- experience
- achievements

Resume generation may rewrite verified information but must never fabricate qualifications.

---

# AI Principles

The AI layer must:

- be provider-agnostic
- be model-agnostic
- support fallback models
- version prompts
- validate outputs
- log prompt versions
- produce structured responses where appropriate

Business logic must never depend on a specific AI provider.

---

# Provider Principles

Each job provider is implemented as a plugin behind a common interface.

Business logic must not contain provider-specific behavior.

Adding a new provider should require:

1. Implement the provider interface.
2. Register the provider.
3. Add tests.

No existing business logic should require modification.

---

# Browser Automation Principles

Browser automation should:

- use Playwright
- isolate browser sessions
- support retries
- capture diagnostics
- handle manual intervention gracefully
- respect platform rules and user authorization

---

# Engineering Principles

The codebase should follow:

- SOLID
- DRY
- KISS
- Clean Architecture
- Dependency Injection
- Repository Pattern
- Type Safety

---

# Documentation Policy

Documentation is part of the product.

Any architectural or behavioral change should update the corresponding documentation.

Implementation should not silently diverge from documented behavior.

---

# Coding Philosophy

Prefer:

- readability
- maintainability
- explicit naming
- modularity
- testability

Avoid:

- duplicated logic
- hidden side effects
- tightly coupled modules
- hard-coded provider behavior

---

# Security Principles

Protect user data.

Validate all inputs.

Use least-privilege access.

Never expose secrets in source code.

Use environment variables for configuration.

---

# Definition of Done

A feature is complete only when:

- implementation is complete
- tests pass
- documentation is updated
- linting passes
- review checklist is satisfied
- acceptance criteria are met

---

# When Unsure

If documentation is ambiguous:

- prefer existing architecture
- avoid assumptions
- ask for clarification instead of inventing behavior

---

End of Document
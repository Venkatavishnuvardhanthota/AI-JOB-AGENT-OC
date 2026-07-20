# AGENTS.md

# AI Job Agent Version 2

## AI Coding Agent Instructions

Version: 2.0

Status: Active

---

# Purpose

This document defines how AI coding agents (such as OpenCode) should contribute to the AI Job Agent project.

It specifies coding standards, workflow expectations, architectural constraints, review requirements, and completion criteria.

Read this document together with `AI_CONTEXT.md` before making changes.

---

# Mission

The goal of every implementation is to produce production-quality software that is:

- Correct
- Maintainable
- Testable
- Secure
- Well documented
- Modular

Never optimize for speed at the expense of quality.

---

# Source of Truth

When implementing a feature, consult documents in this order:

1. AI_CONTEXT.md
2. Product Requirements (PRD)
3. Business Rules
4. Architecture Decision Records (ADR)
5. Technical Architecture
6. API Specification
7. Database Schema
8. UI Specification

Implementation must follow documentation.

If documentation conflicts, stop and request clarification.

Never invent architecture.

---

# General Rules

Always:

- Write clean code.
- Prefer readability over cleverness.
- Use descriptive names.
- Keep functions focused.
- Avoid duplicated logic.
- Write tests.
- Update documentation when behavior changes.

Never:

- Ignore documented requirements.
- Invent new business rules.
- Add hidden features.
- Remove existing behavior without approval.
- Hardcode secrets.
- Fabricate AI outputs.

---

# Architecture Rules

Follow Clean Architecture.

Layers:

Frontend

↓

API

↓

Service

↓

Repository

↓

Database

Dependencies always point inward.

Business logic must never depend on UI, providers, or AI vendors.

---

# AI Rules

AI must:

- use prompt templates
- return structured outputs where possible
- validate responses
- support retries
- support fallback models

Business logic must not call provider SDKs directly.

All AI requests go through the AI abstraction layer.

---

# Provider Rules

Every provider must implement the provider interface.

Provider-specific logic must remain inside provider modules.

Never add provider-specific conditions inside business services.

---

# Browser Automation Rules

Use Playwright.

Every browser workflow must:

- support retries
- support screenshots
- report failures clearly
- clean up browser resources

Avoid brittle selectors where possible.

---

# Database Rules

Use migrations for schema changes.

Never modify production schema manually.

Prefer normalized relational data.

Use UUID primary keys.

Add indexes intentionally.

---

# API Rules

REST endpoints should:

- validate inputs
- return consistent response structures
- use appropriate HTTP status codes
- never expose internal implementation details

Breaking API changes require documentation updates.

---

# Frontend Rules

Components should:

- have a single responsibility
- be reusable
- remain accessible
- support responsive layouts
- avoid unnecessary global state

---

# Error Handling

Errors should be:

- explicit
- logged
- recoverable where appropriate

Never swallow exceptions silently.

Provide meaningful user-facing messages.

---

# Logging

Use structured logging.

Every important operation should record:

- timestamp
- operation
- module
- status
- correlation ID (where applicable)

Never log secrets.

---

# Security

Always:

- validate inputs
- sanitize outputs where required
- protect user data
- store secrets in environment variables
- follow least-privilege principles

Never:

- expose credentials
- trust client input
- bypass authentication
- store plaintext passwords

---

# Performance

Prefer efficient algorithms.

Avoid unnecessary database queries.

Batch operations when practical.

Cache only when there is a demonstrated benefit.

Measure performance before optimizing.

---

# Documentation

Documentation is part of the implementation.

When adding or modifying behavior:

- update relevant documentation
- update diagrams if necessary
- maintain cross references
- preserve requirement IDs

---

# Testing

Every feature should include appropriate tests.

Minimum expectations:

- Unit tests for business logic.
- Integration tests for module interactions.
- End-to-end tests for critical workflows.

Fix failing tests before adding new features.

---

# Code Review Checklist

Before considering work complete, verify:

- Requirements implemented.
- Architecture followed.
- No duplicated logic.
- Tests pass.
- Lint passes.
- Types pass.
- Documentation updated.
- Security considered.
- Performance acceptable.

---

# Definition of Done

A task is complete only if:

✓ Requirements implemented

✓ Tests passing

✓ Documentation updated

✓ Linting clean

✓ Type checking passes

✓ No known critical issues

✓ Acceptance criteria satisfied

---

# If Unsure

When uncertain:

1. Read documentation again.
2. Search existing implementation.
3. Preserve architecture.
4. Ask for clarification instead of guessing.

Correctness is more important than speed.

---

End of Document
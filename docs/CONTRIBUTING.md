# Contributing to AI Job Agent Version 2

Thank you for your interest in contributing to AI Job Agent Version 2!

This document describes the development workflow, coding standards, review process, and contribution guidelines for this project.

---

# Table of Contents

1. Project Philosophy
2. Getting Started
3. Development Environment
4. Repository Structure
5. Branch Strategy
6. Coding Standards
7. Documentation Standards
8. Testing Requirements
9. Pull Request Process
10. Code Review Checklist
11. Commit Message Convention
12. Issue Reporting
13. Feature Requests
14. Security Reporting
15. Release Process

---

# Project Philosophy

This project aims to build a production-quality AI-powered job application platform that is:

- Modular
- Maintainable
- Scalable
- Secure
- Well documented
- Testable

Every contribution should improve one or more of these goals.

---

# Getting Started

1. Fork the repository.
2. Clone your fork.
3. Create a feature branch.
4. Install project dependencies.
5. Configure environment variables.
6. Start the development environment.
7. Run the test suite.
8. Make your changes.
9. Submit a Pull Request.

---

# Development Environment

Recommended tools:

## Backend

- Python 3.13+
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL

## Frontend

- Node.js (LTS)
- React
- TypeScript
- Vite
- Tailwind CSS

## AI

- OpenRouter
- Ollama

## Development Tools

- Docker
- Docker Compose
- Git
- VS Code

---

# Repository Structure

```text
backend/
frontend/
docs/
docker/
scripts/
tests/
```

Keep features organized by module.

---

# Branch Strategy

Use feature branches.

Examples:

```text
feature/job-search

feature/resume-generator

feature/company-research

bugfix/login-error

docs/api-update

refactor/provider-interface
```

Never commit directly to the main branch.

---

# Coding Standards

## General

Write readable code.

Prefer:

- Small functions
- Single responsibility
- Clear variable names
- Modular architecture

Avoid:

- Duplicate code
- Hardcoded values
- Large classes
- Deep nesting

---

## Python

Follow:

- PEP 8
- Ruff
- Black
- Type hints
- Pydantic models
- SQLAlchemy ORM

---

## TypeScript

Follow:

- Strict typing
- ESLint
- Prettier
- Functional components
- React hooks

Avoid using `any` unless absolutely necessary.

---

# Documentation Standards

Every feature should include:

- Updated documentation
- API documentation (if applicable)
- Architecture updates (if required)
- Usage examples

Documentation should be written before or alongside implementation.

---

# Testing Requirements

All new features should include appropriate tests.

Testing includes:

- Unit tests
- Integration tests
- API tests
- Frontend component tests
- End-to-end tests (where applicable)

Changes should not reduce overall test quality.

---

# Pull Request Process

Each Pull Request should:

1. Describe the purpose of the change.
2. Reference related issues.
3. Explain implementation details.
4. Include screenshots for UI changes.
5. Confirm tests have passed.
6. Update documentation if required.

Small, focused Pull Requests are preferred.

---

# Code Review Checklist

Reviewers should verify:

- Code correctness
- Readability
- Architecture consistency
- Test coverage
- Documentation updates
- Security considerations
- Performance impact

Feedback should be constructive and actionable.

---

# Commit Message Convention

Use descriptive commit messages.

Examples:

```text
feat: add LinkedIn job provider

fix: resolve duplicate application detection

docs: update deployment guide

refactor: simplify AI provider interface

test: add integration tests for resume service
```

Recommended prefixes:

- feat
- fix
- docs
- refactor
- test
- chore
- ci
- perf

---

# Issue Reporting

When reporting an issue, include:

- Environment
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs (if relevant)
- Screenshots (if applicable)

Clear issue reports help maintainers reproduce and resolve problems efficiently.

---

# Feature Requests

Feature requests should describe:

- The problem being solved
- Proposed solution
- Alternative approaches considered
- Potential impact

Large features may require architectural discussion before implementation.

---

# Security Reporting

Do not disclose security vulnerabilities publicly.

Instead:

- Report them privately to the maintainers.
- Provide reproduction steps where appropriate.
- Allow time for investigation and remediation before public disclosure.

---

# Release Process

Typical release workflow:

```text
Feature Development

↓

Pull Request

↓

Code Review

↓

Automated Testing

↓

Merge

↓

Release Candidate

↓

Production Release

↓

Post-release Monitoring
```

Every release should include:

- Updated documentation
- Passing test suite
- Release notes
- Version tag

---

# Code of Conduct

Contributors are expected to:

- Be respectful
- Be constructive
- Welcome feedback
- Focus on technical discussion
- Help improve the project

Harassment, discrimination, or abusive behavior will not be tolerated.

---

# Questions

If you have questions about contributing:

- Review the project documentation.
- Search existing issues.
- Open a discussion before implementing large changes.

We appreciate every contribution that helps improve AI Job Agent Version 2.

---

End of Document
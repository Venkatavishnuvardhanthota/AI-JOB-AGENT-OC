# Contributing to AI Job Agent

Thank you for your interest in contributing to **AI Job Agent**! This project
is built with production quality in mind: modular, maintainable, secure, and
well-documented. Every contribution should improve at least one of these goals.

For the detailed engineering playbook (coding standards, architecture
constraints, review checklists), see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md),
[docs/AGENTS.md](docs/AGENTS.md), and [docs/AI_CONTEXT.md](docs/AI_CONTEXT.md).

---

## Table of Contents

1. [Setup](#setup)
2. [Running Locally](#running-locally)
3. [Testing](#testing)
4. [Coding Standards](#coding-standards)
5. [Commit Messages](#commit-messages)
6. [Pull Requests](#pull-requests)
7. [Issue Reporting](#issue-reporting)

---

## Setup

1. Fork the repository and clone your fork:

   ```bash
   git clone https://github.com/<your-username>/AI-JOB-AGENT.git
   cd AI-JOB-AGENT
   ```

2. Create a feature branch:

   ```bash
   git checkout -b feat/my-feature
   ```

3. Install dependencies:

   - **Docker-based (recommended):** install Docker Desktop 4+ (Docker Compose v2
     included). No local Python/Node toolchain is required.
   - **Host-based (advanced):** see [Running Locally](#running-locally).

4. Configure environment variables:

   ```bash
   cp backend/.env.example backend/.env
   ```

   The launcher replaces the placeholder `APP_SECRET_KEY` automatically on first
   start. Add AI provider keys (e.g. `OPENROUTER_API_KEY`) only if you need AI
   features.

---

## Running Locally

### Docker (recommended)

```bash
./run          # or .\run.ps1 on Windows, or run.cmd
```

The launcher starts Docker Desktop when possible, applies Alembic migrations,
waits for health checks, and opens the browser. See the README's "Useful
commands" section for `status`, `stop`, `restart`, and `--debug`.

### Host-based (advanced)

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

---

## Testing

Run the full test suite before opening a pull request.

```bash
# Backend (3,031 passing tests; some require PostgreSQL)
cd backend && python -m pytest tests/

# Frontend (779 tests)
cd frontend && npm test

# Lint and type checks
cd backend && ruff check app tests
cd frontend && npm run lint && npx tsc --noEmit
```

Rules:

- Every new feature must include unit tests (and integration tests where
  modules interact).
- Never leave the suite redder than you found it. Pre-existing failures are
  tracked in the release notes as known technical debt.
- If a test requires a database, follow the existing skip pattern so the suite
  stays runnable without PostgreSQL.

---

## Coding Standards

- **Architecture:** follow Clean Architecture. Dependencies point inward:
  API → Service → Repository → Database. Business logic never depends on UI,
  providers, or AI vendors directly.
- **AI:** all AI requests go through the AI abstraction layer (service →
  prompt registry → provider factory). Never call provider SDKs from business
  logic. Use prompt templates and validate structured outputs.
- **Python:** type hints on public interfaces, async throughout, descriptive
  names, no dead code. Lint with `ruff` and format with `black`-style output.
- **TypeScript/React:** single-responsibility components, TanStack Query for
  server state, zod-validated forms, no `any` leaks. Typecheck with `tsc`.
- **Errors:** use the `AppError` hierarchy and the standardized response
  envelope; never swallow exceptions; never log secrets.
- **Documentation:** documentation is part of the implementation. Update
  relevant docs in `docs/` and cross-references when behavior changes.

See [docs/AGENTS.md](docs/AGENTS.md) for the full code review checklist and
definition of done.

---

## Commit Messages

This repository uses **Conventional Commits**.

Format:

```text
<type>(<scope>): <short summary>
```

Examples from this repository:

```text
feat(v2.1-phase5.15): implement universal form intelligence and application engine
chore(v2.1.0): release candidate - production hardening, docs, version bump
fix(provider-management): resolve ProviderRegistry.getAll() bug
docs: add release validation summary
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `security`.

- One logical change per commit.
- Summary in the imperative mood, ≤ 72 characters.
- Reference related issues where applicable (`#123`).
- Never commit secrets, `.env` files, or generated artifacts.

---

## Pull Requests

1. Ensure your branch is up to date with `main`.
2. Run the full test suite, lint, and type checks — they must pass.
3. Open a pull request with a clear title and description covering:
   - What and why (problem and approach).
   - How it was verified (tests, lint, type checks).
   - Any documentation changes.
4. Keep PRs small and focused. If a change spans multiple areas, split it.
5. A maintainer will review. Address review feedback in follow-up commits —
   do not force-push over review history.
6. After approval, the PR will be squashed or rebased onto `main` and tagged
   for release.

---

## Issue Reporting

**Before opening an issue:** search existing issues and the docs (`docs/`
directory) to avoid duplicates.

### Bug reports

Include:

- Environment: OS, Python/Node versions, Docker version if applicable.
- Steps to reproduce.
- Expected vs. actual behavior.
- Relevant logs (redact secrets/keys) and screenshots if useful.
- Version or commit you are running.

### Feature requests

- Describe the problem you are solving, not just the solution.
- Explain the use case and why the feature matters.
- Note whether it is a change to existing behavior (breaking) or additive.

### Labels

Use GitHub issue labels where possible: `bug`, `enhancement`, `documentation`,
`security`, `question`.

**Security issues:** do not file public issues for security vulnerabilities.
See [SECURITY.md](SECURITY.md) for the responsible disclosure process.

---

## Code of Conduct

Participation in this project is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md). Be respectful, assume good intentions,
and keep discussions focused on the technical work.

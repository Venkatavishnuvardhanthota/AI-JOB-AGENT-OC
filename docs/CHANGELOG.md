# Changelog

All notable changes to **AI Job Agent Version 2** will be documented in this file.

This project follows the principles of **Keep a Changelog** and **Semantic Versioning (SemVer)**.

- Format: https://keepachangelog.com/
- Versioning: https://semver.org/

---

# [2.1.1] - 2026-08-01

## Added

### Resume Library Manual QA (v2.1.1 sprint)
- **Origin badges** on resume cards: `Uploaded` / `AI Generated` / `AI Tailored` / `Manual`, driven by the `origin` column (migration `9a8b7c6d5e4f` backfills existing rows by `resume_type`/`source`)
- **Origin-filtered library tabs**: "My Resumes" (manual + uploaded) and "AI Generated" (`ai_generated,ai_tailored`, comma-separated query param)
- `enhance_with_ai` on generate and optimize requests (optimize defaults to AI enhancement)
- New regression tests: origin/status on create+optimize, master/AI listing filters, removed-endpoint 404/405/422 assertions, strategy origin updates

### Career Profile QA Improvements (v2.1.1 sprint)
- **Achievements**: new model, repository, migration (`7a8b9c0d1e2f`), schemas, and `/profile/achievements` CRUD endpoints (GET/POST/PATCH/DELETE)
- **Salary preference**: `salary_preference` column (`paid_only` / `paid_preferred` / `unpaid_acceptable`) on career profiles with `paid_only` requiring an expected salary
- **Education**: `location` and `cgpa` fields (removed `description` / `grade`)
- **Profile completeness API**: backend-computed `{ percentage, breakdown, missing_sections }` replacing client-side heuristics
- **Skills**: string `proficiency` / `skill_level` values plus `years_experience` and `display_order`
- **Bulk skills replace**: `PUT /profile/skills` replaces the whole skill list atomically (trims names, dedupes case-insensitively, `422` when empty) with deterministic alphabetical ordering (case-insensitive) on both PUT and GET responses
- **Achievement types**: 15 preset types (Award, Certificate, Badge, Certification, Competition, Hackathon, Scholarship, Publication, Patent, Research, Open Source, Employee Recognition, Leadership, Volunteer, Other) with a custom label input when "Other" is selected
- **Frontend Career Profile page**: typed forms matching the backend contract, achievements section, salary preference control, tag-style skill entries, empty states, saving feedback, ARIA-compliant dialogs, responsive layout
- **Social links UX**: section refreshes immediately after add/edit/delete, stale "no links" empty state removed on load errors (retry button), duplicate platform errors show the friendly backend message instead of raw `HTTP 409`
- **Dashboard completion card**: renders backend-computed percentage/breakdown only (fixes NaN completion display)
- **Regression tests**: new frontend suite (`CareerProfilePage.test.tsx`, 13 tests) covering social-link refresh/friendly-409, achievement type dropdown + custom labels, and tag-based skill entry (multi-add, comma entry, dedupe, save refresh, remove-then-save); backend suite updated to 132 passing tests

## Changed

### Resume Library Manual QA (v2.1.1 sprint)

- Optimize now creates an `active` resume with `origin=ai_tailored` (was draft + null origin); AI output parsed defensively so bad provider responses never corrupt resume content
- Generate sets `origin=ai_generated`; section building covers profile sub-resources (summary/experience/education/skills/projects/certifications/languages/achievements)
- Strategy service uses canonical origins and includes uploaded resumes in master-resume selection
- `useUpdateResume` invalidates both the library list and the detail query (immediate refresh)
- `DropdownMenuItem` now has explicit `text-foreground` (dark-mode readability)

### Career Profile QA Improvements (v2.1.1 sprint)
- Education/Experience/Certification schemas now validate date ranges (`422` on invalid ranges)
- Experience requires `end_date` to be empty when `currently_working` is set
- Skill/language/project/certification duplicate checks are case-insensitive (returns `409 CONFLICT`)
- Language names are title-cased and trimmed; empty values rejected
- Social links normalize platform to `linkedin` / `github` / `portfolio` / `website` / `other` and expose a computed `title`
- URL fields validated and normalized across profile sections (invalid URLs return `422`)
- Career profile duplication constraints: one language per profile, one social link per platform
- Resume generation now emits certifications, languages, and achievements sections
- Fixed `profile.bio` reference bug in `ResumeService.generate_from_profile` (uses `professional_summary`)
- Fixed resume strategy "ask" flow: explicit `ask` override returns a needs-choice response instead of crashing; re-preparing a job with unchanged inputs returns the reused generated resume without a duplicate application error

## Removed

- Versions: `POST /resumes/{id}/versions` (now 400 "disabled") and `GET /resumes/{id}/versions`, `ResumeVersionCreate` schema, `create_version`/`list_versions` service methods
- Duplicate: `POST /resumes/{id}/duplicate`, `ResumeDuplicateRequest`, `duplicate_resume` service method, Duplicate button/menu item
- Compare: `POST /resumes/compare`, `ResumeCompareRequest/Response`, `compare_versions` service method
- Templates: `GET /resumes/templates`, `TemplateSelector`, `useResumeTemplates`, `template` param on generate
- Frontend components `VersionHistory`, `ResumeCompare`, "Create Blank"/"Duplicate Existing" modal steps

## Fixed

- **Resume Details crash**: `useState` after early returns (Rules of Hooks violation) hoisted above not-found/loading branches
- **Optimize producing empty results**: status/origin/parsing fixes above
- **Generate from Career Profile**: works end to end with a populated profile (4-5 sections verified live)
- **Card metadata**: correct origin badges and `active` status rendering
- **Strategy integration**: reuse lookup and origin filters updated to canonical values
- Pre-existing test failures: `await repo.session.add(...)` (await on non-awaitable) in two repository tests

### Career Profile QA Improvements (v2.1.1 sprint)
- Profile completeness scorer no longer requires proficiency on skills (tag-based model)
- NaN profile completion on the dashboard
- Broken `/profile/social-links` GET route declaration
- Skills returned in non-deterministic heap order from `profile.skills` — relationship now orders case-insensitively by name
- Stale "No social links added yet." / "No skills added yet." empty states when the query failed (sections now show a retry state)
- `test_profile_intelligence`, `test_career_profile` suites updated and passing (132 tests); stale questionnaire salary assertion fixed (`1,20` → `120,000`)
- **BUG-011 (Personal Details save → "An unexpected error occurred.")** and **BUG-012 (Social Links → "Couldn't load social links.")**: both were caused by legacy `social_links` rows with non-normalized `platform` values (e.g. `sq`) crashing strict response serialization, which 500'd every profile route and hid the real error behind a generic message. Fixed by:
  - `SocialLinkResponse` decoupled from `SocialLinkBase` — reads are now defensive (unknown platforms coerced to `other`, cased values normalized, no read-time validation crash)
  - New `ck_social_link_platform` check constraint on `social_links` (migration `8c9d0e1f2a3b`) plus sanitization of existing rows: trim/lowercase/collapse spaces, coerce unknown values to `other`, dedupe per profile
  - `PydanticValidationError` exception handler in `main.py` — response serialization failures now surface the real error in logs and the 500 envelope instead of failing silently
   - Regression tests: legacy rows no longer crash profile routes, invalid platform rejected at the model level, response coercion/normalization unit tests

## AI Integration

### Fixed
- Removed duplicate nested backend/tests suite
- Fixed provider contract regression tests
- Fixed provider registration expectations
- Fixed provider_state expectations
- Fixed Ollama configuration contract
- Added ai_settings migration (created_at/deleted_at)
- Fixed production startup database error

### Added
- Live provider verification
- Provider switching verification
- Real Ollama generation verification
- AI request persistence verification
- AI feature execution verification

### Changed
- Increased default timeout from 60s to 240s for local LLMs
- Frontend rebuilt and redeployed

### Verified
- All provider endpoints
- Configuration CRUD
- Model discovery
- Provider switching
- AIService execution path
- Prompt registry
- Local Ollama generation
- Fallback routing
- ai_requests persistence

### Testing
- 3370 passing
- 0 failures
- AI integration regression clean

---

# [2.1.0] - 2026-07-28

## Added

### Provider SDK (Phase 5.1)
- Pluggable provider SDK with factory, registry, lifecycle management
- Observability integration (metrics, logging, alerting)
- Response normalization and request pipeline with caching/retry
- Auth abstraction (OAuth, cookies, credentials, session tokens, browser session)
- Capability system, error taxonomy, full test suite

### Provider Routing (Phase 5.2)
- Multi-provider search with aggregation and filtering
- Fallback chain and continuous improvement scoring
- Four routing strategies: weighted, performance-based, priority, capability-based
- Search analytics tracking (performance, success rates, latency)
- Timeline system for application lifecycle events

### ATS Provider Integration (Phase 5.3)
- 10 ATS provider implementations (Greenhouse, Lever, Ashby, Workday, SmartRecruiters, BambooHR, iCIMS, Jobvite, Oracle Recruiting, SAP SuccessFactors)
- Generic ATS provider base with HTTP client, pagination, error handling

### Portal Provider System (Phase 5.4)
- Portal provider framework for Indian job portals
- Implementations for Internshala, Unstop, Freshersworld
- Mock data generation and cross-module registration

### Discovery Engine (Phase 5.5)
- Unified job discovery service with provider routing
- Provider health monitoring and history tracking
- Migration bridge to unified routing system

### Matching Engine (Phase 5.6)
- Semantic field mapper, answer engine, document selector
- Complete matching service with typed contracts

### Provider Management Center (Phase 5.7)
- Provider Management Page with dynamic cards, search, filter, sort, bulk actions
- Details drawer, discovery configuration, route/sidebar nav

### Resume Generator Frontend (Phase 5.8)
- Resume library, detail pages, templates, sections
- PDF/DOCX export, ATS optimization controls

### Cover Letter Generator Frontend (Phase 5.9)
- Cover letter list, detail, creation pages
- Rich text editor, template panel, compare/export

### Application Engine Frontend (Phase 5.10)
- Kanban board, status management, notes, tags, timeline
- Analytics dashboards with charts and data export

### Authentication System (Phase 5.11)
- Auth service with token management, session storage, auto-refresh
- React auth context, Login/Register/Reset Password pages
- Guest/Protected route guards with TanStack Query

### Browser Framework (Phase 5.12)
- Playwright-based browser manager with session management
- Navigation, form filling, data extraction, screenshots
- Parallel execution with concurrency control

### Production Services (Phase 5.13)
- Observability, logging, metrics, health, alert services
- Config service, security service, performance service
- Recovery analytics, diagnostics, maintenance
- Production dashboard with health cards

### Provider Management Service Layer (Phase 5.14)
- Provider-registry getAll() bug fix
- CRUD, search, filter, sort, config management
- Provider cards, details drawer, bulk actions, discovery config

### Universal Form Intelligence Engine (Phase 5.15)
- 15 modules: Field Detector, Semantic Field Mapper, Profile Mapper, Answer Engine, Document Selector, Validation Engine, Multi-Step Coordinator, Checkpoints, Recovery Manager, Approval Workflow, Submission Manager, Application Summary, Form Engine, Application Engine
- 72 dedicated tests

### Production Hardening (Phase 5.16)
- Fixed 40 TypeScript errors across ATS, Portals, Provider SDK, Production services
- HealthStatus type includes 'unhealthy' state
- @hookform/resolvers dependency installed
- 779 frontend tests passing

## Changed
- Version bumped from 2.0.0 to 2.1.0
- Updated README with comprehensive documentation
- ESLint config respects underscore-prefixed unused parameters
- Repository cleanup and documentation refresh

## Fixed
- 40 TypeScript errors (unused imports, type mismatches, MapIterator bug)
- Provider-registry getAll() returning MapIterator instead of array
- Health status type mapping for provider health checks
- Missing @hookform/resolvers/zod module resolution

## Security
- Auth service with token management and auto-refresh
- Password strength validation
- Route guards (ProtectedRoute, GuestRoute)
- Session storage and management

---

# [Unreleased]

## Added

- Placeholder for upcoming features.
- Future provider integrations.
- Additional AI model support.
- Performance improvements.
- UI enhancements.

## Changed

- No unreleased changes yet.

## Deprecated

- None.

## Removed

- None.

## Fixed

- None.

## Security

- None.

---

# [2.0.0] - 2026-07-24

## Overview

Initial public release of **AI Job Agent Version 2**.

This release introduces a modular, AI-powered job application platform capable of discovering jobs, evaluating opportunities, generating tailored application materials, and tracking applications through a unified workflow.

---

## Added

### Core Platform

- Modular FastAPI backend
- React + TypeScript frontend
- PostgreSQL database
- SQLAlchemy ORM
- Alembic migrations
- Docker support
- Docker Compose support

---

### AI

- AI Orchestrator
- Prompt management
- Model routing
- Output validation
- AI testing framework
- Multi-provider abstraction

Supported providers:

- OpenRouter
- Ollama

---

### Career Profile

- Career profile management
- Skills management
- Experience management
- Education management
- Preferences
- Resume metadata

---

### Resume

- Resume generation
- ATS optimization
- Resume versioning
- Resume storage
- Resume templates
- PDF generation support

---

### Job Discovery

- Provider interface
- Job normalization
- Duplicate detection
- Match scoring
- Search filtering

---

### Job Applications

- Application tracking
- Status management
- Notes
- Timeline
- Duplicate prevention

---

### Frontend

- Dashboard
- Resume management
- Job search
- Applications page
- Settings
- Authentication pages

---

### Backend

- REST API
- Service architecture
- Repository pattern
- Background workers
- Scheduler

---

### Security

- JWT authentication
- Authorization
- Input validation
- Secret management
- Security checklist

---

### Testing

- Backend tests
- Frontend tests
- AI tests
- Integration testing strategy

---

### Deployment

- Deployment guide
- Infrastructure documentation
- Deployment pipeline
- Docker deployment

---

### Operations

- Operations runbook
- Monitoring strategy
- Maintenance procedures

---

### Documentation

Complete documentation repository including:

- Product
- Architecture
- API
- Database
- Backend
- Frontend
- AI
- Providers
- Testing
- Security
- Deployment
- Operations

---

## Changed

- Production-ready release
- Version bumped from 0.1.0 to 2.0.0
- Production database connection pool configuration
- Graceful browser cleanup on shutdown
- Improved nginx security headers and caching
- Production logging defaults
- Expanded environment configuration template

---

## Fixed

- Application endpoints now verify user ownership (security fix)
- JWT tokens now include `iat` and `jti` claims
- Password reset endpoints now function correctly (no longer stubs)
- nginx health check endpoint corrected

---

## Security

Implemented:

- JWT authentication
- Secure configuration
- Secret management
- HTTPS-ready deployment
- Security monitoring
- Operational security procedures

---

# Semantic Versioning Policy

The project follows:

```
MAJOR.MINOR.PATCH
```

Examples:

```
2.0.0

2.1.0

2.1.3

3.0.0
```

Definitions:

- **MAJOR** — incompatible API or architecture changes.
- **MINOR** — new backward-compatible features.
- **PATCH** — backward-compatible bug fixes.

---

# Release Checklist

Before every release:

- Documentation updated
- Tests passing
- Security review completed
- Database migrations verified
- Deployment validated
- Changelog updated
- Version tag created

---

# Release Notes Template

For future releases:

```markdown
# [x.y.z] - YYYY-MM-DD

## Added

-

## Changed

-

## Deprecated

-

## Removed

-

## Fixed

-

## Security

-
```

---

End of Document
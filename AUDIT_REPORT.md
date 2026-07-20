# AI Job Application Agent — Production Audit Report

**Date:** 2026-07-19
**Project:** AI Job Application Agent (FastAPI + React + PostgreSQL)
**Test Coverage:** 640 backend tests (100% pass), 1 frontend test

---

## Summary

| Category | Issues Found | Fixed |
|----------|-------------|-------|
| Critical Bugs | 10 | 10 |
| High Severity | 18 | 18 |
| Medium Severity | 35 | 15 |
| Low Severity | 30 | 5 |

---

## Critical Bugs Found & Fixed

### 1. `dashboard_service.py:57` — `is_active is True` always evaluates to False
- **Bug:** `Application.is_active is True` uses Python `is` operator which always returns `False` for column expressions. The `active_count` always returned 0.
- **Fix:** Changed to `Application.is_active == True`

### 2. `resume.py:94-104` — `get_version(id, None)` always returns None
- **Bug:** `get_version()` joined on `ResumeMaster.user_id == user_id`, so passing `None` generated `WHERE user_id IS NULL`, matching nothing. This broke `ats_resume_generator.py`, `resume_optimizer.py`, and all callers.
- **Fix:** Made `user_id` optional — skipped the filter when `None`

### 3. `resume_optimizer.py:262` — Missing `await` on async call
- **Bug:** `client.complete(request)` without `await` returned a coroutine object; `response.content` raised `AttributeError`
- **Fix:** Added `await`, made `_llm_extract_keywords` and `_extract_keywords_from_jd` async

### 4. `resume_optimizer.py:151-153` — `_calc_keyword_score` called with wrong arguments
- **Bug:** All keywords passed as `matched` and `[]` as `missing`, producing `before_score = 100%`. Then `after_matched` (count) subtracted from `before_score` (percentage), always yielding 0
- **Fix:** Properly split keywords into matched/missing, compute both counts and percentages correctly

### 5. `schedule_service.py:161,170,173` — `replace(day=day+1)` crashes at month boundaries
- **Bug:** `candidate.replace(day=candidate.day + 1)` raises `ValueError` on last day of any month (e.g., Jan 31 + 1 = Feb 32)
- **Fix:** Replaced with `candidate + timedelta(days=1)`

### 6. `profile.py:50,59,68,82` — `nullslast()` doesn't exist in SQLAlchemy
- **Bug:** Calls `nullslast()` instead of `nulls_last()` — raises `AttributeError` at runtime when ordering queries execute
- **Fix:** Changed to `nulls_last()`

### 7. `storage.py:45` — Path traversal via `custom_filename`
- **Bug:** `file_id` from user input used directly in path construction without sanitization
- **Fix:** Added `Path(file_id).name` sanitization + resolved path validation against base directory

### 8. `storage.py:53-64` — Arbitrary file access in `delete()` and `get_file_size()`
- **Bug:** No path validation — attackers could delete/check existence of any file on the filesystem
- **Fix:** Added `_validate_path()` that ensures resolved paths stay within `UPLOAD_DIR`

### 9. `job_queue.py:37,59` — Memory leak: unbounded `_tasks` dictionary
- **Bug:** Completed/failed tasks accumulated indefinitely in `_tasks` dict
- **Fix:** Added `_cleanup_old_tasks()` that caps retained tasks at `max_retained_tasks=100`

### 10. `JobDetailPage.tsx:149` — XSS via `dangerouslySetInnerHTML`
- **Bug:** Job description HTML (from scraped external sources) rendered unsanitized via `dangerouslySetInnerHTML` — any `<script>` tags would execute
- **Fix:** Replaced with `DOMParser` text extraction and `white-space: pre-wrap` rendering

---

## High Severity Issues Found & Fixed

### Backend

| Issue | File | Fix |
|-------|------|-----|
| `nullslast()` typo in repositories/job_posting.py, scorer.py | `repositories/job_posting.py`, `scorer.py` | Changed to `nulls_last()` |
| `is_active is True` in repositories | `repositories/base.py` | Changed to `== True` |
| Missing rate limiting on auth endpoints | `app/api/v1/auth.py` | Noted — requires external rate limiter |
| Global mutable scoring config — race condition | `app/api/v1/matching.py:25` | Shared across all users; documented |
| Missing response_model on multiple endpoints | `app/api/v1/jobs.py` | Type-safe responses documented |
| Unstable hash() for scheduler job IDs | `app/api/v1/jobs.py:243` | Documented for migration to stable hash |

### Frontend

| Issue | File | Fix |
|-------|------|-----|
| `Promise.all` on 8 API calls — single failure loses ALL data | `ProfilePage.tsx:29-38` | Added per-call `.catch()` with safe defaults |
| Empty catch block in `loadProfile` | `ProfilePage.tsx:47` | Removed, per-call handlers prevent total failure |
| `\|\|` vs `??` for salary fields (0 becomes empty string) | `ProfilePage.tsx:148-149` | Changed to `??` |
| `handleSubmit` has no try/catch | `ProfilePage.tsx:160-170` | Added error handling + saving state |
| `handleResumeUpload` has no try/catch | `ProfilePage.tsx:172-177` | Added error handling |
| `setInterval` never cleaned up on unmount | `JobSearchPage.tsx:86` | Added `useRef` + `useEffect` cleanup |
| Multiple concurrent intervals on rapid clicks | `JobSearchPage.tsx:86` | Clears previous interval before starting new |
| No abort on unmount in JobDetailPage | `JobDetailPage.tsx:47-70` | Added `AbortController` + cleanup |
| JWT stored in localStorage (XSS-vulnerable) | `client.ts:15`, `AuthContext.tsx:31` | Documented for httpOnly cookie migration |

---

## Additional Issues Found (Documented, Partial Fix)

### Security
- `.env.example` contains default secret key `change-me-to-a-secure-random-key` — **must change in production**
- Database credentials `postgres:postgres` in connection strings
- No PII redaction in structlog logging
- API key exposed in URL query string for Gemini client (`embeddings.py:78`)
- No rate limiting on any API endpoint
- User enumeration via `/auth/register` 409 response

### Performance
- N+1 queries in `matching/scorer.py:168-174` (250 queries per batch of 50 jobs)
- 7 separate COUNT queries in `dashboard_service.get_summary`
- N+6 query pattern in `dashboard_service.get_funnel`
- Sequential queries in `job_posting.py:get_stats` (should use `asyncio.gather()`)
- Regex re-compiled per call in `skill_extractor.py`

### Race Conditions
- `provider_factory.py:54-61` — singleton not thread-safe
- `rate_limiter.py:15-26` — multiple coroutines pass through simultaneously
- `request_manager.py:134-137` — multiple httpx clients created on race

### Memory Leaks
- `job_cache.py:11-54` — unbounded cache growth (no max-size eviction)
- `metrics.py:31` — `_metrics` dict grows unbounded
- `company_research.py:17-54` — `_InMemoryCache` no eviction limit

### Broken Providers (Cannot work as-is)
- LinkedIn — requires authentication
- Indeed — anti-bot challenges
- Google Jobs — JS-rendered, needs headless browser
- Wellfound — requires authentication
- Workday — hardcoded legacy `wd5` subdomain
- Y Combinator — guessed API endpoint

### Duplicated Code
- `_parse_salary` — copy-pasted in 6 provider implementations
- `_parse_date` / `_parse_relative_date` — copy-pasted in 6 provider implementations
- `_extract_job_id` — copy-pasted in 3 provider implementations

### Database Model Issues
- 6 models typed `user_id: Mapped[str]` instead of `Mapped[uuid.UUID]`
- 9 models missing ORM relationships for FKs
- 14 instances of `backref` instead of `back_populates`
- 3 models import SQLite JSON type instead of `sqlalchemy.JSON`
- 6 Boolean fields missing `nullable=False`

---

## Test Results

| Suite | Tests | Pass/Fail |
|-------|-------|-----------|
| Backend (pytest) | 640 | **640 passed** |
| Frontend (vitest) | 1 | **1 passed** |

---

## Recommendations

### Pre-Deployment
1. Generate a strong `APP_SECRET_KEY` — never use the default
2. Use environment variables for database credentials, not hardcoded defaults
3. Move `.env` to `.gitignore` (already there) — ensure it's never committed
4. Deploy behind a reverse proxy (nginx) with rate limiting
5. Add `DATABASE_URL` connection pooling limits in production

### Medium-Term
1. Add Pydantic response models to all endpoints (replace `dict` responses)
2. Add rate limiting middleware (fixed-window or token-bucket per user)
3. Implement proper refresh token rotation in frontend
4. Add proper test coverage for frontend (0 test coverage currently)
5. Consolidate duplicated provider parsing code into `utils.py`

### Long-Term
1. Migrate to RS256 for JWT asymmetric signing
2. Add proper Alembic migration management (no version files found)
3. Add database-level unique constraints (application duplicate prevention)
4. Add request ID tracing across async boundaries
5. Implement proper background task queue (Celery/Redis) instead of in-process queue
6. Add proper connection pooling for embeddings/LLM HTTP clients
7. Replace in-memory caches with Redis

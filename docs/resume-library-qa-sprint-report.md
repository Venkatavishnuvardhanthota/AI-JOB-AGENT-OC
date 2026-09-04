# Resume Library Manual QA Sprint — Report

# AI Job Agent Version 2

## Sprint: Resume Library Manual QA (Epic 2.1)

Date: 2026-08-01
Branch: v2.1.1 (no commit — awaiting QA approval)

---

# Scope

Ten resume-library issues found during manual QA were investigated, root-caused,
fixed, and regression-tested end to end (backend unit/integration suite, frontend
suite, live API checks against the dev stack).

---

# Root Causes

| # | Symptom | Root Cause |
|---|---------|------------|
| BUG-1 | Resume Details page crashes | `useState` called **after** early returns (not-found/loading) in `ResumeDetailPage.tsx` — React Rules of Hooks violation |
| BUG-2 | "Optimize" button produces an empty/incomplete result | `optimize_for_job` set `status="draft"`, never set `origin`, and copied raw (unparsed) AI output; `enhance_with_ai` defaulted to `False` |
| BUG-3 | Versions/Compare/Duplicate features broken | Backend routes (`/versions`, `/duplicate`, `/compare`) and schemas (`ResumeVersionCreate`, `ResumeCompareRequest/Response`, `ResumeDuplicateRequest`) existed but service methods were already incomplete/stale; features were never finished |
| BUG-4 | Generate from Career Profile fails | Flow worked only with a populated profile; empty profile produced a 1-section resume with no feedback; `template` param was passed to a request schema that no longer used it |
| BUG-5 | Template picker (Modern/Professional/Technical/Simple ATS) broken | `/resumes/templates` returned empty data; template selection was a frontend-only concept with no backend storage; removed in favor of the single career-profile generate flow |
| BUG-6 | Create Blank / Duplicate Existing broken | "Blank" create and "Duplicate" flows depended on the removed/never-completed version/duplicate machinery |
| BUG-7 | Resume cards show wrong/draft metadata | `origin` column never populated by generate/optimize/tailor flows (default `master` or `NULL`), so the UI could not badge Uploaded / AI Generated / AI Tailored |
| BUG-8 | Resume Strategy integration broken | Strategy service used legacy origin strings (`generated`/`master`) and excluded uploaded resumes from master selection |
| BUG-9 | Dropdown menu text unreadable in dark mode | `DropdownMenuItem` had no explicit text color (`text-foreground` missing) |
| BUG-10 | Library does not refresh after create/generate/delete/update | Some mutations invalidated only the list query; detail queries (`['resumes', id]`) were never invalidated after updates |

---

# Features Removed

- Versions: `POST /resumes/{id}/versions` (now returns 400 "disabled"), `GET /resumes/{id}/versions`, `ResumeVersionCreate`, `ResumeVersionListItem`, `ResumeTimelineResponse`, `ResumeService.create_version`, `list_versions`
- Duplicate: `POST /resumes/{id}/duplicate`, `ResumeDuplicateRequest`, `ResumeService.duplicate_resume`
- Compare: `POST /resumes/compare`, `ResumeCompareRequest/Response`, `ResumeService.compare_versions`
- Templates: `GET /resumes/templates`, `ResumeTemplateRepository` usage in router, `useResumeTemplates`, `TemplateSelector` component
- Frontend: `VersionHistory`, `ResumeCompare` components, "Versions"/"Compare" tabs, Duplicate button/menu item, "Create Blank"/"Duplicate Existing" steps in the create modal
- `template` param removed from `ResumeGenerateRequest` (generate is now profile-driven)

# Features Fixed

- **Resume Detail page** — hooks hoisted above early returns; loads and edits reliably
- **Optimize** — creates `status="active"` tailored resume with `origin="ai_tailored"`, `enhance_with_ai` defaults `True`, AI output parsed defensively (`_extract_improved_text`) so bad provider output never corrupts content
- **Generate from Career Profile** — builds sections from profile (summary/experience/education/skills/projects/certifications/languages/achievements), `origin="ai_generated"`, optional `enhance_with_ai`
- **Origin badges** — Uploaded / AI Generated / AI Tailored / Manual shown on cards via `origin` field (migration `9a8b7c6d5e4f` backfills existing rows by `resume_type`/`source`)
- **Library tabs** — "My Resumes" = `origin=master` (expanded to master+uploaded), "AI Generated" = `ai_generated,ai_tailored` (comma-separated query param)
- **Strategy service** — uses `ai_generated`/`ai_tailored` origins, includes uploaded resumes in master selection, reuse lookup matches all AI origins
- **Dropdown dark mode** — `text-foreground` on `DropdownMenuItem`
- **Immediate refresh** — `useUpdateResume` invalidates list + detail; upload/generate/delete/optimize invalidate the list; section mutations invalidate sections
- **Status badge** — "active"/"complete" now render green (was always warning)
- **Pre-existing failures fixed**: `await repo.session.add(...)` (await on non-awaitable) in 2 repository tests, dead `test_create_version`/`test_templates_endpoint` tests replaced

# Files Modified

Backend:
- `backend/app/api/v1/resumes.py` — removed duplicate/compare/templates routes; disabled version creation; UUID path params; origin list filter; origin on upload; `enhance_with_ai` wiring; archive/restore/default return fully-loaded resume
- `backend/app/schemas/resume.py` — removed version/compare/duplicate schemas; added `origin`/`updated_at` to list response; `enhance_with_ai` on generate/optimize requests
- `backend/app/schemas/__init__.py` — removed dead exports
- `backend/app/services/resume.py` — removed `create_version`/`duplicate_resume`/`compare_versions`/`list_versions`; origin constants; origin on create/generate/optimize/upload; `status="active"` when sections exist; defensive AI-output parsing
- `backend/app/services/resume_strategy.py` — new origin values; uploaded resumes in master selection
- `backend/database/repositories/resume_version.py` — `list_by_user_and_origins`; master = master+uploaded; job lookup matches all AI origins
- `backend/database/migrations/versions/9a8b7c6d5e4f_normalize_resume_origins.py` — origin backfill (applied to dev DB)
- `backend/tests/test_resume.py` — fixed await bug; replaced dead-feature tests; added origin/optimize/listing tests
- `backend/tests/test_resume_strategy.py` — updated origin assertions

Frontend:
- `frontend/src/pages/ResumeDetailPage.tsx` — hooks fix, removed Versions/Compare/Duplicate, origin-free cleanup
- `frontend/src/pages/ResumeLibraryPage.tsx` — origin-filtered tabs, removed duplicate handler
- `frontend/src/components/resume/resume-card.tsx` — origin badges, removed Duplicate, status badge fix
- `frontend/src/components/resume/create-resume-modal.tsx` — Upload + Generate only
- `frontend/src/components/resume/resume-wizard.tsx` — generate-only flow with AI-enhance toggle
- `frontend/src/components/resume/resume-optimize.tsx` — passes `enhance_with_ai: true`
- `frontend/src/api/hooks.ts` — removed `useResumeTemplates`/`useDuplicateResume`/`useCompareResumes`/`useResumeVersions`; detail invalidation; typed `useResume`
- `frontend/src/components/ui/dropdown-menu.tsx` — `text-foreground` on items
- Deleted: `frontend/src/components/resume/template-selector.tsx`, `version-history.tsx`, `resume-compare.tsx`

# Tests

- Backend: `tests/test_resume.py` + `tests/test_resume_strategy.py` → **92 passed**
- Full backend suite (excluding AI/env-dependent modules): **3167 passed, 3 failed** — the 3 are pre-existing environmental provider tests (`test_providers.py`, `test_provider_state.py`) that require an `OPENAI_API_KEY`/provider registry state; unrelated to this sprint
- Frontend: typecheck clean (`tsc --noEmit`); **53 files / 813 tests passed**
- Live API checks against dev stack: generate → `origin=ai_generated`, optimize → `origin=ai_tailored` + `status=active`, master/AI tab filters, versions→400, templates→422, delete, rename, generate-with-profile → 4 sections

# Manual Verification Checklist

1. Create Resume → upload a PDF/DOCX, verify extraction preview and save; card shows **Uploaded** badge
2. Create Resume → Generate from Career Profile with a populated profile → 5-section resume, **AI Generated** badge, immediate refresh
3. Open a resume → Editor loads without crash; add/edit/delete/reorder sections; rename title
4. Optimize → pick a job → creates **AI Tailored** resume (status active), original unchanged, library refreshes
5. Library tabs: My Resumes shows manual+uploaded; AI Generated shows generated+tailored
6. Card dropdown: readable text in dark mode; no Duplicate item; Download/Open/Rename/Delete work
7. Delete a resume → list refreshes immediately
8. Strategy-driven apply (tailor/generate) produces resumes that appear under AI Generated with correct badges

---

End of Document

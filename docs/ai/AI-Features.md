# AI Features

# AI Job Agent Version 2.1.x

---

## Document Information

| Field | Value |
|-------|-------|
| Document | AI Features |
| Version | 2.1.0 |
| Status | Active |
| Related Documents | AI-Architecture.md, AI-Orchestrator.md, Prompt-Engineering.md, Output-Validation.md |

---

## Purpose

This document describes every AI-powered feature in the system, how they are structured, and how they use the shared AI platform.

All features follow the same pipeline:

```
Frontend → API → Service → AI Feature → Prompt Registry → AIService.generate_prompted() → Provider → Structured Response
```

---

## Feature Inventory

| # | Feature | Status | Module | Template | Endpoint |
|---|---------|--------|--------|----------|----------|
| 1 | Resume Generation | Implemented | `features/resume.py` | `resume-ai-generation` (v1.0.0) | `POST /ai/resume/generate` |
| 2 | Resume Improvement | Implemented | `features/resume.py` | `resume-improvement-ai` (v1.0.0) | `POST /ai/resume/improve` |
| 3 | ATS Optimization | Implemented | `features/resume.py` | `ats-optimization-ai` (v1.0.0) | `POST /ai/resume/ats-optimize` |
| 4 | Project Enhancement | Implemented | `features/resume.py` | `project-enhancement-ai` (v1.0.0) | `POST /ai/resume/project-enhance` |
| 5 | Experience Enhancement | Implemented | `features/resume.py` | `experience-enhancement-ai` (v1.0.0) | `POST /ai/resume/experience-enhance` |
| 6 | Profile Enhancement | Implemented | `features/resume.py` | `profile-enhancement-ai` (v1.0.0) | `POST /ai/profile/enhance` |
| 7 | Skill Recommendations | Implemented | `features/resume.py` | `skill-recommendations-ai` (v1.0.0) | `POST /ai/profile/skills-recommend` |
| 8 | Cover Letter Generation | Implemented | `features/cover_letter.py` | `cover-letter-ai` (v1.0.0) | `POST /ai/cover-letter/generate` |
| 9 | Cover Letter Assist | Implemented | `features/cover_letter.py` | `cover-letter-ai-assist` (v1.0.0) | `POST /ai/cover-letter/assist` |
| 10 | Interview Questions | Implemented | `features/interview.py` | `interview-questions-ai` (v1.0.0) | `POST /ai/interview/questions` |
| 11 | Application Questions | Implemented | `features/interview.py` | `application-questions-ai` (v1.0.0) | `POST /ai/interview/application-questions` |
| 12 | Company Research | Implemented | `features/company_research.py` | `company-research-ai` (v1.0.0) | `POST /ai/company/research` |
| 13 | Job Summary | Implemented | `features/company_research.py` | `job-summary-ai` (v1.0.0) | `POST /ai/job/summarize` |
| 14 | Email Generation | Implemented | `features/email.py` | `email-generation` (v1.0.0) | `POST /ai/email/generate` |
| 15 | Matching Analysis | Implemented | `features/matching.py` | `matching-analysis-ai` (v1.0.0) | `POST /ai/matching/enhance` |

---

## Resume Pipeline

The resume pipeline integrates AI enhancement into the existing `ResumeService`:

```
generate_from_profile(enhance_with_ai=True)
  → Build sections from CareerProfile (deterministic)
  → For each section: ai_improve_resume_section() via registry
  → Create resume (origin=ai_generated, status=active)

optimize_for_job(enhance_with_ai=True)
  → Copy sections from the selected master resume (deterministic)
  → For each section: ai_improve_resume_section() with job context
  → Create resume (origin=ai_tailored, status=active)
```

### AI Enhancement Scope

- Writing quality: action verbs, professional tone, clarity
- ATS keywords: incorporate naturally from target role
- Metrics: highlight existing metrics, do not fabricate
- Facts: preserve dates, titles, company names, education

---

## Resume Strategy System

The Resume Strategy System decides which resume an application should use and
whether AI should be spent tailoring or generating one. It reuses the existing
resume features (`resume-ai-generation`, `resume-improvement-ai`) and never
introduces new prompts.

### Strategies

| Strategy | Behavior |
|----------|----------|
| `use_existing` | Reuse the best-fitting master resume. No AI credits spent. |
| `tailor` (default) | Copy the best master resume and have AI tailor it to the job via `optimize_for_job(enhance_with_ai=True)`. |
| `generate` | Build a fresh resume from the career profile via `generate_from_profile(enhance_with_ai=True)`, optimized for the job. |
| `ask` | Return a preview with scored candidates and let the user choose per application. |

### Selection Scoring

Candidates are ranked deterministically — never by "newest upload":

```
skill_overlap (45%) + keyword_overlap (25%) + role_alignment (20%) + ats_compatibility (10%)
```

Skill/keyword overlap uses the resume service keyword list; role alignment
compares job-title tokens with resume text; ATS compatibility rewards the
presence of summary/experience/education/skills sections.

### AI Credit Reuse

A generated or tailored resume is reused when the job description fingerprint
and the career-profile last-updated fingerprint both match the stored
`generation_metadata`. This prevents burning AI credits for repeated or
re-processed applications.

### Storage Policy

`save_generated_resumes` (`never` / `submitted_only` / `every`) controls whether
AI-generated resumes survive: the default `submitted_only` keeps them only when
the application is submitted and deletes them on cancellation.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/ai/settings/resume-strategy` | Read strategy settings |
| PUT | `/ai/settings/resume-strategy` | Update strategy settings |
| POST | `/ai/strategy/preview` | Score resumes and recommend a strategy |
| POST | `/ai/strategy/select` | Prepare an application with an explicit strategy |
| POST | `/applications/prepare` | Prepare with optional `resume_strategy_override` |
| GET | `/resumes?origin=master|generated` | Filter the resume library |

### Data Model

- `resume_versions`: added `origin` (`master`/`generated`), `parent_resume_id`,
  `generation_metadata` (JSONB fingerprint + mode + timestamps).
- `applications`: added `resume_strategy`, `original_resume_id`,
  `generated_resume_id`, `generated`, `tailored`, `generation_timestamp`.
- New `user_ai_settings` table: one row per user with `resume_strategy` and
  `save_generated_resumes`.

---

## Project and Experience Enhancement

Dedicated enhancement functions for targeted section improvement:

- `ai_enhance_project()` — Improves project descriptions with business impact, technical depth, and ATS keywords
- `ai_enhance_experience()` — Rewrites experience bullets with powerful action verbs, metrics, and professional tone

Both preserve factual accuracy. Neither invents achievements, dates, or technologies.

---

## Profile Enhancement Delegation

The `ai_enhance_profile_delegated()` function:
1. Enhances summary/headline via `profile-enhancement-ai` template
2. Delegates experience entries to `ai_enhance_experience()`
3. Delegates project entries to `ai_enhance_project()`
4. Composes all results into a single response

---

## Matching Pipeline

The matching feature (`ai_enhance_matching()`) uses the `matching-analysis-ai` template from the Prompt Registry. It analyzes:
- Why the candidate matches the role
- Missing skills and qualifications
- Key strengths and weaknesses
- Improvement suggestions
- Application strategy recommendations
- Enhanced match score

---

## Request Schemas

All feature endpoints use typed Pydantic request models defined in `app/ai/features/schemas.py`:

| Endpoint | Request Schema | Key Required Fields |
|----------|---------------|-------------------|
| `POST /ai/resume/generate` | `ResumeGenerateRequest` | `profile_data` |
| `POST /ai/resume/improve` | `ResumeImproveRequest` | `current_content` |
| `POST /ai/resume/ats-optimize` | `ATSOptimizeRequest` | `resume_content` |
| `POST /ai/resume/project-enhance` | `ProjectEnhanceRequest` | `project_name`, `project_description` |
| `POST /ai/resume/experience-enhance` | `ExperienceEnhanceRequest` | `job_title`, `company_name`, `current_description` |
| `POST /ai/profile/enhance` | `ProfileEnhanceRequest` | `current_profile` |
| `POST /ai/profile/skills-recommend` | `SkillsRecommendRequest` | `current_skills` |
| `POST /ai/cover-letter/generate` | `CoverLetterGenerateRequest` | `job_title`, `company_name`, `job_description`, `resume_text` |
| `POST /ai/cover-letter/assist` | `CoverLetterAssistRequest` | `instruction`, `content` |
| `POST /ai/interview/questions` | `InterviewQuestionsRequest` | `job_title`, `company` |
| `POST /ai/interview/application-questions` | `ApplicationQuestionsRequest` | `job_title`, `company` |
| `POST /ai/company/research` | `CompanyResearchRequest` | `company` |
| `POST /ai/job/summarize` | `JobSummaryRequest` | `title`, `company` |
| `POST /ai/email/generate` | `EmailGenerateRequest` | `email_type` (enum) |
| `POST /ai/matching/enhance` | `MatchingEnhanceRequest` | `job_title`, `company` |

Response format for all endpoints:
```json
{"success": true, "data": { ... }}
```

Error format:
```json
{"success": false, "error": "message", "code": "ERROR_CODE"}
```

---

## Package Exports

All feature functions are exported from `app/ai/features/__init__.py`:

```python
from app.ai.features import ai_generate_resume, ai_enhance_project, ai_enhance_experience
```

---

## Legacy Cover Letter Package

The `app/cover_letter/` package is **deprecated** but not yet removed.

**Migration blockers:**
- `app/orchestrator/coordinator.py` — `CoverLetterExecutor` uses `get_cover_letter_service()`
- `app/application_package/validator.py` — imports `GeneratedCoverLetter`
- `app/application_package/generator.py` — imports `GeneratedCoverLetter`
- `tests/test_cover_letter.py` — full test suite

**New replacement:**
- `app/services/cover_letter.py` — async AI-powered cover letter service
- `app/ai/features/cover_letter.py` — registry-based AI generation and assist

---

## Legacy Prompt Templates

Legacy templates (e.g., `resume-generation`, `cover-letter`) are preserved for backward compatibility but are deprecated. New code should use the `-ai` suffixed variants (e.g., `resume-ai-generation`, `cover-letter-ai`).

---

## Test Coverage

| Module | Tests | File |
|--------|-------|------|
| AI Exceptions & Config | 29 | `tests/test_ai.py` |
| AI API Endpoints | 13 | `tests/test_ai_api.py` |
| AI Features & Schemas | 76 | `tests/test_ai_features.py` |
| Prompt Registry | 42 | `tests/test_prompts.py` |
| Resume Strategy | 40 | `tests/test_resume_strategy.py` |
| **Total** | **200** | |

---

## Migration Notes

### From Sprint 3 to Sprint 3.1

- `app/ai/features/matching.py`: Changed from `AIService.generate()` with hardcoded prompt to `generate_prompted()` with `matching-analysis-ai` template
- `app/ai/features/resume.py`:
  - Added `ai_enhance_project()` and `ai_enhance_experience()`
  - Added `ai_enhance_profile_delegated()` that composes specialized enhancers
  - Updated `ai_enhance_profile()` to focus on summary/headline only
- `app/services/resume.py`: Added `enhance_with_ai` flag to `generate_from_profile()` and `optimize_for_job()`
- `app/api/v1/ai_features.py`: All endpoints now use typed Pydantic request models
- `app/ai/features/schemas.py`: Created with 15 request models + response models
- `app/ai/features/__init__.py`: Now exports all 16 public feature functions

### Prompt Registry Changes

Templates added in Sprint 3.1:
- `matching-analysis-ai` (v1.0.0)
- `project-enhancement-ai` (v1.0.0)
- `experience-enhancement-ai` (v1.0.0)

Template updated in Sprint 3.1:
- `profile-enhancement-ai` — narrowed scope to summary/headline only, removed experience/project embedding

---

End of Document

# Prompt Engineering

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Prompt Engineering |
| Version | 2.0 |
| Status | Approved |
| Related Documents | AI-Architecture.md, AI-Orchestrator.md, Model-Routing.md, Output-Validation.md |

---

# Purpose

This document defines the prompt engineering framework for AI Job Agent Version 2.

The framework ensures that prompts are:

- Consistent
- Reusable
- Maintainable
- Version-controlled
- Secure
- Provider-independent
- Testable

Prompt engineering is treated as an application layer rather than embedded directly into business logic.

---

# Design Goals

The prompt framework shall:

- Separate prompts from application code
- Promote prompt reuse
- Support multiple AI providers
- Produce structured outputs
- Minimize hallucinations
- Reduce prompt size where practical
- Enable iterative improvement
- Support automated testing

---

# Prompt Lifecycle

Every AI request follows a standard prompt lifecycle.

```text
Business Request
        │
        ▼
Task Selection
        │
        ▼
Prompt Template
        │
        ▼
Variable Injection
        │
        ▼
Context Injection
        │
        ▼
Validation
        │
        ▼
AI Provider
```

---

# Prompt Layers

Prompts consist of multiple logical layers.

```text
System Prompt

↓

Task Prompt

↓

Business Rules

↓

Structured Context

↓

User Input

↓

Formatting Instructions
```

Each layer has a clearly defined responsibility.

---

# System Prompt

The system prompt defines global AI behavior.

Responsibilities include:

- Professional tone
- Domain knowledge
- Output consistency
- Safety constraints
- Formatting expectations

The system prompt should remain stable across related tasks.

---

# Task Prompt

Each AI capability has its own task prompt.

Examples:

- Resume Generation
- Resume Optimization
- Cover Letter Generation
- Job Matching
- Resume Critique
- Skill Gap Analysis
- Company Summary
- Interview Preparation
- Application Answers

Task prompts should describe *what* the model should accomplish without including task-specific user data.

---

# Business Rules Layer

Business rules communicate application-specific requirements.

Examples:

- ATS-friendly formatting
- No fabricated experience
- Preserve factual information
- Use measurable achievements when available
- Do not invent certifications
- Respect user preferences

Business rules should be reusable across prompts.

---

# Context Injection

Context is injected after prompt selection.

Possible context includes:

- Career profile
- Resume
- Job description
- Company research
- User preferences
- Existing application draft

Only relevant context should be included.

---

# Variable Substitution

Prompt templates may contain placeholders.

Example:

```text
{{candidate_name}}

{{target_role}}

{{job_description}}

{{skills}}

{{experience}}

{{education}}
```

Variables should be validated before prompt construction.

---

# Prompt Template Structure

A prompt template should contain:

- Metadata
- Version
- Description
- Required variables
- Optional variables
- System instructions
- Task instructions
- Output requirements

Templates should remain human-readable.

---

# Output Instructions

Every prompt should specify the expected output.

Examples:

- Plain text
- Markdown
- JSON
- Structured sections
- Bullet lists
- Tables

Avoid relying on implicit formatting.

---

# Structured Output

Whenever possible, prompts should request structured responses.

Example:

```text
Summary

Skills

Achievements

Recommendations

Final Score
```

Machine-readable formats simplify validation.

---

# Prompt Versioning

Every prompt template should have a version.

Example:

```text
resume_generation_v1

resume_generation_v2

resume_generation_v3
```

Version history enables safe experimentation and rollback.

---

# Prompt Storage

Prompt templates should reside outside application code.

Suggested organization:

```text
prompts/

resume/

cover_letter/

matching/

company/

interview/

shared/
```

Each prompt should have a clear owner and purpose.

---

# Reusable Components

Common instructions should be shared rather than duplicated.

Examples:

- ATS formatting
- Professional writing style
- JSON output rules
- Markdown formatting
- Safety rules

Shared prompt fragments reduce maintenance effort.

---

# Context Size Management

Prompt size should be minimized.

Strategies include:

- Remove irrelevant profile fields
- Summarize long documents
- Limit historical context
- Exclude duplicate information
- Truncate oversized inputs when necessary

Smaller prompts generally improve efficiency and reduce cost.

---

# Hallucination Prevention

Prompts should explicitly instruct models to:

- Use only supplied information
- Avoid inventing experience
- Avoid inventing skills
- Avoid inventing employers
- Avoid fabricating certifications
- Indicate uncertainty when required information is missing

---

# Tone Guidelines

Generated content should be:

- Professional
- Clear
- Concise
- Grammatically correct
- Action-oriented
- Appropriate for recruitment

Tone should remain consistent across providers.

---

# Resume Generation Prompts

Resume prompts should emphasize:

- ATS optimization
- Relevant achievements
- Quantifiable impact
- Appropriate keywords
- Clear formatting
- Truthful representation

The model should not invent missing qualifications.

---

# Cover Letter Prompts

Cover letter prompts should include:

- Target company
- Target role
- Relevant experience
- Candidate strengths
- Motivation
- Professional closing

Cover letters should be personalized rather than generic.

---

# Job Matching Prompts

Matching prompts should evaluate:

- Required skills
- Preferred skills
- Experience alignment
- Education alignment
- Location compatibility
- Employment type
- Seniority level

The output should explain the reasoning behind the match.

---

# Company Summary Prompts

Company prompts should focus on:

- Business overview
- Products or services
- Industry
- Company culture (when supported by reliable context)
- Relevant technologies
- Hiring relevance

Summaries should distinguish factual information from generated explanations.

---

# Interview Preparation Prompts

Interview prompts may generate:

- Technical questions
- Behavioral questions
- Suggested answers
- Preparation tips
- Key topics for review

Questions should align with the target role and provided context.

---

# Prompt Validation

Before execution, prompts should be checked for:

- Missing variables
- Empty required fields
- Unsupported placeholders
- Maximum size
- Invalid formatting

Invalid prompts should fail before reaching the AI provider.

---

# Security

Prompt construction shall:

- Exclude secrets
- Exclude API keys
- Exclude internal credentials
- Minimize personally identifiable information
- Prevent accidental inclusion of unrelated user data

Trusted application instructions should remain distinct from untrusted user input.

---

# Prompt Injection Mitigation

User-provided text may attempt to override instructions.

Mitigation strategies include:

- Separate trusted instructions from user content
- Treat uploaded documents as data, not instructions
- Validate structured outputs before use
- Ignore attempts to modify system behavior through user content

---

# Testing

Prompt testing should verify:

- Variable substitution
- Template rendering
- Required context
- Output format
- Consistency across providers
- Hallucination resistance
- Regression between prompt versions

Representative test cases should be maintained for each task.

---

# Maintenance

Prompt changes should:

- Be reviewed
- Be versioned
- Include rationale
- Be tested
- Be documented

Prompt quality should be monitored using production metrics and user feedback.

---

# Acceptance Criteria

The prompt engineering framework is considered complete when:

- Prompts are externalized from application code.
- Templates are reusable and version-controlled.
- Context injection is standardized.
- Output requirements are explicit.
- Prompt validation occurs before execution.
- Prompt behavior is testable.
- Security considerations are incorporated.

---

# Related Documents

- AI-Architecture.md
- AI-Orchestrator.md
- Model-Routing.md
- Output-Validation.md

---

End of Document
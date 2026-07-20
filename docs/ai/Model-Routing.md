# Model Routing

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Model Routing |
| Version | 2.0 |
| Status | Approved |
| Related Documents | AI-Architecture.md, AI-Orchestrator.md, Prompt-Engineering.md, Output-Validation.md |

---

# Purpose

This document defines how AI Job Agent Version 2 selects AI providers and models for each task.

The routing layer is responsible for choosing the most appropriate model based on:

- Task type
- Model capabilities
- Provider health
- Context size
- Latency
- Cost
- User preferences
- Availability

Business services should never select AI models directly.

---

# Design Goals

The routing system shall be:

- Provider independent
- Model independent
- Configurable
- Observable
- Fault tolerant
- Extensible
- Cost-aware
- Performance optimized

Changing providers or models should require configuration updates rather than application code changes.

---

# Architecture

```text
Business Service
        │
        ▼
AI Orchestrator
        │
        ▼
Model Router
        │
        ├──────────────┐
        ▼              ▼
Provider Selector   Model Selector
        │              │
        └──────┬───────┘
               ▼
      Provider Adapter
               │
               ▼
         AI Provider
```

---

# Routing Workflow

```text
Receive AI Task
        │
        ▼
Identify Task Type
        │
        ▼
Load Routing Policy
        │
        ▼
Evaluate Providers
        │
        ▼
Evaluate Models
        │
        ▼
Health Check
        │
        ▼
Select Best Candidate
        │
        ▼
Execute Request
```

---

# Supported Providers

Initial providers include:

- Ollama
- OpenRouter

Future providers may include:

- OpenAI
- Anthropic
- Google Gemini
- Azure OpenAI
- Self-hosted inference servers

Each provider must implement the common provider interface.

---

# Model Capability Categories

Models should be categorized by capability rather than by provider.

Examples:

| Capability | Example Tasks |
|------------|---------------|
| Coding | Code generation, debugging |
| Reasoning | Multi-step analysis |
| Writing | Resume generation, cover letters |
| Summarization | Company summaries |
| Classification | Job categorization |
| Extraction | Resume parsing |
| General Chat | User assistance |

A single model may support multiple capability categories.

---

# Task-to-Capability Mapping

| Task | Primary Capability |
|------|--------------------|
| Resume Generation | Writing |
| Resume Optimization | Writing |
| Cover Letter | Writing |
| Job Matching | Reasoning |
| Company Summary | Summarization |
| Skill Gap Analysis | Reasoning |
| Interview Questions | Reasoning |
| Resume Parsing | Extraction |
| Application Answers | Writing |

Routing decisions begin with the required capability rather than a specific model name.

---

# Provider Selection

Provider selection should consider:

- Availability
- Health status
- Supported capabilities
- Configured priority
- User preference
- Cost policy

If multiple providers satisfy the requirements, the routing policy determines the preferred choice.

---

# Model Selection

Within a provider, model selection should consider:

- Capability match
- Context window
- Response quality
- Latency
- Reliability
- Token limits
- Configuration preferences

The routing engine should avoid selecting models that cannot handle the required context size.

---

# Routing Policies

Routing policies define which models are preferred for each task.

Example policy:

```text
Resume Generation

↓

Preferred:
Provider A → Model X

Fallback:
Provider B → Model Y

Final Fallback:
Provider A → Model Z
```

Policies should be configurable without modifying business logic.

---

# User Preferences

Users may configure preferences such as:

- Preferred provider
- Preferred model
- Local-only execution
- Cloud-only execution
- Automatic routing

User preferences should be honored when compatible with system policies.

---

# Health Monitoring

Each provider should expose health information.

Health checks may include:

- Connectivity
- Authentication status
- Response latency
- Error rate
- Availability

Unhealthy providers should be temporarily deprioritized.

---

# Fallback Strategy

If the selected model fails:

```text
Primary Model
        │
        ▼
Retry
        │
        ▼
Fallback Model
        │
        ▼
Fallback Provider
        │
        ▼
Standard Error Response
```

Fallback order should be deterministic and configurable.

---

# Retry Policy

Retryable failures include:

- Network interruptions
- Temporary provider outages
- Rate limiting
- Timeout

Non-retryable failures include:

- Invalid prompt
- Unsupported task
- Authentication failure
- Configuration errors

Retries should use exponential backoff.

---

# Context Window Management

Before routing, the router should estimate prompt size.

If the estimated context exceeds a model's limits:

1. Select a model with a larger context window.
2. Compress or summarize context if permitted.
3. Reject the request with a clear error if no suitable model exists.

Context truncation should be explicit and controlled.

---

# Cost-Aware Routing

Where cost information is available, routing may consider:

- Estimated token usage
- Provider pricing
- Monthly budget
- Task priority

Example strategy:

- Use lower-cost models for routine summarization.
- Reserve higher-capability models for complex reasoning or long-form writing.

Cost policies should never compromise correctness for critical tasks.

---

# Latency Optimization

Latency-sensitive tasks include:

- Interactive chat
- Resume editing suggestions
- Job search assistance

Long-running tasks include:

- Resume generation
- Cover letter generation
- Company research

Routing policies should optimize for responsiveness where appropriate.

---

# Concurrency

The router should support concurrent requests.

Concurrency policies should account for:

- Provider rate limits
- Local hardware capacity
- User-defined limits
- Background task priorities

Resource contention should be handled gracefully.

---

# Caching

Routing metadata may be cached.

Examples:

- Provider health
- Model capabilities
- Routing policies

AI-generated content caching is handled separately by the orchestrator.

---

# Configuration

Routing configuration should define:

- Enabled providers
- Enabled models
- Preferred order
- Retry limits
- Timeout values
- Health thresholds
- Cost limits
- Latency thresholds

Configuration should be environment-specific and version-controlled.

---

# Observability

The routing layer should record:

- Selected provider
- Selected model
- Routing decision reason
- Execution latency
- Retry count
- Fallback usage
- Success rate
- Failure rate

These metrics support tuning and operational monitoring.

---

# Security

The routing layer shall:

- Never expose provider credentials
- Validate routing configuration
- Prevent unauthorized provider access
- Enforce provider-specific security requirements
- Isolate provider failures

Routing decisions should not expose internal infrastructure details to end users.

---

# Testing

Routing tests should verify:

- Provider selection
- Model selection
- Capability mapping
- Health-based routing
- Retry behavior
- Fallback behavior
- Cost-aware policies
- User preference overrides

Provider implementations should be mockable for deterministic testing.

---

# Acceptance Criteria

The model routing layer is considered complete when:

- Routing decisions are provider-independent.
- Model selection is capability-based.
- Health and availability influence routing.
- Fallback chains are configurable.
- Cost and latency policies are supported.
- Routing behavior is observable and testable.
- New providers and models can be added without modifying business logic.

---

# Related Documents

- AI-Architecture.md
- AI-Orchestrator.md
- Prompt-Engineering.md
- Output-Validation.md

---

End of Document
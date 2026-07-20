# Provider Interface

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Provider Interface |
| Version | 2.0 |
| Status | Approved |
| Related Documents | Provider-Architecture.md, OpenRouter.md, Ollama.md, AI-Orchestrator.md |

---

# Purpose

This document defines the common provider interface that every AI provider must implement.

The interface enables AI Job Agent Version 2 to interact with multiple providers through a single, stable contract without requiring provider-specific logic in business services.

Current providers include:

- Ollama
- OpenRouter

Future providers can be integrated by implementing this interface.

---

# Design Principles

The provider interface shall be:

- Stable
- Provider independent
- Extensible
- Backward compatible
- Testable
- Observable
- Secure

The interface defines behavior rather than implementation.

---

# High-Level Architecture

```text
                AI Orchestrator
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
OpenRouter Adapter  Ollama Adapter  Future Adapter
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              Provider Interface
```

All provider implementations communicate through this interface.

---

# Responsibilities

Every provider implementation is responsible for:

- Validating configuration
- Authenticating requests
- Executing inference
- Streaming responses
- Parsing provider output
- Normalizing metadata
- Reporting health
- Reporting usage
- Translating provider-specific errors

Business logic must never be implemented inside providers.

---

# Provider Lifecycle

```text
Application Startup

↓

Load Configuration

↓

Validate Configuration

↓

Initialize Provider

↓

Health Check

↓

Ready

↓

Handle Requests

↓

Shutdown
```

Providers should remain reusable throughout the application lifetime.

---

# Core Interface

Every provider shall implement the following logical operations.

---

## Initialize

Purpose:

Prepare the provider for use.

Responsibilities:

- Load configuration
- Validate credentials
- Allocate resources
- Prepare HTTP client
- Initialize caches

Initialization should fail fast when configuration is invalid.

---

## Validate Configuration

Verify:

- Required settings
- Credentials
- Endpoint
- Timeouts
- Provider-specific options

Invalid configuration should prevent provider registration.

---

## Health Check

Return provider health information.

Checks may include:

- Connectivity
- Authentication
- Basic inference
- Model availability
- Latency

Health responses should use a standardized format.

---

## Execute Request

Execute a complete AI request.

Input:

- Prompt
- Context
- Generation options
- Selected model

Output:

- Normalized response

Providers should not expose raw provider responses outside the adapter.

---

## Execute Streaming Request

Support streamed responses where available.

Streaming interface should support:

- Incremental output
- Cancellation
- Timeout
- Error propagation
- Completion notification

Providers that do not support streaming should clearly report this capability.

---

## List Models

Return available models.

Each model should include metadata such as:

- Identifier
- Display name
- Provider
- Context window
- Capabilities
- Availability
- Status

The router uses this information when selecting models.

---

## Report Usage

Where supported, return usage information.

Examples:

- Prompt tokens
- Completion tokens
- Total tokens
- Execution duration
- Estimated cost

Unavailable metrics should use consistent defaults rather than inconsistent structures.

---

## Shutdown

Release resources gracefully.

Examples:

- Close HTTP connections
- Flush metrics
- Release memory
- Stop background workers

Shutdown should be safe to call multiple times.

---

# Request Model

Every provider receives a standardized request.

Typical fields include:

- Request ID
- Task type
- Model
- System prompt
- User prompt
- Context
- Generation parameters
- Timeout
- Streaming flag

The request model should remain provider-independent.

---

# Response Model

Every provider returns the same logical response.

Fields include:

- Generated content
- Provider
- Model
- Finish reason
- Usage
- Execution time
- Metadata
- Validation status (if applicable)

Consumers should never inspect provider-specific payloads.

---

# Capability Definition

Providers advertise supported capabilities.

Examples:

- Chat completion
- Structured output
- Streaming
- Long context
- Function calling
- Reasoning
- Code generation
- Embeddings
- Image understanding (future)

Capabilities should be discoverable programmatically.

---

# Error Contract

All provider-specific errors must be translated into common application errors.

Supported categories include:

- AuthenticationFailed
- ProviderUnavailable
- Timeout
- RateLimited
- InvalidRequest
- UnsupportedCapability
- UnsupportedModel
- ConfigurationError
- InternalProviderError

Applications should not depend on provider-native error messages.

---

# Timeout Handling

Providers should support configurable timeouts.

Typical categories:

| Operation | Timeout |
|-----------|----------|
| Health Check | Short |
| Standard Request | Medium |
| Streaming | Long |
| Long-form Generation | Long |

Timeout values should be externally configurable.

---

# Retry Compatibility

Providers should expose enough information for the orchestrator to decide whether a request may be retried.

Retryable examples:

- Timeout
- Network interruption
- Temporary service outage

Non-retryable examples:

- Authentication failure
- Invalid request
- Unsupported model

Retry policy remains the responsibility of the orchestrator.

---

# Streaming Contract

Streaming implementations should provide:

- Ordered chunks
- Completion event
- Error event
- Cancellation support
- Timeout detection

Consumers should receive a consistent stream regardless of provider.

---

# Health Status

Health should include:

- Status
- Response latency
- Last successful check
- Provider version (if available)
- Available models
- Diagnostic information

Diagnostic information should avoid exposing secrets.

---

# Configuration Contract

Providers should support common configuration concepts.

Examples:

- Enabled
- Endpoint
- Timeout
- Retry policy
- Preferred models
- Maximum concurrency
- Logging level

Provider-specific configuration may extend the base contract.

---

# Security Requirements

Every provider shall:

- Protect credentials
- Use secure communication
- Validate configuration
- Avoid secret leakage
- Sanitize logs
- Prevent unauthorized access

Sensitive configuration should never be returned through diagnostic APIs.

---

# Observability

Every provider should emit standardized metrics.

Examples:

- Requests
- Successes
- Failures
- Latency
- Retry count
- Timeout count
- Streaming sessions
- Usage metrics

Metrics should support comparison across providers.

---

# Logging

Provider logs should contain:

- Request ID
- Provider
- Model
- Duration
- Outcome

Logs must never contain:

- API keys
- Secrets
- Full prompts
- Personally identifiable information

---

# Extensibility

Adding a provider should require only:

1. Implement the interface.
2. Register the provider.
3. Configure routing.
4. Add automated tests.

The interface should remain stable as providers evolve.

---

# Compatibility

The interface should support:

- Local providers
- Cloud providers
- Hybrid providers
- Future multimodal providers

Backward compatibility should be maintained whenever practical.

---

# Testing

Every provider implementation should pass a common compliance test suite covering:

- Initialization
- Configuration validation
- Health checks
- Request execution
- Streaming
- Error translation
- Usage reporting
- Shutdown

Compliance tests ensure consistent behavior across providers.

---

# Acceptance Criteria

The provider interface is considered complete when:

- All providers implement the same contract.
- Requests and responses are standardized.
- Capabilities are discoverable.
- Errors are normalized.
- Health reporting is consistent.
- Providers are interchangeable.
- Compliance tests validate conformance.

---

# Related Documents

- Provider-Architecture.md
- OpenRouter.md
- Ollama.md
- AI-Orchestrator.md
- Model-Routing.md

---

End of Document
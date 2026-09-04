from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProviderState(str, Enum):
    READY = "ready"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"
    NOT_IMPLEMENTED = "not_implemented"
    INITIALIZATION_FAILED = "initialization_failed"
    UNKNOWN = "unknown"


@dataclass
class ProviderStatus:
    id: str
    name: str
    state: ProviderState
    category: str
    detail: str = ""


KNOWN_JOB_PROVIDERS: set[str] = {
    "adzuna", "wellfound", "y_combinator", "greenhouse", "lever", "ashby",
    "naukri", "foundit", "internshala", "freshersworld", "unstop", "workday",
    "smartrecruiters", "bamboohr", "recruitee", "mock",
}

IMPLEMENTED_JOB_PROVIDERS: set[str] = KNOWN_JOB_PROVIDERS

KNOWN_AI_PROVIDERS: set[str] = {"openrouter", "ollama", "openai", "anthropic", "gemini"}
IMPLEMENTED_AI_PROVIDERS: set[str] = {"openrouter", "ollama", "openai", "anthropic", "gemini"}

KNOWN_ATS_PROVIDERS: set[str] = {
    "greenhouse", "lever", "ashby", "workday",
    "smartrecruiters", "bamboohr", "recruitee",
}
IMPLEMENTED_ATS_PROVIDERS: set[str] = KNOWN_ATS_PROVIDERS

KNOWN_SUBMISSION_PROVIDERS: set[str] = {
    "greenhouse", "lever", "ashby", "workday",
    "smartrecruiters", "bamboohr", "recruitee",
}
IMPLEMENTED_SUBMISSION_PROVIDERS: set[str] = KNOWN_SUBMISSION_PROVIDERS


def get_job_provider_statuses(*, configured: list[str] | None = None, registered: list[str] | None = None) -> list[ProviderStatus]:
    configured_set = {p.lower().strip() for p in (configured or [])}
    registered_set = set(registered or [])

    results: list[ProviderStatus] = []
    for name in sorted(configured_set):
        if name in registered_set:
            results.append(ProviderStatus(id=name, name=name, state=ProviderState.READY, category="discovery"))
        elif name in IMPLEMENTED_JOB_PROVIDERS:
            results.append(ProviderStatus(
                id=name, name=name, state=ProviderState.UNAVAILABLE,
                category="discovery", detail="Provider registered but not currently available",
            ))
        else:
            results.append(ProviderStatus(
                id=name, name=name, state=ProviderState.NOT_IMPLEMENTED,
                category="discovery", detail="No implementation exists for this provider",
            ))
    return results


def get_ai_provider_statuses(*, configured: list[str] | None = None, registered: list[str] | None = None) -> list[ProviderStatus]:
    configured_set = {p.lower().strip() for p in (configured or [])}
    registered_set = set(registered or [])

    results: list[ProviderStatus] = []
    for name in sorted(configured_set):
        if name not in KNOWN_AI_PROVIDERS:
            results.append(ProviderStatus(
                id=name, name=name, state=ProviderState.INITIALIZATION_FAILED,
                category="ai", detail="Invalid AI provider name",
            ))
        elif name in registered_set:
            results.append(ProviderStatus(id=name, name=name, state=ProviderState.READY, category="ai"))
        elif name in IMPLEMENTED_AI_PROVIDERS:
            results.append(ProviderStatus(
                id=name, name=name, state=ProviderState.UNAVAILABLE,
                category="ai", detail="Provider registered but not currently available",
            ))
        else:
            results.append(ProviderStatus(
                id=name, name=name, state=ProviderState.NOT_IMPLEMENTED,
                category="ai", detail="No implementation exists for this provider",
            ))
    return results


def get_ats_provider_statuses(*, configured: list[str] | None = None, registered: list[str] | None = None) -> list[ProviderStatus]:
    configured_set = {p.lower().strip() for p in (configured or [])}
    registered_set = set(registered or [])

    results: list[ProviderStatus] = []
    for name in sorted(configured_set):
        if name in registered_set:
            results.append(ProviderStatus(id=name, name=name, state=ProviderState.READY, category="ats"))
        elif name in IMPLEMENTED_ATS_PROVIDERS:
            results.append(ProviderStatus(
                id=name, name=name, state=ProviderState.UNAVAILABLE,
                category="ats", detail="Provider registered but not currently available",
            ))
        else:
            results.append(ProviderStatus(
                id=name, name=name, state=ProviderState.NOT_IMPLEMENTED,
                category="ats", detail="No implementation exists for this provider",
            ))
    return results


def get_submission_provider_statuses(*, configured: list[str] | None = None, registered: list[str] | None = None) -> list[ProviderStatus]:
    configured_set = {p.lower().strip() for p in (configured or [])}
    registered_set = set(registered or [])

    results: list[ProviderStatus] = []
    for name in sorted(configured_set):
        if name in registered_set:
            results.append(ProviderStatus(id=name, name=name, state=ProviderState.READY, category="submission"))
        elif name in IMPLEMENTED_SUBMISSION_PROVIDERS:
            results.append(ProviderStatus(
                id=name, name=name, state=ProviderState.UNAVAILABLE,
                category="submission", detail="Provider registered but not currently available",
            ))
        else:
            results.append(ProviderStatus(
                id=name, name=name, state=ProviderState.NOT_IMPLEMENTED,
                category="submission", detail="No implementation exists for this provider",
            ))
    return results


def get_all_provider_statuses(
    *,
    job_configured: list[str] | None = None,
    job_registered: list[str] | None = None,
    ai_configured: list[str] | None = None,
    ai_registered: list[str] | None = None,
    ats_configured: list[str] | None = None,
    ats_registered: list[str] | None = None,
    submission_configured: list[str] | None = None,
    submission_registered: list[str] | None = None,
) -> list[dict[str, Any]]:
    results: list[ProviderStatus] = []
    results.extend(get_job_provider_statuses(configured=job_configured, registered=job_registered))
    results.extend(get_ai_provider_statuses(configured=ai_configured, registered=ai_registered))
    results.extend(get_ats_provider_statuses(configured=ats_configured, registered=ats_registered))
    results.extend(get_submission_provider_statuses(configured=submission_configured, registered=submission_registered))
    return [{"id": s.id, "name": s.name, "state": s.state.value, "category": s.category, "detail": s.detail} for s in results]

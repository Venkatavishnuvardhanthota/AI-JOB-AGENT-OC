from app.core.provider_state import (
    ProviderState,
    get_job_provider_statuses,
    get_ai_provider_statuses,
    get_all_provider_statuses,
)


class TestProviderState:
    def test_job_provider_ready(self):
        statuses = get_job_provider_statuses(configured=["greenhouse"], registered=["greenhouse"])
        assert len(statuses) == 1
        assert statuses[0].id == "greenhouse"
        assert statuses[0].state == ProviderState.READY

    def test_job_provider_not_implemented(self):
        statuses = get_job_provider_statuses(configured=["linkedin"], registered=[])
        assert len(statuses) == 1
        assert statuses[0].id == "linkedin"
        assert statuses[0].state == ProviderState.NOT_IMPLEMENTED

    def test_ai_provider_ready(self):
        statuses = get_ai_provider_statuses(configured=["openrouter"], registered=["openrouter"])
        assert len(statuses) == 1
        assert statuses[0].id == "openrouter"
        assert statuses[0].state == ProviderState.READY

    def test_ai_provider_not_implemented(self):
        statuses = get_ai_provider_statuses(configured=["openai"], registered=[])
        assert len(statuses) == 1
        assert statuses[0].id == "openai"
        assert statuses[0].state == ProviderState.NOT_IMPLEMENTED

    def test_ai_provider_invalid_name(self):
        statuses = get_ai_provider_statuses(configured=["nonexistent_provider"], registered=[])
        assert len(statuses) == 1
        assert statuses[0].state == ProviderState.INITIALIZATION_FAILED

    def test_multiple_providers(self):
        statuses = get_all_provider_statuses(
            job_configured=["greenhouse", "lever"],
            job_registered=["greenhouse"],
            ai_configured=["openrouter", "ollama", "openai"],
            ai_registered=["openrouter"],
        )
        ids = [s["id"] for s in statuses]
        assert "greenhouse" in ids
        assert "lever" in ids
        assert "openrouter" in ids
        assert "ollama" in ids
        assert "openai" in ids

    def test_empty_config(self):
        statuses = get_job_provider_statuses(configured=[], registered=[])
        assert statuses == []

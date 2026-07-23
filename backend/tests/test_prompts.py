from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from app.ai.exceptions import (
    MissingVariableError,
    PromptTemplateError,
    ResponseParsingError,
    ResponseValidationError,
)
from app.ai.prompts.parser import ResponseParser
from app.ai.prompts.registry import PromptTemplateRegistry
from app.ai.prompts.renderer import PromptRenderer
from app.ai.prompts.template import PromptTemplate
from app.ai.schemas import AIResponse, UsageMetrics
from app.ai.service import AIService


class FakeResponseModel(BaseModel):
    title: str
    score: int


class TestPromptTemplate:
    def test_variables_extracted(self):
        t = PromptTemplate(name="test", template="Hello {name}, you are {age} years old")
        assert set(t.variables) == {"name", "age"}

    def test_no_variables(self):
        t = PromptTemplate(name="static", template="Hello world")
        assert t.variables == []

    def test_default_values(self):
        t = PromptTemplate(name="foo", template="Bar")
        assert t.description is None
        assert t.system_prompt is None
        assert t.version == "1.0.0"

    def test_empty_name_rejected(self):
        with pytest.raises(Exception):
            PromptTemplate(name="", template="x")

    def test_empty_template_rejected(self):
        with pytest.raises(Exception):
            PromptTemplate(name="x", template="")


class TestPromptTemplateRegistry:
    def test_register_and_get(self):
        reg = PromptTemplateRegistry()
        t = PromptTemplate(name="greet", template="Hello {name}")
        reg.register(t)
        assert reg.get("greet") == t

    def test_get_unknown_raises(self):
        reg = PromptTemplateRegistry()
        with pytest.raises(PromptTemplateError):
            reg.get("nope")

    def test_list_empty(self):
        reg = PromptTemplateRegistry()
        assert reg.list() == []

    def test_list_names_empty(self):
        reg = PromptTemplateRegistry()
        assert reg.list_names() == []

    def test_register_and_list(self):
        reg = PromptTemplateRegistry()
        reg.register(PromptTemplate(name="a", template="A"))
        reg.register(PromptTemplate(name="b", template="B"))
        names = [t.name for t in reg.list()]
        assert set(names) == {"a", "b"}

    def test_list_names(self):
        reg = PromptTemplateRegistry()
        reg.register(PromptTemplate(name="x", template="X"))
        assert reg.list_names() == ["x"]

    def test_unregister(self):
        reg = PromptTemplateRegistry()
        reg.register(PromptTemplate(name="del", template="X"))
        reg.unregister("del")
        assert reg.count() == 0

    def test_unregister_unknown_raises(self):
        reg = PromptTemplateRegistry()
        with pytest.raises(PromptTemplateError):
            reg.unregister("nope")

    def test_is_registered(self):
        reg = PromptTemplateRegistry()
        reg.register(PromptTemplate(name="exists", template="X"))
        assert reg.is_registered("exists")
        assert not reg.is_registered("nope")

    def test_count(self):
        reg = PromptTemplateRegistry()
        assert reg.count() == 0
        reg.register(PromptTemplate(name="a", template="A"))
        assert reg.count() == 1
        reg.register(PromptTemplate(name="b", template="B"))
        assert reg.count() == 2

    def test_clear(self):
        reg = PromptTemplateRegistry()
        reg.register(PromptTemplate(name="x", template="X"))
        reg.clear()
        assert reg.count() == 0

    def test_overwrite_warning(self):
        reg = PromptTemplateRegistry()
        t1 = PromptTemplate(name="dup", template="v1")
        t2 = PromptTemplate(name="dup", template="v2")
        reg.register(t1)
        reg.register(t2)
        assert reg.get("dup").template == "v2"


class TestPromptRenderer:
    def test_render_simple(self):
        renderer = PromptRenderer()
        t = PromptTemplate(name="t", template="Hello {name}")
        result = renderer.render(t, {"name": "World"})
        assert result == "Hello World"

    def test_render_multiple(self):
        renderer = PromptRenderer()
        t = PromptTemplate(name="t", template="{a} and {b}")
        result = renderer.render(t, {"a": "1", "b": "2"})
        assert result == "1 and 2"

    def test_missing_variable_raises(self):
        renderer = PromptRenderer()
        t = PromptTemplate(name="t", template="Hello {name}, age {age}")
        with pytest.raises(MissingVariableError) as exc:
            renderer.render(t, {"name": "World"})
        assert "age" in str(exc.value)

    def test_extra_variables_ignored(self):
        renderer = PromptRenderer()
        t = PromptTemplate(name="t", template="{a}")
        result = renderer.render(t, {"a": "x", "b": "y"})
        assert result == "x"

    def test_unresolved_placeholder_raises(self):
        renderer = PromptRenderer()
        t = PromptTemplate(name="t", template="{a} {b}")
        with pytest.raises(MissingVariableError):
            renderer.render(t, {"a": "hello"})

    def test_no_variables(self):
        renderer = PromptRenderer()
        t = PromptTemplate(name="t", template="Static text")
        result = renderer.render(t, {})
        assert result == "Static text"


class TestResponseParser:
    def test_extract_json_plain(self):
        parser = ResponseParser()
        result = parser.extract_json('{"title": "Hi", "score": 5}')
        assert result == {"title": "Hi", "score": 5}

    def test_extract_json_fenced(self):
        parser = ResponseParser()
        content = 'Here is the result:\n```json\n{"title": "Hi", "score": 5}\n```'
        result = parser.extract_json(content)
        assert result == {"title": "Hi", "score": 5}

    def test_extract_json_fenced_no_lang(self):
        parser = ResponseParser()
        content = '```\n{"title": "Hi"}\n```'
        result = parser.extract_json(content)
        assert result == {"title": "Hi"}

    def test_extract_json_with_extra_whitespace(self):
        parser = ResponseParser()
        content = '  \n  {"a": 1}  \n'
        result = parser.extract_json(content)
        assert result == {"a": 1}

    def test_extract_json_empty_raises(self):
        parser = ResponseParser()
        with pytest.raises(ResponseParsingError, match="empty"):
            parser.extract_json("")

    def test_extract_json_whitespace_raises(self):
        parser = ResponseParser()
        with pytest.raises(ResponseParsingError):
            parser.extract_json("   \n  \n  ")

    def test_extract_json_malformed_raises(self):
        parser = ResponseParser()
        with pytest.raises(ResponseParsingError):
            parser.extract_json("not json at all")

    def test_parse_valid(self):
        parser = ResponseParser()
        result = parser.parse('{"title": "Hello", "score": 42}', FakeResponseModel)
        assert isinstance(result, FakeResponseModel)
        assert result.title == "Hello"
        assert result.score == 42

    def test_parse_fenced_valid(self):
        parser = ResponseParser()
        content = '```json\n{"title": "A", "score": 1}\n```'
        result = parser.parse(content, FakeResponseModel)
        assert result.title == "A"

    def test_parse_validation_error(self):
        parser = ResponseParser()
        with pytest.raises(ResponseValidationError):
            parser.parse('{"title": "Hi"}', FakeResponseModel)

    def test_parse_invalid_json_raises_parsing_error(self):
        parser = ResponseParser()
        with pytest.raises(ResponseParsingError):
            parser.parse("bad json", FakeResponseModel)

    def test_fix_single_quotes(self):
        parser = ResponseParser()
        result = parser.extract_json("{'title': 'Hi', 'score': 5}")
        assert result == {"title": "Hi", "score": 5}


class TestAIServiceStructured:
    @pytest.fixture
    def mock_registry(self):
        reg = MagicMock()
        provider = AsyncMock()
        provider.generate.return_value = AIResponse(
            content='{"title": "Engineer", "score": 95}',
            model="test-model",
            provider="test-provider",
            usage=UsageMetrics(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )
        reg.resolve.return_value = provider
        reg.list_providers.return_value = ["test-provider"]
        return reg

    @pytest.fixture
    def mock_config(self):
        cfg = MagicMock()
        cfg.default_provider = "test-provider"
        cfg.default_model = "test-model"
        cfg.temperature = 0.7
        cfg.max_tokens = 100
        cfg.fallback_provider = None
        return cfg

    @pytest.fixture
    def prompt_registry(self):
        reg = PromptTemplateRegistry()
        reg.register(
            PromptTemplate(
                name="test-job",
                template="Write a title for {job_title} with score {level}",
                system_prompt="You are a job analyzer.",
            )
        )
        return reg

    @pytest.fixture
    def service(self, mock_registry, mock_config, prompt_registry):
        return AIService(
            registry=mock_registry,
            config=mock_config,
            prompt_registry=prompt_registry,
        )

    @pytest.fixture
    def service_no_prompt_registry(self, mock_registry, mock_config):
        return AIService(registry=mock_registry, config=mock_config)

    async def test_generate_structured_success(self, service):
        result = await service.generate_structured(
            template_name="test-job",
            variables={"job_title": "Software Engineer", "level": "5"},
            response_model=FakeResponseModel,
        )
        assert isinstance(result, FakeResponseModel)
        assert result.title == "Engineer"
        assert result.score == 95

    async def test_generate_structured_overrides(self, service):
        result = await service.generate_structured(
            template_name="test-job",
            variables={"job_title": "Engineer", "level": "3"},
            response_model=FakeResponseModel,
            model="override-model",
            temperature=0.1,
            max_tokens=50,
        )
        assert isinstance(result, FakeResponseModel)

    async def test_generate_prompted_success(self, service):
        response = await service.generate_prompted(
            template_name="test-job",
            variables={"job_title": "Engineer", "level": "3"},
        )
        assert isinstance(response, AIResponse)
        assert response.content is not None

    async def test_generate_structured_missing_variable(self, service):
        with pytest.raises(MissingVariableError):
            await service.generate_structured(
                template_name="test-job",
                variables={"job_title": "Engineer"},
                response_model=FakeResponseModel,
            )

    async def test_generate_structured_template_not_found(self, service):
        with pytest.raises(PromptTemplateError):
            await service.generate_structured(
                template_name="nope",
                variables={"x": "y"},
                response_model=FakeResponseModel,
            )

    async def test_generate_structured_no_prompt_registry(self, service_no_prompt_registry):
        with pytest.raises(Exception):
            await service_no_prompt_registry.generate_structured(
                template_name="test-job",
                variables={"x": "y"},
                response_model=FakeResponseModel,
            )

    async def test_generate_prompted_no_prompt_registry(self, service_no_prompt_registry):
        with pytest.raises(Exception):
            await service_no_prompt_registry.generate_prompted(
                template_name="test-job",
                variables={"x": "y"},
            )

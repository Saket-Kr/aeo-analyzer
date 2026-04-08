import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import FanOutLLMResponse
from app.services.llm_client import LLMServiceError, generate_sub_queries


VALID_RESPONSE = {
    "sub_queries": [
        {"type": "comparative", "query": "X vs Y for SEO"},
        {"type": "comparative", "query": "AI tool A vs tool B"},
        {"type": "feature_specific", "query": "AI tool with keyword analysis"},
        {"type": "feature_specific", "query": "AI tool with SERP tracking"},
        {"type": "use_case", "query": "using AI for blog post optimization"},
        {"type": "use_case", "query": "AI tool for e-commerce product pages"},
        {"type": "how_to", "query": "how to use AI for meta descriptions"},
        {"type": "how_to", "query": "how to set up AI writing workflow"},
        {"type": "trust_signals", "query": "AI SEO tool agency reviews"},
        {"type": "trust_signals", "query": "case studies AI writing ROI"},
        {"type": "definitional", "query": "what is AI SEO writing"},
        {"type": "definitional", "query": "AI writing vs manual SEO"},
    ]
}


def _mock_completion(content: str):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    return completion


@pytest.mark.asyncio
async def test_valid_llm_response():
    with patch("app.services.llm_client.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_completion(json.dumps(VALID_RESPONSE))
        )
        result = await generate_sub_queries("best AI writing tool")
        assert len(result.sub_queries) == 12
        types = {sq.type for sq in result.sub_queries}
        assert len(types) == 6


@pytest.mark.asyncio
async def test_retry_on_failure_then_success():
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            from openai import APIConnectionError
            raise APIConnectionError(request=MagicMock())
        return _mock_completion(json.dumps(VALID_RESPONSE))

    with patch("app.services.llm_client.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=side_effect)
        result = await generate_sub_queries("test query")
        assert len(result.sub_queries) == 12
        assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted_raises_error():
    from openai import APITimeoutError

    with patch("app.services.llm_client.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )
        with pytest.raises(LLMServiceError) as exc_info:
            await generate_sub_queries("test query")
        assert exc_info.value.attempt == 3
        assert exc_info.value.error_type == "APITimeoutError"


@pytest.mark.asyncio
async def test_invalid_json_triggers_retry():
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            return _mock_completion("not valid json {{{")
        return _mock_completion(json.dumps(VALID_RESPONSE))

    with patch("app.services.llm_client.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=side_effect)
        result = await generate_sub_queries("test query")
        assert len(result.sub_queries) == 12


def test_pydantic_validation_of_response():
    response = FanOutLLMResponse.model_validate(VALID_RESPONSE)
    assert len(response.sub_queries) == 12
    assert all(sq.type in [
        "comparative", "feature_specific", "use_case",
        "trust_signals", "how_to", "definitional"
    ] for sq in response.sub_queries)


@pytest.mark.asyncio
async def test_partial_response_with_fewer_queries():
    partial = {
        "sub_queries": [
            {"type": "comparative", "query": "X vs Y"},
            {"type": "definitional", "query": "what is X"},
        ]
    }
    with patch("app.services.llm_client.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_completion(json.dumps(partial))
        )
        result = await generate_sub_queries("test query")
        assert len(result.sub_queries) == 2

import asyncio
import json
import random
from abc import ABC, abstractmethod

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
)

from app.constants import (
    LLM_API_KEY,
    LLM_BASE_DELAY,
    LLM_BASE_URL,
    LLM_MAX_RETRIES,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
    SUB_QUERY_TYPES,
)
from app.models.schemas import FanOutLLMResponse


class LLMServiceError(Exception):
    def __init__(self, error_type: str, detail: str, attempt: int):
        self.error_type = error_type
        self.detail = detail
        self.attempt = attempt


client = AsyncOpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    timeout=LLM_TIMEOUT,
)

SYSTEM_PROMPT = """You are a search query decomposition engine. Given a target query, you simulate how AI-powered search engines (Perplexity, ChatGPT Search, Google AI Mode) decompose it into sub-queries to build a comprehensive answer.

Generate 10 to 15 sub-queries across these 6 types. Produce at least 2 sub-queries for each type.

Sub-query types:
1. comparative — Compare the subject against alternatives or competitors
2. feature_specific — Focus on a specific capability, feature, or attribute
3. use_case — Real-world application or scenario where the subject is applied
4. how_to — Step-by-step procedural or instructional query
5. trust_signals — Reviews, case studies, credibility markers, social proof
6. definitional — Conceptual "what is" query explaining the subject

Rules:
- Each sub-query must be specific to the provided target query
- Sub-queries must be diverse — avoid near-duplicates
- Only use the 6 types listed above
- Return a JSON object with a single key "sub_queries" containing an array of objects, each with "type" and "query" fields

Example for target query "best CRM software for startups":

{
  "sub_queries": [
    {"type": "comparative", "query": "HubSpot vs Salesforce vs Pipedrive for startups"},
    {"type": "comparative", "query": "free CRM vs paid CRM for early stage startups"},
    {"type": "feature_specific", "query": "CRM with automated lead scoring for small teams"},
    {"type": "feature_specific", "query": "CRM software with built-in email marketing integration"},
    {"type": "use_case", "query": "CRM for managing investor relations at a startup"},
    {"type": "use_case", "query": "using CRM to track product-led growth signups"},
    {"type": "how_to", "query": "how to migrate from spreadsheets to a CRM system"},
    {"type": "how_to", "query": "how to set up a sales pipeline in a CRM for B2B startup"},
    {"type": "trust_signals", "query": "CRM software reviews from YC-backed startup founders"},
    {"type": "trust_signals", "query": "case studies of startups scaling with CRM automation"},
    {"type": "definitional", "query": "what is a CRM and why do startups need one"},
    {"type": "definitional", "query": "CRM vs spreadsheet for customer management"}
  ]
}"""

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "fan_out_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "sub_queries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": SUB_QUERY_TYPES},
                            "query": {"type": "string"},
                        },
                        "required": ["type", "query"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["sub_queries"],
            "additionalProperties": False,
        },
    },
}


class LLMStrategy(ABC):
    @abstractmethod
    async def generate(self, target_query: str) -> FanOutLLMResponse:
        ...


class GuidedDecodingStrategy(LLMStrategy):
    async def generate(self, target_query: str) -> FanOutLLMResponse:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f'Target query: "{target_query}"\n\nGenerate sub-queries for this target query.'},
            ],
            temperature=LLM_TEMPERATURE,
            response_format=RESPONSE_SCHEMA,
        )
        raw = response.choices[0].message.content
        return FanOutLLMResponse.model_validate(json.loads(raw))


class PromptBasedStrategy(LLMStrategy):
    async def generate(self, target_query: str) -> FanOutLLMResponse:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + "\n\nReturn ONLY the JSON object. No markdown, no code blocks, no explanation."},
                {"role": "user", "content": f'Target query: "{target_query}"\n\nGenerate sub-queries for this target query.'},
            ],
            temperature=LLM_TEMPERATURE,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:]).rsplit("```", 1)[0]
        return FanOutLLMResponse.model_validate(json.loads(raw))


DEFAULT_STRATEGY = GuidedDecodingStrategy()


async def generate_sub_queries(
    target_query: str, strategy: LLMStrategy | None = None
) -> FanOutLLMResponse:
    strategy = strategy or DEFAULT_STRATEGY
    last_error = None
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            return await strategy.generate(target_query=target_query)
        except (APIConnectionError, APITimeoutError, APIStatusError, json.JSONDecodeError, ValueError) as e:
            last_error = e
            if attempt < LLM_MAX_RETRIES:
                delay = LLM_BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)

    raise LLMServiceError(
        error_type=type(last_error).__name__,
        detail=str(last_error),
        attempt=LLM_MAX_RETRIES,
    )

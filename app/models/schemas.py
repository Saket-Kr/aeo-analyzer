from typing import Literal

from pydantic import BaseModel, ConfigDict


class AEORequest(BaseModel):
    input_type: Literal["url", "text"]
    input_value: str


class DirectAnswerDetails(BaseModel):
    word_count: int
    threshold: int
    is_declarative: bool
    has_hedge_phrase: bool


class HtagDetails(BaseModel):
    violations: list[str]
    h_tags_found: list[str]


class ReadabilityDetails(BaseModel):
    fk_grade_level: float
    target_range: str
    complex_sentences: list[str]


class CheckResult(BaseModel):
    check_id: str
    name: str
    passed: bool
    score: int
    max_score: int
    details: DirectAnswerDetails | HtagDetails | ReadabilityDetails
    recommendation: str | None


class AEOResponse(BaseModel):
    aeo_score: int
    band: str
    checks: list[CheckResult]


class FanOutRequest(BaseModel):
    target_query: str
    existing_content: str | None = None


class SubQuery(BaseModel):
    type: Literal[
        "comparative",
        "feature_specific",
        "use_case",
        "trust_signals",
        "how_to",
        "definitional",
    ]
    query: str


class FanOutLLMResponse(BaseModel):
    sub_queries: list[SubQuery]


class SubQueryResult(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    type: str
    query: str
    covered: bool | None = None
    similarity_score: float | None = None


class GapSummary(BaseModel):
    covered: int
    total: int
    coverage_percent: int
    covered_types: list[str]
    missing_types: list[str]


class FanOutResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    target_query: str
    model_used: str
    total_sub_queries: int
    sub_queries: list[SubQueryResult]
    gap_summary: GapSummary | None = None


class ErrorDetail(BaseModel):
    error_type: str
    error_message: str
    attempt: int
    model: str



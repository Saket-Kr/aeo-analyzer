import os
from enum import Enum


class ScoreBand(str, Enum):
    OPTIMIZED = "AEO Optimized"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    SIGNIFICANT_GAPS = "Significant Gaps"
    NOT_READY = "Not AEO Ready"


SCORE_BAND_THRESHOLDS = [
    (85, ScoreBand.OPTIMIZED),
    (65, ScoreBand.NEEDS_IMPROVEMENT),
    (40, ScoreBand.SIGNIFICANT_GAPS),
    (0, ScoreBand.NOT_READY),
]

HEDGE_PHRASES = [
    "it depends",
    "may vary",
    "in some cases",
    "this varies",
    "generally speaking",
]

DIRECT_ANSWER_WORD_LIMIT = 60
DIRECT_ANSWER_WORD_UPPER = 90

DIRECT_ANSWER_SCORES = {
    "perfect": 20,
    "partial": 12,
    "over_limit": 8,
    "excessive": 0,
}

FK_GRADE_TARGET_MIN = 7.0
FK_GRADE_TARGET_MAX = 9.0

FK_GRADE_SCORES = [
    (7.0, 9.0, 20),
    (6.0, 10.0, 14),
    (5.0, 11.0, 8),
]
FK_GRADE_DEFAULT_SCORE = 0

COMPLEX_SENTENCE_COUNT = 3

MAX_SCORE_PER_CHECK = 20
TOTAL_MAX_SCORE = 60

SIMILARITY_THRESHOLD = 0.72
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

SUB_QUERY_TYPES = [
    "comparative",
    "feature_specific",
    "use_case",
    "trust_signals",
    "how_to",
    "definitional",
]
MIN_SUB_QUERIES = 10
MAX_SUB_QUERIES = 15
MIN_PER_TYPE = 2

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-235B-A22B-FP8")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_RETRIES = 3
LLM_BASE_DELAY = 1.0
LLM_TIMEOUT = 30.0

URL_FETCH_TIMEOUT = 10.0

BOILERPLATE_TAGS = ["nav", "footer", "header", "aside", "script", "style", "noscript"]

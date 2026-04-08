# AEO Analyzer

A Python FastAPI service that scores content for AI search engine optimization (AEO) and simulates how AI search engines decompose queries into sub-queries for comprehensive answer generation.

## Quick Start

Requires **Python 3.11+**.

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure environment

Copy `.env.example` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_BASE_URL` | For fan-out only | OpenAI-compatible API endpoint (e.g., vLLM server) |
| `LLM_API_KEY` | For fan-out only | Bearer token for the LLM API |
| `LLM_MODEL` | No | Model ID (default: `Qwen/Qwen3-235B-A22B-FP8`) |
| `LLM_TEMPERATURE` | No | Sampling temperature (default: `0.7`) |

The AEO scorer (`/api/aeo/analyze`) works without any env vars — it's pure NLP, no LLM calls. The fan-out engine (`/api/fanout/generate`) requires `LLM_BASE_URL` and `LLM_API_KEY`.

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

API docs available at http://localhost:8000/docs

### 4. Try it

**AEO Content Scorer:**
```bash
curl -X POST http://localhost:8000/api/aeo/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "input_type": "text",
    "input_value": "<h1>What is Python?</h1><p>Python is a high-level programming language designed for readability and simplicity.</p><h2>Features</h2><p>Python supports multiple paradigms including object-oriented and functional programming.</p>"
  }'
```

**Fan-Out Engine (requires LLM env vars):**
```bash
curl -X POST http://localhost:8000/api/fanout/generate \
  -H "Content-Type: application/json" \
  -d '{
    "target_query": "best AI writing tool for SEO",
    "existing_content": "Jasper AI is a writing tool that uses AI to generate SEO-optimized content. It supports keyword clustering and SERP analysis."
  }'
```

The first fan-out request with `existing_content` will download the sentence-transformer embedding model (~80MB). Subsequent requests use the cached model.

### 5. Run tests

```bash
pytest                               # all 45 tests
pytest tests/test_direct_answer.py   # single file
pytest -k "test_name"                # single test
```

Tests do not require env vars or an LLM connection — all LLM calls are mocked.

## Completion Status

| Feature | Status | Notes |
|---------|--------|-------|
| AEO Content Scorer | Complete | All 3 checks with score aggregation |
| Direct Answer Check | Complete | spaCy dep parsing + hedge detection |
| H-tag Hierarchy Check | Complete | DOM-order validation, 3 rule types |
| Readability Check | Complete | textstat FK grade + complex sentence ranking |
| Fan-Out Engine | Complete | Qwen3-235B via vLLM with guided decoding |
| Gap Analysis | Complete | all-MiniLM-L6-v2 cosine similarity |
| Tests | Complete | 45 tests across all checks, parser, and mocked LLM |
| PROMPT_LOG.md | Complete | Both strategies documented with results |

## Architecture Decisions

### Content Parsing

URL fetching uses `httpx` with a 10-second timeout and redirect following. HTML parsing uses BeautifulSoup4. For `input_type: "text"`, we detect whether the input is HTML by checking if BeautifulSoup finds any tags — this avoids requiring the caller to specify the format.

Boilerplate stripping removes `<nav>`, `<footer>`, `<header>`, `<aside>`, `<script>`, `<style>`, and `<noscript>` tags before extracting clean text. When `<main>` or `<article>` tags are present, we extract content from within them to avoid sidebar and chrome content polluting the analysis.

Plain text input works but naturally scores 0 on H-tag hierarchy since headings require HTML structure.

**Production improvement:** `httpx` fetches raw HTML and cannot execute JavaScript. Single-page applications or JS-rendered content will return empty HTML. A production system would use Firecrawl or Playwright for reliable content extraction from any page. For smarter main-content extraction beyond tag removal, Mozilla's Readability algorithm (via `readability-lxml`) would be more robust.

### AEO Check Pipeline

Each check implements a `BaseCheck` abstract class with a single `run(content) -> CheckResult` method. This is the strategy pattern — checks are independently testable and the pipeline is extensible by adding a new subclass and registering it in `ALL_CHECKS`.

The spaCy model (`en_core_web_sm`) is loaded once as a module-level singleton in `app/services/nlp.py` and shared across the parser and checks. This avoids redundant 500ms load times per request.

With 3 checks, a template method pattern with default implementations would add indirection without reducing duplication — each check has different scoring logic, different detail schemas, and different analysis methods. At 8-10+ checks, introducing a `TemplateCheck` with common scoring normalization and recommendation generation would become worthwhile. Similarly, a factory pattern for dynamic check registration per content type would be the right move when check selection needs to vary by request.

### LLM Integration

We use `Qwen/Qwen3-235B-A22B-FP8` hosted on vLLM via an OpenAI-compatible API. The 235B MoE model with 22B active parameters provides strong structured output quality at reasonable inference speed.

The key architectural decision is using **vLLM's guided decoding** via the `response_format` parameter. Instead of prompting the model to return JSON and hoping, we pass a JSON schema that vLLM enforces at the token generation level. The model structurally cannot produce invalid JSON or unexpected fields. This eliminates an entire class of failure modes that plague LLM-based systems.

We implemented two strategies behind a common interface:
- `GuidedDecodingStrategy` — uses `response_format` with a JSON schema (default, production choice)
- `PromptBasedStrategy` — instructs JSON output in the prompt, parses response text

Both were tested. See `PROMPT_LOG.md` for comparison results. Guided decoding is the default because it guarantees structural validity. The prompt-based strategy exists to demonstrate the comparison and as a fallback for LLM providers that don't support guided decoding.

### Prompt Design

The system prompt defines the role ("search query decomposition engine"), all 6 sub-query types with descriptions, output constraints (10-15 queries, minimum 2 per type), and a complete JSON example using a different topic ("best CRM software for startups") so the model generalizes rather than copying.

The user message contains only the target query, keeping the variable input separate from stable instructions.

Temperature is set to 0.7 — high enough for diverse, non-formulaic sub-queries, low enough to avoid incoherent output.

### Embedding Model Choice

`all-MiniLM-L6-v2` over `all-mpnet-base-v2`. The MiniLM model produces 384-dimension vectors and is roughly 5x faster than mpnet (768-dim). For our use case — matching short query strings against individual sentences — the accuracy difference is negligible while the latency improvement is meaningful.

The model is loaded lazily on first use and cached as a singleton. First load downloads ~80MB from HuggingFace; subsequent loads are from local cache (~200ms).

**Production consideration:** For multilingual content or matching longer passages, `all-mpnet-base-v2` would be worth the performance cost. At scale, embeddings would be pre-computed and served via a model server (e.g., Triton Inference Server) rather than loaded per-process.

### Similarity Threshold

We kept the assignment's default of 0.72. For `all-MiniLM-L6-v2`, this falls in the "clearly same topic" range (scores above 0.70 indicate strong semantic overlap; scores above 0.85 indicate near-paraphrases).

In production, this threshold would be calibrated per domain by:
1. Collecting labeled pairs of (sub-query, sentence, human-judged covered/not-covered)
2. Computing similarity scores across the dataset
3. Finding the threshold that maximizes F1 score
4. Potentially varying the threshold by content type (technical content tends to produce higher similarity scores due to narrower vocabulary)

Making the threshold configurable via request parameter or environment variable would let users tune sensitivity without code changes.

### Async vs Sync

AEO checks are CPU-bound (spaCy parsing, textstat computation) — they run sequentially and complete in under 100ms total. No benefit from async here.

The fan-out LLM call is I/O-bound — it uses the async OpenAI SDK natively.

Embedding encoding is CPU-bound — it runs synchronously after the LLM response arrives.

In production, CPU-bound work would use `asyncio.to_thread()` or a process pool to avoid blocking the event loop under concurrent load.

### Error Handling

Both features use custom exception classes (`ContentFetchError`, `LLMServiceError`) caught by FastAPI exception handlers. This keeps route handler code clean and produces consistent error responses.

The fan-out engine's retry logic uses exponential backoff with jitter (3 attempts). Transport failures (timeouts, connection errors, server errors) trigger retries. JSON parsing failures are also retried as a defensive measure, though guided decoding makes them near-impossible.

The 503 error response for LLM failures includes structured detail: `error_type` (exception class name), `error_message`, `attempt` count, and `model` name. This is a minor deviation from the assignment's flat string `detail` field — the structured format is more debuggable and machine-parseable.

### LLM Output Evaluation

Beyond structural JSON validation (handled by guided decoding + Pydantic), the system validates business rules: sub-query count and type distribution. Insufficient results are returned as-is rather than retried — the data is still useful even if incomplete.

Production evaluation would add:
- **Semantic diversity scoring** — pairwise cosine similarity within each type; flag if avg > 0.85 (near-duplicate sub-queries)
- **Relevance scoring** — embedding similarity between target query and each sub-query; flag if < 0.5
- **Automated regression testing** — golden set of (query → expected sub-queries), run periodically to detect model drift
- **Guardrails** — declarative output constraints via frameworks like Guardrails AI or LMQL

## Production Improvements

| Area | Current | Production |
|------|---------|------------|
| URL fetching | httpx (raw HTML) | Firecrawl / Playwright for JS-rendered pages |
| Content extraction | BeautifulSoup heuristic | Mozilla Readability for smarter main content isolation |
| LLM structured output | vLLM guided decoding | Works here; for external APIs, add retry + Pydantic validation fallback |
| LLM output eval | Pydantic + business rules | Semantic diversity, relevance scoring, regression tests |
| Retry / resilience | Exponential backoff | Circuit breaker pattern, fallback to smaller model on repeated failures |
| Embedding model | Loaded per-process | Model server (Triton), pre-computed embeddings |
| Threshold tuning | Fixed 0.72 | Per-domain calibration with labeled data |
| Check pipeline | Fixed 3 checks | Factory pattern for dynamic check registration per content type |
| Caching | None | Cache LLM responses for repeated queries, cache embeddings for repeated content |
| Observability | Structured error responses | Structured logging, latency metrics, LLM token usage tracking |

## API Contract Changes

**503 error detail field:** Changed from a flat string to a structured object containing `error_type`, `error_message`, `attempt`, and `model`. This makes errors machine-parseable and more useful for debugging without breaking the overall response shape.

from sentence_transformers import SentenceTransformer, util

from app.constants import EMBEDDING_MODEL, SIMILARITY_THRESHOLD
from app.models.schemas import GapSummary, SubQuery, SubQueryResult

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def analyze_gaps(
    sentences: list[str], sub_queries: list[SubQuery]
) -> tuple[list[SubQueryResult], GapSummary]:
    model = _get_model()
    query_texts = [sq.query for sq in sub_queries]

    content_embeddings = model.encode(sentences=sentences, convert_to_tensor=True)
    query_embeddings = model.encode(sentences=query_texts, convert_to_tensor=True)

    similarities = util.cos_sim(a=query_embeddings, b=content_embeddings)
    max_scores = similarities.max(dim=1).values

    results = []
    type_coverage: dict[str, bool] = {}

    for i, sq in enumerate(sub_queries):
        sim = round(float(max_scores[i]), 2)
        covered = sim >= SIMILARITY_THRESHOLD
        results.append(SubQueryResult(
            type=sq.type,
            query=sq.query,
            covered=covered,
            similarity_score=sim,
        ))

        if sq.type not in type_coverage:
            type_coverage[sq.type] = False
        if covered:
            type_coverage[sq.type] = True

    covered_types = [t for t, has_any in type_coverage.items() if has_any]
    missing_types = [t for t, has_any in type_coverage.items() if not has_any]
    covered_count = sum(1 for r in results if r.covered)

    summary = GapSummary(
        covered=covered_count,
        total=len(results),
        coverage_percent=round((covered_count / len(results)) * 100) if results else 0,
        covered_types=covered_types,
        missing_types=missing_types,
    )
    return results, summary

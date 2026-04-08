from app.constants import LLM_MODEL
from app.models.schemas import FanOutRequest, FanOutResponse, SubQueryResult
from app.services.content_parser import parse_content
from app.services.gap_analyzer import analyze_gaps
from app.services.llm_client import generate_sub_queries


async def run_fanout(request: FanOutRequest) -> FanOutResponse:
    llm_response = await generate_sub_queries(target_query=request.target_query)

    if request.existing_content:
        content = parse_content(raw=request.existing_content, )
        results, summary = analyze_gaps(sentences=content.sentences, sub_queries=llm_response.sub_queries)
    else:
        results = [
            SubQueryResult(type=sq.type, query=sq.query)
            for sq in llm_response.sub_queries
        ]
        summary = None

    return FanOutResponse(
        target_query=request.target_query,
        model_used=LLM_MODEL,
        total_sub_queries=len(results),
        sub_queries=results,
        gap_summary=summary,
    )

from fastapi import APIRouter

from app.constants import SCORE_BAND_THRESHOLDS, TOTAL_MAX_SCORE
from app.models.schemas import AEORequest, AEOResponse
from app.services.aeo_checks import ALL_CHECKS
from app.services.content_parser import fetch_url, parse_content

router = APIRouter()


def _get_band(score: int) -> str:
    for threshold, band in SCORE_BAND_THRESHOLDS:
        if score >= threshold:
            return band.value
    return SCORE_BAND_THRESHOLDS[-1][1].value


@router.post("/analyze", response_model=AEOResponse)
async def analyze(request: AEORequest):
    if request.input_type == "url":
        raw = await fetch_url(url=request.input_value)
        content = parse_content(raw=raw, is_url_fetched=True)
    else:
        content = parse_content(raw=request.input_value)

    results = [check.run(content) for check in ALL_CHECKS]
    raw_score = sum(r.score for r in results)
    aeo_score = round((raw_score / TOTAL_MAX_SCORE) * 100)

    return AEOResponse(
        aeo_score=aeo_score,
        band=_get_band(aeo_score),
        checks=results,
    )

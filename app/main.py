from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api import aeo, fanout
from app.constants import LLM_MODEL
from app.models.schemas import ErrorDetail
from app.services.content_parser import ContentFetchError
from app.services.llm_client import LLMServiceError

app = FastAPI(title="AEO Analyzer")

app.include_router(aeo.router, prefix="/api/aeo", tags=["aeo"])
app.include_router(fanout.router, prefix="/api/fanout", tags=["fanout"])


@app.exception_handler(ContentFetchError)
async def content_fetch_error_handler(request, exc: ContentFetchError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "url_fetch_failed",
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(LLMServiceError)
async def llm_service_error_handler(request, exc: LLMServiceError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "llm_unavailable",
            "message": "Fan-out generation failed after retries.",
            "detail": ErrorDetail(
                error_type=exc.error_type,
                error_message=exc.detail,
                attempt=exc.attempt,
                model=LLM_MODEL,
            ).model_dump(),
        },
    )


@app.get("/")
async def root():
    return {"message": "Welcome to the AEO Analyzer API"}

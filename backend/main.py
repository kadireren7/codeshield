from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse

from backend.analysis_service import run_path_analysis
from backend.db import init_db
from backend.html_report import render_html_report
from backend.job_runner import run_background_analysis
from backend.jobs import create_job, get_job
from backend.models import (
    AnalyzeAcceptedResponse,
    AsyncJobAcceptedResponse,
    AnalysisJobPollResponse,
    CodeAnalysisRequest,
    ErrorResponse,
    HealthResponse,
    MetaResponse,
    PathAnalysisRequest,
    PathAnalysisResponse,
)
from backend.rules_config import load_rules_config
from backend.sarif_export import path_response_to_sarif


def _error_response(status_code: int, message: str) -> JSONResponse:
    payload = ErrorResponse(error="invalid_request", message=message, details=None)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _validate_path_analysis_request(request: PathAnalysisRequest) -> JSONResponse | None:
    if not Path(request.path).is_absolute() or request.path.startswith("\\\\"):
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            "Path must be an absolute local filesystem path.",
        )
    if request.rules_config_path:
        try:
            load_rules_config(Path(request.rules_config_path))
        except FileNotFoundError:
            return _error_response(
                status.HTTP_400_BAD_REQUEST,
                f"Rules config not found: {request.rules_config_path}",
            )
    target = Path(request.path)
    if not target.exists():
        return _error_response(status.HTTP_404_NOT_FOUND, "Path does not exist.")
    if not target.is_dir():
        return _error_response(status.HTTP_400_BAD_REQUEST, "Path must point to a directory.")
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = app
    init_db()
    yield


app = FastAPI(
    title="CodeShield AI API",
    version="0.1.0",
    description="Experimental API with local rule-based project path analysis.",
    lifespan=lifespan,
)


@app.get("/", tags=["root"])
async def read_root() -> dict[str, str]:
    return {
        "name": "CodeShield AI API",
        "status": "ok",
        "mode": "experimental-mvp",
    }


@app.get(
    "/healthz",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok", service="codeshield-ai", version=app.version)


@app.get(
    "/api/v1/meta",
    response_model=MetaResponse,
    tags=["system"],
    summary="API metadata",
)
async def meta() -> MetaResponse:
    return MetaResponse(
        name="CodeShield AI API",
        version=app.version,
        api_version="v1",
        mode="experimental-mvp",
        capabilities=[
            "request_intake",
            "local_path_analyzer",
            "python_ast_assist",
            "async_path_jobs",
            "sarif_export",
            "html_report",
        ],
        limits={
            "min_code_chars": 10,
            "max_code_chars": 100_000,
            "default_max_files": 300,
            "default_max_file_size_kb": 512,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    _ = request
    response = ErrorResponse(
        error="validation_error",
        message="Request validation failed.",
        details=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response.model_dump(),
    )


@app.post(
    "/api/v1/analyze",
    response_model=AnalyzeAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["analysis"],
    summary="Submit code for analysis intake",
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Validation error",
        }
    },
)
async def analyze_code(request: CodeAnalysisRequest) -> AnalyzeAcceptedResponse:
    _ = request
    return AnalyzeAcceptedResponse(
        request_id=uuid4(),
        status="pending",
        message="Analysis request accepted. Result retrieval is not implemented in this MVP.",
    )


@app.post(
    "/api/v1/analyze/path",
    response_model=PathAnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["analysis"],
    summary="Analyze a local project path using rule-based checks",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid path input"},
        404: {"model": ErrorResponse, "description": "Path not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def analyze_local_path(request: PathAnalysisRequest) -> PathAnalysisResponse | Response:
    # Dedicated endpoint (vs extending POST /analyze) keeps unrelated contracts separate.
    bad = _validate_path_analysis_request(request)
    if bad is not None:
        return bad
    try:
        return run_path_analysis(request)
    except (PermissionError, OSError):
        return _error_response(status.HTTP_400_BAD_REQUEST, "Path could not be scanned.")


@app.post(
    "/api/v1/analyze/path/async",
    response_model=AsyncJobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["analysis"],
    summary="Queue local path analysis (poll GET /api/v1/analysis/{request_id})",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid path input"},
        404: {"model": ErrorResponse, "description": "Path not found"},
    },
)
async def analyze_local_path_async(
    request: PathAnalysisRequest,
    background_tasks: BackgroundTasks,
) -> AsyncJobAcceptedResponse | Response:
    bad = _validate_path_analysis_request(request)
    if bad is not None:
        return bad
    job_id = create_job(request)
    background_tasks.add_task(run_background_analysis, job_id, request)
    return AsyncJobAcceptedResponse(
        request_id=job_id,
        status="pending",
        message="Job accepted. Poll GET /api/v1/analysis/{request_id} until status is completed or failed.",
    )


@app.get(
    "/api/v1/analysis/{request_id}",
    response_model=AnalysisJobPollResponse,
    tags=["analysis"],
    summary="Poll async path analysis job",
)
async def poll_analysis_job(request_id: UUID) -> AnalysisJobPollResponse | Response:
    row = get_job(request_id)
    if row is None:
        return _error_response(status.HTTP_404_NOT_FOUND, "Unknown analysis job id.")
    if row["status"] == "pending":
        return AnalysisJobPollResponse(request_id=request_id, status="pending")
    if row["status"] == "failed":
        return AnalysisJobPollResponse(
            request_id=request_id,
            status="failed",
            error=row["error_message"] or "Job failed.",
        )
    data = json.loads(row["result_json"] or "{}")
    completed = PathAnalysisResponse.model_validate(data)
    return AnalysisJobPollResponse(
        request_id=request_id,
        status="completed",
        summary=completed.summary,
        findings=completed.findings,
        limitations=completed.limitations,
    )


@app.get(
    "/api/v1/analysis/{request_id}/sarif",
    tags=["analysis"],
    summary="SARIF 2.1.0 for completed async jobs",
    response_model=None,
)
async def analysis_job_sarif(request_id: UUID) -> JSONResponse | Response:
    row = get_job(request_id)
    if row is None:
        return _error_response(status.HTTP_404_NOT_FOUND, "Unknown analysis job id.")
    if row["status"] != "completed" or not row["result_json"]:
        return _error_response(
            status.HTTP_404_NOT_FOUND,
            "SARIF is only available for completed async analysis jobs.",
        )
    completed = PathAnalysisResponse.model_validate(json.loads(row["result_json"]))
    return JSONResponse(content=path_response_to_sarif(completed))


@app.get(
    "/api/v1/analysis/{request_id}/report.html",
    tags=["analysis"],
    summary="HTML report for completed async jobs",
    response_class=HTMLResponse,
    response_model=None,
)
async def analysis_job_html(request_id: UUID) -> HTMLResponse | Response:
    row = get_job(request_id)
    if row is None:
        return _error_response(status.HTTP_404_NOT_FOUND, "Unknown analysis job id.")
    if row["status"] != "completed" or not row["result_json"]:
        return _error_response(
            status.HTTP_404_NOT_FOUND,
            "HTML report is only available for completed async analysis jobs.",
        )
    completed = PathAnalysisResponse.model_validate(json.loads(row["result_json"]))
    return HTMLResponse(content=render_html_report(completed))

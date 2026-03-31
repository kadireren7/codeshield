from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Response

from backend.analyzer import analyze_codebase
from backend.models import (
    AnalyzeAcceptedResponse,
    CodeAnalysisRequest,
    ErrorResponse,
    HealthResponse,
    MetaResponse,
    PathAnalysisRequest,
    PathAnalysisResponse,
)
from backend.scanner import scan_source_files

LOCAL_ANALYZER_LIMITATIONS = [
    "This is a heuristic rule-based analysis.",
    "Results may include false positives.",
    "The analyzer does not execute code or build a full AST-based semantic model.",
]


def _is_local_absolute_path(path_value: str) -> bool:
    if path_value.startswith("\\\\"):
        return False
    path = Path(path_value)
    return path.is_absolute()


def _error_response(status_code: int, message: str) -> JSONResponse:
    payload = ErrorResponse(error="invalid_request", message=message, details=None)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


app = FastAPI(
    title="CodeShield AI API",
    version="0.1.0",
    description="Experimental API with local rule-based project path analysis.",
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
        capabilities=["request_intake", "local_path_analyzer"],
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
    # MVP behavior: request intake only. No persisted result polling endpoint yet.
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
    # Kept as a dedicated endpoint to preserve the existing intake contract and avoid
    # overloading one route with two unrelated request shapes.
    if not _is_local_absolute_path(request.path):
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            "Path must be an absolute local filesystem path.",
        )

    target = Path(request.path)
    if not target.exists():
        return _error_response(status.HTTP_404_NOT_FOUND, "Path does not exist.")
    if not target.is_dir():
        return _error_response(status.HTTP_400_BAD_REQUEST, "Path must point to a directory.")

    try:
        source_files = scan_source_files(
            root=target,
            max_files=request.max_files,
            max_file_size_kb=request.max_file_size_kb,
        )
    except PermissionError:
        return _error_response(status.HTTP_400_BAD_REQUEST, "Path is not readable.")
    except OSError:
        return _error_response(status.HTTP_400_BAD_REQUEST, "Path could not be scanned.")

    result = analyze_codebase(source_files)
    return PathAnalysisResponse(
        request_id=uuid4(),
        status="completed",
        summary={
            "files_scanned": len(source_files),
            "issues_found": len(result.findings),
            "risk_score": result.risk_score,
        },
        findings=result.findings,
        limitations=LOCAL_ANALYZER_LIMITATIONS,
    )

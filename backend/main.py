from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


class SupportedLanguage(str, Enum):
    python = "python"
    javascript = "javascript"
    typescript = "typescript"
    go = "go"
    rust = "rust"
    java = "java"
    cpp = "cpp"
    csharp = "csharp"


class CodeAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        min_length=10,
        max_length=100_000,
        description="Code to analyze.",
        examples=["def add(a, b):\n    return a + b"],
    )
    language: SupportedLanguage = Field(
        default=SupportedLanguage.python,
        description="Language of submitted code.",
        examples=["python"],
    )


class AnalyzeAcceptedResponse(BaseModel):
    request_id: UUID
    status: Literal["pending"]
    message: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: list[dict] | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class MetaResponse(BaseModel):
    name: str
    version: str
    api_version: Literal["v1"]
    mode: Literal["experimental-mvp"]
    capabilities: list[str]
    limits: dict[str, int]


app = FastAPI(
    title="CodeShield AI API",
    version="0.1.0",
    description="Experimental API for asynchronous code analysis intake.",
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
        capabilities=["request_intake"],
        limits={"min_code_chars": 10, "max_code_chars": 100_000},
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

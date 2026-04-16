from __future__ import annotations

from enum import Enum
from typing import Literal
from uuid import UUID

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


class PathAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1, description="Absolute local project directory path.")
    max_files: int = Field(default=300, ge=1, le=2_000)
    max_file_size_kb: int = Field(default=512, ge=32, le=5_120)
    rules_config_path: str | None = Field(
        default=None,
        description="Optional absolute path to a YAML rules file overriding defaults.",
    )


class Finding(BaseModel):
    type: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    file: str
    line: int
    message: str
    impact: str
    suggestion: str


class AnalysisSummary(BaseModel):
    files_scanned: int
    issues_found: int
    risk_score: int


class PathAnalysisResponse(BaseModel):
    request_id: UUID
    status: Literal["completed"]
    summary: AnalysisSummary
    findings: list[Finding]
    limitations: list[str]


class AsyncJobAcceptedResponse(BaseModel):
    request_id: UUID
    status: Literal["pending"]
    message: str


class AnalysisJobPollResponse(BaseModel):
    request_id: UUID
    status: Literal["pending", "completed", "failed"]
    summary: AnalysisSummary | None = None
    findings: list[Finding] | None = None
    limitations: list[str] | None = None
    error: str | None = None

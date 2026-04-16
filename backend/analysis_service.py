from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from backend.analyzer import analyze_codebase
from backend.models import PathAnalysisRequest, PathAnalysisResponse
from backend.rules_config import load_rules_config
from backend.scanner import scan_source_files

LOCAL_ANALYZER_LIMITATIONS = [
    "This is a heuristic rule-based analysis; Python also uses AST-assisted checks where syntax is valid.",
    "Results may include false positives.",
    "The analyzer does not execute code or build a full semantic model for non-Python languages.",
]


def is_local_absolute_path(path_value: str) -> bool:
    if path_value.startswith("\\\\"):
        return False
    return Path(path_value).is_absolute()


def run_path_analysis(
    request: PathAnalysisRequest,
    *,
    request_id: UUID | None = None,
) -> PathAnalysisResponse:
    """Scan and analyze a validated local directory; raises FileNotFoundError for missing rules file."""
    rules_path = Path(request.rules_config_path) if request.rules_config_path else None
    rules_cfg = load_rules_config(rules_path)

    target = Path(request.path)
    source_files = scan_source_files(
        root=target,
        max_files=request.max_files,
        max_file_size_kb=request.max_file_size_kb,
    )
    result = analyze_codebase(source_files, rules_cfg)
    rid = request_id or uuid4()
    return PathAnalysisResponse(
        request_id=rid,
        status="completed",
        summary={
            "files_scanned": len(source_files),
            "issues_found": len(result.findings),
            "risk_score": result.risk_score,
        },
        findings=result.findings,
        limitations=LOCAL_ANALYZER_LIMITATIONS,
    )

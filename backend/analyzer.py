from __future__ import annotations

from dataclasses import dataclass

from backend.heuristic_analyzer import analyze_file_heuristic
from backend.models import Finding
from backend.python_ast_analyzer import analyze_python_ast
from backend.rules_config import apply_rules_to_findings, load_rules_config
from backend.scanner import SourceFile


SEVERITY_POINTS = {"HIGH": 20, "MEDIUM": 10, "LOW": 4}


@dataclass(slots=True)
class AnalysisResult:
    findings: list[Finding]
    risk_score: int


def _dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str, int]] = set()
    out: list[Finding] = []
    for finding in findings:
        key = (finding.file, finding.type, finding.line)
        if key in seen:
            continue
        seen.add(key)
        out.append(finding)
    return out


def analyze_codebase(
    files: list[SourceFile],
    rules_config: dict | None = None,
) -> AnalysisResult:
    """
    Python files: AST-assisted checks plus line heuristics (deduplicated).
    Other languages: line heuristics only.
    """
    cfg = rules_config if rules_config is not None else load_rules_config(None)
    findings: list[Finding] = []
    for source_file in files:
        lines = source_file.content.splitlines()
        if source_file.relative_path.lower().endswith(".py"):
            ast_findings = analyze_python_ast(source_file.relative_path, source_file.content)
            heur_findings = analyze_file_heuristic(source_file.relative_path, lines)
            findings.extend(_dedupe_findings(ast_findings + heur_findings))
        else:
            findings.extend(analyze_file_heuristic(source_file.relative_path, lines))

    findings = apply_rules_to_findings(findings, cfg)
    return AnalysisResult(
        findings=findings,
        risk_score=_compute_risk_score(findings, len(files)),
    )


def _compute_risk_score(findings: list[Finding], files_scanned: int) -> int:
    # Heuristic score only: this helps prioritize review, not measure true production risk.
    raw_score = sum(SEVERITY_POINTS[finding.severity] for finding in findings)
    if files_scanned < 5:
        raw_score = int(raw_score * 0.7)
    elif files_scanned < 10:
        raw_score = int(raw_score * 0.85)
    return min(raw_score, 100)

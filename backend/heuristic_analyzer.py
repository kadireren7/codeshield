from __future__ import annotations

import re

from backend.models import Finding


LOOP_PATTERN = re.compile(r"^\s*(for|while)\b")
NESTED_LOOP_PATTERN = re.compile(r"^\s*for\b")
SLEEP_PATTERN = re.compile(r"\b(?:time\.)?sleep\s*\(")
BROAD_EXCEPT_PATTERN = re.compile(r"^\s*except\s*:\s*$")
EXCEPTION_PASS_PATTERN = re.compile(r"^\s*except\s+Exception\s*:\s*pass\s*$")
REQUEST_CALL_PATTERN = re.compile(r"\brequests\.(get|post|put|delete|patch)\s*\(")
TIMEOUT_PATTERN = re.compile(r"\btimeout\s*=")
FETCH_PATTERN = re.compile(r"\bfetch\s*\(")
AXIOS_PATTERN = re.compile(r"\baxios\s*\(")

DB_HINTS = ("db.", "query", "session.", "Model.objects", "find(", "execute(")


def analyze_file_heuristic(file_path: str, lines: list[str]) -> list[Finding]:
    """Line-based heuristics for all supported languages."""
    findings: list[Finding] = []
    findings.extend(_detect_db_calls_inside_loops(file_path, lines))
    findings.extend(_detect_blocking_calls(file_path, lines))
    findings.extend(_detect_nested_loops(file_path, lines))
    findings.extend(_detect_unbounded_accumulation(file_path, lines))
    findings.extend(_detect_maintainability_risk(file_path, lines))
    findings.extend(_detect_broad_exception_swallowing(file_path, lines))
    findings.extend(_detect_missing_timeouts(file_path, lines))
    return findings


def _detect_db_calls_inside_loops(file_path: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for idx, line in enumerate(lines):
        if not LOOP_PATTERN.search(line):
            continue
        window = "\n".join(lines[idx : min(len(lines), idx + 10)])
        if any(hint in window for hint in DB_HINTS):
            findings.append(
                Finding(
                    type="Potential N+1 Query",
                    severity="HIGH",
                    file=file_path,
                    line=idx + 1,
                    message="Database-like call appears inside a loop.",
                    impact="This may increase latency significantly as data volume grows.",
                    suggestion="Batch queries, prefetch related data, or move data access outside the loop.",
                )
            )
    return findings


def _detect_blocking_calls(file_path: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for idx, line in enumerate(lines):
        if not SLEEP_PATTERN.search(line):
            continue
        severity = (
            "HIGH" if "async def " in "\n".join(lines[max(0, idx - 8) : idx + 1]) else "MEDIUM"
        )
        findings.append(
            Finding(
                type="Blocking Call",
                severity=severity,
                file=file_path,
                line=idx + 1,
                message="Blocking sleep/wait detected.",
                impact="Blocking waits can reduce throughput and delay concurrent requests.",
                suggestion="Use non-blocking alternatives (e.g., asyncio.sleep) in async flows.",
            )
        )
    return findings


def _detect_nested_loops(file_path: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    loop_stack: list[int] = []
    for idx, line in enumerate(lines):
        if not NESTED_LOOP_PATTERN.search(line):
            continue
        indent = len(line) - len(line.lstrip(" "))
        loop_stack = [level for level in loop_stack if level < indent]
        if loop_stack:
            findings.append(
                Finding(
                    type="Potential Performance Bottleneck",
                    severity="MEDIUM",
                    file=file_path,
                    line=idx + 1,
                    message="Nested loop detected.",
                    impact="Nested iteration can scale poorly with larger inputs.",
                    suggestion="Rework the algorithm, indexing, or batching to reduce nested iteration.",
                )
            )
        loop_stack.append(indent)
    return findings


def _detect_unbounded_accumulation(file_path: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    init_pattern = re.compile(r"^\s*\w+\s*=\s*\[\]\s*$")
    for idx, line in enumerate(lines):
        if not init_pattern.search(line):
            continue
        var_name = line.split("=")[0].strip()
        for lookahead in range(idx + 1, min(len(lines), idx + 40)):
            candidate = lines[lookahead]
            if LOOP_PATTERN.search(candidate):
                window = "\n".join(lines[lookahead : min(len(lines), lookahead + 20)])
                if f"{var_name}.append(" in window:
                    findings.append(
                        Finding(
                            type="Potential Memory Growth",
                            severity="MEDIUM",
                            file=file_path,
                            line=lookahead + 1,
                            message=f"List '{var_name}' accumulates items inside a loop.",
                            impact="Unbounded growth can increase memory usage and GC pressure.",
                            suggestion="Stream/process incrementally or enforce limits on collected items.",
                        )
                    )
                    break
    return findings


def _detect_maintainability_risk(file_path: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    if len(lines) > 500:
        findings.append(
            Finding(
                type="Maintainability Risk",
                severity="MEDIUM",
                file=file_path,
                line=1,
                message="Large file size detected (>500 lines).",
                impact="Large files are harder to review, test, and change safely.",
                suggestion="Split the file by responsibility into smaller modules.",
            )
        )

    conditional_count = sum(1 for line in lines if re.search(r"^\s*(if|elif|match)\b", line))
    if conditional_count > 80:
        findings.append(
            Finding(
                type="Maintainability Risk",
                severity="LOW",
                file=file_path,
                line=1,
                message="High conditional complexity detected.",
                impact="Heavy branching can increase bug risk and reduce readability.",
                suggestion="Extract decision logic into focused helpers or strategy objects.",
            )
        )
    return findings


def _detect_broad_exception_swallowing(file_path: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for idx, line in enumerate(lines):
        if BROAD_EXCEPT_PATTERN.search(line) or EXCEPTION_PASS_PATTERN.search(line):
            findings.append(
                Finding(
                    type="Silent Failure Risk",
                    severity="MEDIUM",
                    file=file_path,
                    line=idx + 1,
                    message="Broad exception handling may hide real failures.",
                    impact="Errors can be swallowed, making incidents hard to detect and debug.",
                    suggestion="Catch specific exceptions and log/handle them explicitly.",
                )
            )
    return findings


def _detect_missing_timeouts(file_path: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for idx, line in enumerate(lines):
        if (
            REQUEST_CALL_PATTERN.search(line)
            or FETCH_PATTERN.search(line)
            or AXIOS_PATTERN.search(line)
        ):
            window = "\n".join(lines[idx : min(len(lines), idx + 4)])
            if not TIMEOUT_PATTERN.search(window):
                findings.append(
                    Finding(
                        type="Missing Timeout",
                        severity="MEDIUM",
                        file=file_path,
                        line=idx + 1,
                        message="External call without an obvious timeout.",
                        impact="Requests without timeouts can hang and consume resources.",
                        suggestion="Set explicit timeout values for all outbound network calls.",
                    )
                )
    return findings

from __future__ import annotations

import ast
from typing import Any

from backend.models import Finding


def analyze_python_ast(file_path: str, source: str) -> list[Finding]:
    """
    Structural checks for Python using the AST.
    Falls back to empty list if syntax is invalid (callers may use heuristics).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    visitor = _PythonAstVisitor(file_path, source)
    visitor.visit(tree)
    return visitor.findings


class _PythonAstVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source: str) -> None:
        self.file_path = file_path
        self.source = source
        self.findings: list[Finding] = []
        self._loop_depth = 0
        self._async_function_depth = 0

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self._async_function_depth += 1
        self.generic_visit(node)
        self._async_function_depth -= 1
        return node

    def visit_For(self, node: ast.For) -> Any:
        self._visit_loop(node)

    def visit_While(self, node: ast.While) -> Any:
        self._visit_loop(node)

    def _visit_loop(self, node: ast.For | ast.While) -> Any:
        outer = self._loop_depth
        if outer >= 1 and node.lineno is not None:
            self.findings.append(
                Finding(
                    type="Potential Performance Bottleneck",
                    severity="MEDIUM",
                    file=self.file_path,
                    line=node.lineno,
                    message="Nested loop detected (AST).",
                    impact="Nested iteration can scale poorly with larger inputs.",
                    suggestion="Rework the algorithm, indexing, or batching to reduce nested iteration.",
                )
            )
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth = outer
        return node

    def visit_Call(self, node: ast.Call) -> Any:
        if self._loop_depth > 0 and self._call_looks_like_db(node):
            ln = node.lineno or 1
            self.findings.append(
                Finding(
                    type="Potential N+1 Query",
                    severity="HIGH",
                    file=self.file_path,
                    line=ln,
                    message="Database-like call appears inside a loop (AST).",
                    impact="This may increase latency significantly as data volume grows.",
                    suggestion="Batch queries, prefetch related data, or move data access outside the loop.",
                )
            )
        if isinstance(node.func, ast.Attribute) and node.func.attr == "sleep":
            mod = node.func.value
            if isinstance(mod, ast.Name) and mod.id == "asyncio":
                pass  # asyncio.sleep is non-blocking; do not flag as blocking sleep
            elif isinstance(mod, ast.Name) and mod.id == "time":
                ln = node.lineno or 1
                sev = "HIGH" if self._async_function_depth > 0 else "MEDIUM"
                self.findings.append(
                    Finding(
                        type="Blocking Call",
                        severity=sev,
                        file=self.file_path,
                        line=ln,
                        message="time.sleep call detected (AST).",
                        impact="Blocking waits can reduce throughput and delay concurrent requests.",
                        suggestion="Use non-blocking alternatives (e.g., asyncio.sleep) in async flows.",
                    )
                )
        self.generic_visit(node)
        return node

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> Any:
        if node.type is None and node.lineno is not None:
            self.findings.append(
                Finding(
                    type="Silent Failure Risk",
                    severity="MEDIUM",
                    file=self.file_path,
                    line=node.lineno,
                    message="Bare except catches all exceptions (AST).",
                    impact="Errors can be swallowed, making incidents hard to detect and debug.",
                    suggestion="Catch specific exceptions and log/handle them explicitly.",
                )
            )
        elif (
            node.type is not None
            and isinstance(node.type, ast.Name)
            and node.type.id == "Exception"
        ):
            if self._body_is_only_pass(node.body) and node.lineno is not None:
                self.findings.append(
                    Finding(
                        type="Silent Failure Risk",
                        severity="MEDIUM",
                        file=self.file_path,
                        line=node.lineno,
                        message="except Exception with only pass (AST).",
                        impact="Errors can be swallowed, making incidents hard to detect and debug.",
                        suggestion="Catch specific exceptions and log/handle them explicitly.",
                    )
                )
        self.generic_visit(node)
        return node

    @staticmethod
    def _body_is_only_pass(body: list[ast.stmt]) -> bool:
        if len(body) != 1:
            return False
        return isinstance(body[0], ast.Pass)

    @staticmethod
    def _call_looks_like_db(node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Attribute):
            name = func.attr
            if name in {"query", "execute", "fetchone", "fetchall", "objects"}:
                return True
            if name == "query" and isinstance(func.value, ast.Name):
                return func.value.id in {"db", "session", "cursor"}
        if isinstance(func, ast.Attribute) and func.attr == "objects":
            return True
        if isinstance(func, ast.Name) and func.id in {"execute"}:
            return True
        return False

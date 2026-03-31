from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"}
IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".turbo",
    "coverage",
    "__pycache__",
    ".idea",
    ".vscode",
    "vendor",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
}


@dataclass(slots=True)
class SourceFile:
    relative_path: str
    content: str


def scan_source_files(root: Path, max_files: int, max_file_size_kb: int) -> list[SourceFile]:
    """Recursively scan supported source files under a local project root."""
    results: list[SourceFile] = []
    max_size_bytes = max_file_size_kb * 1024

    for directory, subdirs, files in os.walk(root, topdown=True):
        current_dir = Path(directory)
        subdirs[:] = [
            subdir
            for subdir in subdirs
            if subdir not in IGNORED_DIRECTORIES and not subdir.startswith(".")
        ]

        for file_name in files:
            if len(results) >= max_files:
                return results

            file_path = current_dir / file_name
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if file_path.name.startswith("."):
                continue

            try:
                size = file_path.stat().st_size
            except OSError:
                continue
            if size > max_size_bytes:
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            relative_path = str(file_path.relative_to(root)).replace("\\", "/")
            results.append(SourceFile(relative_path=relative_path, content=content))

    return results

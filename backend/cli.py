from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.analysis_service import is_local_absolute_path, run_path_analysis
from backend.html_report import render_html_report
from backend.models import PathAnalysisRequest
from backend.sarif_export import path_response_to_sarif


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codeshield",
        description="Local rule-based codebase scanner (same engine as the FastAPI app).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Analyze a local project directory")
    scan.add_argument("path", type=str, help="Absolute path to project root")
    scan.add_argument("--max-files", type=int, default=300)
    scan.add_argument("--max-file-size-kb", type=int, default=512)
    scan.add_argument("--rules", type=str, default=None, help="Optional YAML rules file path")
    scan.add_argument("--json", action="store_true", help="Print JSON report to stdout")
    scan.add_argument("--sarif", metavar="FILE", help="Write SARIF 2.1.0 JSON to file")
    scan.add_argument("--html", metavar="FILE", help="Write HTML report to file")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command != "scan":
        parser.print_help()
        return 2

    req = PathAnalysisRequest(
        path=args.path,
        max_files=args.max_files,
        max_file_size_kb=args.max_file_size_kb,
        rules_config_path=args.rules,
    )
    if not is_local_absolute_path(req.path):
        print("Error: path must be an absolute local filesystem path.", file=sys.stderr)
        return 1
    target = Path(req.path)
    if not target.exists():
        print("Error: path does not exist.", file=sys.stderr)
        return 1
    if not target.is_dir():
        print("Error: path must be a directory.", file=sys.stderr)
        return 1
    try:
        result = run_path_analysis(req)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (PermissionError, OSError) as exc:
        print(f"Error: could not scan path: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    if args.sarif:
        Path(args.sarif).write_text(
            json.dumps(path_response_to_sarif(result), indent=2),
            encoding="utf-8",
        )
    if args.html:
        Path(args.html).write_text(render_html_report(result), encoding="utf-8")

    if not args.json and not args.sarif and not args.html:
        print(json.dumps(result.model_dump(mode="json"), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

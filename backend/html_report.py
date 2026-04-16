from __future__ import annotations

import html

from backend.models import PathAnalysisResponse


def render_html_report(response: PathAnalysisResponse) -> str:
    """Single-page HTML summary for local review."""
    rows = []
    for finding in response.findings:
        rows.append(
            "<tr>"
            f"<td>{html.escape(finding.type)}</td>"
            f"<td>{html.escape(finding.severity)}</td>"
            f"<td><code>{html.escape(finding.file)}</code></td>"
            f"<td>{finding.line}</td>"
            f"<td>{html.escape(finding.message)}</td>"
            "</tr>"
        )
    body_rows = "\n".join(rows) if rows else "<tr><td colspan='5'>No findings.</td></tr>"
    summary = response.summary
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>CodeShield report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1.5rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; vertical-align: top; }}
    th {{ background: #f4f4f4; text-align: left; }}
    code {{ font-size: 0.9em; }}
  </style>
</head>
<body>
  <h1>CodeShield local analysis</h1>
  <p>Request <code>{html.escape(str(response.request_id))}</code> — status {html.escape(response.status)}</p>
  <p>Files scanned: {summary.files_scanned} · Issues: {summary.issues_found} · Risk score: {summary.risk_score}</p>
  <h2>Findings</h2>
  <table>
    <thead><tr><th>Type</th><th>Severity</th><th>File</th><th>Line</th><th>Message</th></tr></thead>
    <tbody>
    {body_rows}
    </tbody>
  </table>
  <h2>Limitations</h2>
  <ul>
    {"".join(f"<li>{html.escape(item)}</li>" for item in response.limitations)}
  </ul>
</body>
</html>
"""

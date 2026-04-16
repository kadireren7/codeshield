from __future__ import annotations

from typing import Any

from backend.models import PathAnalysisResponse

_SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"


def _severity_to_level(severity: str) -> str:
    if severity == "HIGH":
        return "error"
    if severity == "MEDIUM":
        return "warning"
    return "note"


def path_response_to_sarif(response: PathAnalysisResponse) -> dict[str, Any]:
    """Minimal SARIF 2.1.0 document for CI integration."""
    results: list[dict[str, Any]] = []
    for finding in response.findings:
        results.append(
            {
                "ruleId": finding.type.replace(" ", "_"),
                "level": _severity_to_level(finding.severity),
                "message": {"text": finding.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.file},
                            "region": {"startLine": finding.line},
                        }
                    }
                ],
            }
        )
    return {
        "$schema": _SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "CodeShield",
                        "informationUri": "https://github.com/",
                        "rules": [],
                    }
                },
                "results": results,
            }
        ],
    }

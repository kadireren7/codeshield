from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml

from backend.models import Finding

Severity = Literal["HIGH", "MEDIUM", "LOW"]

# Finding.type -> key in default_rules.yaml
FINDING_TYPE_TO_RULE: dict[str, str] = {
    "Potential N+1 Query": "potential_n_plus_one",
    "Blocking Call": "blocking_call",
    "Potential Performance Bottleneck": "performance_bottleneck",
    "Potential Memory Growth": "memory_growth",
    "Maintainability Risk": "maintainability_risk",
    "Silent Failure Risk": "silent_failure_risk",
    "Missing Timeout": "missing_timeout",
}


def _default_rule_entry() -> dict[str, Any]:
    return {"enabled": True}


def load_rules_config(path: Path | None) -> dict[str, Any]:
    """Load YAML rule config; merge over packaged defaults."""
    base = Path(__file__).resolve().parent / "config" / "default_rules.yaml"
    with base.open(encoding="utf-8") as f:
        merged: dict[str, Any] = yaml.safe_load(f) or {}

    if path is None:
        return merged

    user_path = Path(path)
    if not user_path.is_file():
        raise FileNotFoundError(f"Rules config not found: {user_path}")
    with user_path.open(encoding="utf-8") as f:
        user = yaml.safe_load(f) or {}
    user_rules = user.get("rules") or {}
    merged_rules = dict(merged.get("rules") or {})
    for key, value in user_rules.items():
        if isinstance(value, dict):
            merged_rules[key] = {**merged_rules.get(key, {}), **value}
        else:
            merged_rules[key] = value
    merged["rules"] = merged_rules
    return merged


def apply_rules_to_findings(
    findings: list[Finding], config: dict[str, Any]
) -> list[Finding]:
    """Drop disabled rules and apply optional severity overrides."""
    rules_map: dict[str, Any] = config.get("rules") or {}
    out: list[Finding] = []
    for finding in findings:
        rule_key = FINDING_TYPE_TO_RULE.get(finding.type)
        if rule_key is None:
            out.append(finding)
            continue
        entry = {**_default_rule_entry(), **(rules_map.get(rule_key) or {})}
        if not entry.get("enabled", True):
            continue
        sev = entry.get("severity")
        if sev in ("HIGH", "MEDIUM", "LOW"):
            out.append(
                finding.model_copy(update={"severity": sev})  # type: ignore[arg-type]
            )
        else:
            out.append(finding)
    return out

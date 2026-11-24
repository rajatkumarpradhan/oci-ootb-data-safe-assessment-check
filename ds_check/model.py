"""Data model and report loading for the Data Safe assessment gate."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

RISK_ORDER = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "ADVISORY")


class ReportError(ValueError):
    """Raised when an assessment report file is malformed."""


@dataclass(frozen=True)
class Finding:
    id: str
    title: str
    risk: str = "MEDIUM"
    status: str = "OPEN"
    note: str = ""

    def is_open(self) -> bool:
        return self.status.upper() == "OPEN"


@dataclass(frozen=True)
class Report:
    target: str
    assessment_time: datetime
    findings: tuple = ()

    def open_findings(self):
        return [f for f in self.findings if f.is_open()]

    def age_days(self, now: datetime) -> float:
        return (now - self.assessment_time).total_seconds() / 86400.0


def _parse_time(raw: str) -> datetime:
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReportError(f"unparseable assessment_time: {raw!r}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def load_report(path: str) -> Report:
    """Load a synthetic Data Safe assessment report. Raises ReportError."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportError(f"cannot read report: {exc}") from exc
    if not isinstance(data, dict) or not data.get("target"):
        raise ReportError("report must be an object with a 'target'")
    if not data.get("assessment_time"):
        raise ReportError("report is missing 'assessment_time'")
    when = _parse_time(str(data["assessment_time"]))
    findings = []
    for i, raw in enumerate(data.get("findings", [])):
        if not isinstance(raw, dict) or not raw.get("id") or not raw.get("title"):
            raise ReportError(f"findings[{i}] needs an id and a title")
        risk = str(raw.get("risk", "MEDIUM")).upper()
        if risk not in RISK_ORDER:
            raise ReportError(f"findings[{i}] has unknown risk {risk!r}")
        findings.append(Finding(
            id=str(raw["id"]),
            title=str(raw["title"]),
            risk=risk,
            status=str(raw.get("status", "OPEN")),
            note=str(raw.get("note", "")),
        ))
    return Report(target=str(data["target"]), assessment_time=when,
                  findings=tuple(findings))

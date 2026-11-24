"""Gate rules over a Data Safe assessment report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

STALE_DAYS = 30


@dataclass(frozen=True)
class GateFinding:
    rule: str
    severity: str
    detail: str


def rule_stale_assessment(report: Report, now: datetime):
    age = report.age_days(now)
    if age > STALE_DAYS:
        return [GateFinding("DS001", "HIGH",
            f"latest assessment for {report.target} is {int(age)} days old "
            f"(older than {STALE_DAYS}); schedule a fresh Data Safe assessment")]
    return []


def rule_open_critical(report: Report, now: datetime):
    crits = [f for f in report.open_findings() if f.risk == "CRITICAL"]
    if crits:
        ids = ", ".join(f.id for f in crits)
        return [GateFinding("DS002", "HIGH",
            f"{len(crits)} CRITICAL finding(s) open on {report.target}: {ids}")]
    return []


def rule_open_high(report: Report, now: datetime):
    highs = [f for f in report.open_findings() if f.risk == "HIGH"]
    if highs:
        ids = ", ".join(f.id for f in highs)
        return [GateFinding("DS003", "HIGH",
            f"{len(highs)} HIGH finding(s) open on {report.target}: {ids}")]
    return []


def rule_open_medium(report: Report, now: datetime):
    meds = [f for f in report.open_findings() if f.risk == "MEDIUM"]
    if meds:
        return [GateFinding("DS004", "MEDIUM",
            f"{len(meds)} MEDIUM finding(s) open on {report.target}")]
    return []


def rule_open_low(report: Report, now: datetime):
    lows = [f for f in report.open_findings() if f.risk in ("LOW", "ADVISORY")]
    if lows:
        return [GateFinding("DS005", "LOW",
            f"{len(lows)} LOW/ADVISORY finding(s) open on {report.target}")]
    return []


def rule_deferred_without_note(report: Report, now: datetime):
    out = []
    bad = [f for f in report.findings
           if f.status.upper() == "DEFERRED" and not f.note.strip()]
    if bad:
        ids = ", ".join(f.id for f in bad)
        out.append(GateFinding("DS006", "LOW",
            f"{len(bad)} deferred finding(s) without a justification note: {ids}"))
    return out


ALL_RULES = (
    rule_stale_assessment,
    rule_open_critical,
    rule_open_high,
    rule_open_medium,
    rule_open_low,
    rule_deferred_without_note,
)


def run_all(report: Report, now: datetime):
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(report, now))
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    findings.sort(key=lambda f: (order.get(f.severity, 3), f.rule))
    return findings


def exit_code(findings) -> int:
    if any(f.severity == "HIGH" for f in findings):
        return 2
    return 1 if findings else 0

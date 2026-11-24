"""Command line entry point: gate a synthetic Data Safe assessment report."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from .model import ReportError, load_report
from .rules import exit_code, run_all


def _now(value: str | None) -> datetime:
    if value:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="ds-assessment-check",
        description="Offline release gate over an OCI Data Safe security "
                    "assessment report (synthetic export).",
    )
    parser.add_argument("report", help="path to a JSON assessment report")
    parser.add_argument("--now", help="reference time (ISO 8601) for the "
                        "staleness check; defaults to current UTC time")
    args = parser.parse_args(argv)
    try:
        report = load_report(args.report)
    except ReportError as exc:
        print(f"report error: {exc}", file=sys.stderr)
        return 3
    now = _now(args.now)
    findings = run_all(report, now)
    opened = report.open_findings()
    print(f"Data Safe assessment gate - target {report.target}, "
          f"{len(report.findings)} finding(s) ({len(opened)} open), "
          f"assessed {int(report.age_days(now))} day(s) ago")
    for f in findings:
        print(f"[{f.severity:6}] {f.rule} {f.detail}")
    code = exit_code(findings)
    if code == 0:
        print("RESULT: gate passed, no blocking findings  (exit code 0)")
    else:
        high = sum(1 for f in findings if f.severity == "HIGH")
        print(f"RESULT: gate failed - {high} HIGH / {len(findings)} total "
              f"gate finding(s)  (exit code {code})")
    return code


if __name__ == "__main__":
    sys.exit(main())

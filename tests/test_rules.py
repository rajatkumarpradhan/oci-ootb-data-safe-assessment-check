import unittest
from datetime import datetime, timezone

from ds_check.model import Finding, Report
from ds_check.rules import (
    exit_code,
    rule_deferred_without_note,
    rule_open_critical,
    rule_open_high,
    rule_open_medium,
    rule_stale_assessment,
    run_all,
)

NOW = datetime(2026, 11, 24, 0, 0, tzinfo=timezone.utc)
FRESH = "2026-11-20T00:00:00+00:00"
STALE = "2026-09-01T00:00:00+00:00"


def rep(time=FRESH, findings=()):
    from ds_check.model import _parse_time
    return Report(target="t1", assessment_time=_parse_time(time),
                  findings=tuple(findings))


class TestStale(unittest.TestCase):
    def test_fires_when_old(self):
        out = rule_stale_assessment(rep(time=STALE), NOW)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "HIGH")

    def test_quiet_when_fresh(self):
        self.assertEqual(rule_stale_assessment(rep(), NOW), [])


class TestRiskRules(unittest.TestCase):
    def test_critical_high(self):
        f = Finding(id="DS-1", title="t", risk="CRITICAL")
        out = rule_open_critical(rep(findings=(f,)), NOW)
        self.assertEqual(len(out), 1)
        self.assertIn("DS-1", out[0].detail)

    def test_closed_critical_ignored(self):
        f = Finding(id="DS-1", title="t", risk="CRITICAL", status="CLOSED")
        self.assertEqual(rule_open_critical(rep(findings=(f,)), NOW), [])

    def test_high_rule(self):
        f = Finding(id="DS-2", title="t", risk="HIGH")
        self.assertEqual(len(rule_open_high(rep(findings=(f,)), NOW)), 1)

    def test_medium_rule(self):
        f = Finding(id="DS-3", title="t", risk="MEDIUM")
        out = rule_open_medium(rep(findings=(f,)), NOW)
        self.assertEqual(out[0].severity, "MEDIUM")

    def test_deferred_without_note(self):
        f = Finding(id="DS-4", title="t", status="DEFERRED")
        self.assertEqual(len(rule_deferred_without_note(rep(findings=(f,)), NOW)), 1)

    def test_deferred_with_note_quiet(self):
        f = Finding(id="DS-4", title="t", status="DEFERRED", note="accepted")
        self.assertEqual(rule_deferred_without_note(rep(findings=(f,)), NOW), [])


class TestRunAll(unittest.TestCase):
    def test_sorted_high_first(self):
        fs = (Finding(id="A", title="t", risk="MEDIUM"),
              Finding(id="B", title="t", risk="CRITICAL"))
        out = run_all(rep(findings=fs), NOW)
        self.assertEqual(out[0].severity, "HIGH")

    def test_exit_codes(self):
        self.assertEqual(exit_code([]), 0)
        crit = run_all(rep(findings=(Finding(id="A", title="t", risk="CRITICAL"),)), NOW)
        self.assertEqual(exit_code(crit), 2)
        med = run_all(rep(findings=(Finding(id="A", title="t", risk="MEDIUM"),)), NOW)
        self.assertEqual(exit_code(med), 1)


if __name__ == "__main__":
    unittest.main()

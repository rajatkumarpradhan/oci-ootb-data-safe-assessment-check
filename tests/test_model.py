import unittest
from datetime import datetime, timezone

from ds_check.model import (Finding, Report, ReportError, load_report)

SAMPLE = "samples/report_messy.json"


class TestLoad(unittest.TestCase):
    def test_load_ok(self):
        rep = load_report(SAMPLE)
        self.assertEqual(rep.target, "adb-prod-orders")
        self.assertEqual(len(rep.findings), 6)

    def test_rejects_bad_json(self):
        with self.assertRaises(ReportError):
            load_report("README.md")

    def test_rejects_missing_file(self):
        with self.assertRaises(ReportError):
            load_report("does-not-exist.json")

    def test_finding_defaults(self):
        f = Finding(id="DS-1", title="t")
        self.assertEqual(f.risk, "MEDIUM")
        self.assertTrue(f.is_open())

    def test_open_findings_filter(self):
        rep = load_report(SAMPLE)
        self.assertEqual(len(rep.open_findings()), 5)

    def test_age_days(self):
        rep = load_report(SAMPLE)
        now = datetime(2026, 10, 30, 9, 15, tzinfo=timezone.utc)
        self.assertAlmostEqual(rep.age_days(now), 30.0)


if __name__ == "__main__":
    unittest.main()

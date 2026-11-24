import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from ds_check.cli import main

NOW = "2026-11-24T12:00:00Z"


class TestCli(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_messy_exit_2(self):
        code, out, _ = self.run_cli("samples/report_messy.json", "--now", NOW)
        self.assertEqual(code, 2)
        self.assertIn("DS001", out)
        self.assertIn("DS-1001", out)

    def test_clean_exit_0(self):
        code, out, _ = self.run_cli("samples/report_clean.json", "--now", NOW)
        self.assertEqual(code, 0)
        self.assertIn("gate passed", out)

    def test_error_exit_3(self):
        code, _, err = self.run_cli("README.md", "--now", NOW)
        self.assertEqual(code, 3)
        self.assertIn("report error", err)


if __name__ == "__main__":
    unittest.main()

# oci-ootb-data-safe-assessment-check

**OOTB project: wires built-in OCI services, with a small custom release-gate
tool.** OCI Data Safe runs the security assessment; OCI Events and OCI
Notifications deliver the "assessment finished" signal; the custom Python in
this repo gates on the exported report. Everything runs **offline against
synthetic sample reports** - no live tenancy, no credentials.

## Built-in OCI services used (native configuration, no custom code)

1. **OCI Data Safe** - register the target database and run (or schedule) a
   *security assessment*; Data Safe produces the findings report this repo's
   tool consumes.
2. **OCI Events** - an event rule matches the Data Safe
   `Security Assessment - End` event type, so downstream automation fires when
   an assessment completes.
3. **OCI Notifications** - a topic + subscription that the event rule
   publishes to, so the team gets the completion notice and the gate result.

## Custom code in this repo

`ds_check/` is a small offline gate that reads a **synthetic** Data Safe
assessment report (JSON export) and decides pass/fail:

| Rule | Severity | Finding |
| ---- | -------- | ------- |
| DS001 | HIGH | Assessment older than 30 days (stale posture) |
| DS002 | HIGH | Any CRITICAL finding still OPEN |
| DS003 | HIGH | Any HIGH finding still OPEN |
| DS004 | MEDIUM | Any MEDIUM finding still OPEN |
| DS005 | LOW | Any LOW/ADVISORY finding still OPEN |
| DS006 | LOW | DEFERRED finding without a justification note |

Exit codes: `0` gate passed, `1` only MEDIUM/LOW gate findings, `2` HIGH gate
findings, `3` malformed report. `--now` pins the reference time so the
staleness rule is deterministic in tests and CI.

## What actually ran vs what is template-only

- **Ran (local + CI, output verified):** the Python gate on both sample
  reports, and 19 unit tests, on Python 3.10/3.11/3.12. CI re-runs both demos
  and asserts the messy report exits 2 and the clean report exits 0.
- **Template only:** `terraform/main.tf` (Data Safe target registration,
  Events rule, Notifications topic). It shows the wiring but has **not** been
  plan/apply validated against a live tenancy, and no live Data Safe
  assessment was executed.
- The report format in `samples/` is a simplified stand-in for a real Data
  Safe assessment export.

## Run it

```bash
python -m ds_check.cli samples/report_messy.json --now 2026-11-24T12:00:00Z  # exits 2
python -m ds_check.cli samples/report_clean.json --now 2026-11-24T12:00:00Z  # exits 0
```

## Test it

```bash
python -m unittest discover -s tests -v   # 19 tests
```

## Layout

```
ds_check/       model.py (report loading), rules.py (DS001-DS006), cli.py
samples/        messy + clean synthetic assessment reports
tests/          19 unittest tests (model, rules, CLI)
terraform/      template-only Data Safe + Events + Notifications wiring
```

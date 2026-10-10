"""Run and persist actual verification evidence; no Pine compiler claims."""

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys

from .audit import source_audit


def main():
    commands = [
        [sys.executable, "-m", "compileall", "-q", "eaa"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests/eaa", "-v"],
        [sys.executable, "-m", "eaa", "eaa/fixtures/synthetic_trades.csv", "--calendar", "eaa/fixtures/synthetic_calendar.csv", "--paths", "eaa/fixtures/synthetic_paths.csv", "--rules", "eaa/config/project_550_v1.json", "--contracts", "1,4", "--extra-slippage", "0,1", "--commissions", "1,2", "--bootstrap", "30", "--output", "docs/eaa/evidence/SYNTHETIC_CLI_SMOKE.json"],
    ]
    records = []
    for command in commands:
        result = subprocess.run(command, text=True, capture_output=True)
        records.append({"command": command, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    result_file = Path("docs/eaa/evidence/SYNTHETIC_CLI_SMOKE.json")
    if records[-1]["exit_code"] == 0:
        smoke = json.loads(result_file.read_text())
        # Keep per-scenario summaries and the first deterministic event trace.
        for scenario in smoke["scenarios"]:
            scenario["first_window_trace"] = scenario.pop("windows")[0]
        smoke["evidence_note"] = "SYNTHETIC ONLY. Full window traces are reproducible with the recorded CLI command."
        result_file.write_text(json.dumps(smoke, indent=2) + "\n")
    evidence = {"executed_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(), "platform": platform.platform(), "commands": records, "static_assertions": source_audit(Path.cwd()), "pine_compiled": False, "strategy_performance_tested": False}
    Path("docs/eaa/evidence/verification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"commands": len(records), "all_passed": all(r["exit_code"] == 0 for r in records), "unittest_log": records[1]["stderr"][-250:], "pine_compiled": False}))
    return 0 if all(r["exit_code"] == 0 for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())

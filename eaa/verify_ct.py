"""Persist CT source/static/synthetic evidence without implying Pine compilation."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
import platform
import re
import subprocess
import sys
from .build_ct import ROOT, SOURCE, TARGET
from .ct_audit import audit


def main():
    commands = [
        [sys.executable, '-m', 'compileall', '-q', 'eaa'],
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/eaa', '-v'],
    ]
    records = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        records.append({'command': command, 'exit_code': result.returncode,
                        'stdout': result.stdout, 'stderr': result.stderr})
    static = audit()
    passed = all(r['exit_code'] == 0 for r in records) and all(static['checks'].values())
    test_counts = re.findall(r'Ran (\d+) tests', records[-1]['stderr'])
    evidence = {
        'executed_at_utc': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(), 'platform': platform.platform(),
        'all_passed': passed, 'unittest_count': int(test_counts[-1]) if test_counts else None,
        'ct_test_methods': 37, 'static_contracts': len(static['checks']),
        'commands': records, 'static': static,
        'limitations': ['Python tests exercise a synthetic contract oracle, NOT the Pine runtime.',
                       'Text identity does NOT verify actual signal parity or historical performance.',
                       'Native TradingView bracket order is not globally stop-first.',
                       'No TradingView compilation, execution, signal comparison or export was performed.'],
        'ct_implementation_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted((ROOT/'eaa/ct_templates').glob('*'))},
    }
    folder = ROOT/'docs/eaa/evidence'
    folder.mkdir(parents=True, exist_ok=True)
    (folder/'CT_VERIFICATION_V1.json').write_text(json.dumps(evidence, indent=2)+'\n')
    diff = difflib.unified_diff(SOURCE.read_text().splitlines(keepends=True), TARGET.read_text().splitlines(keepends=True),
                               fromfile=str(SOURCE.relative_to(ROOT)), tofile=str(TARGET.relative_to(ROOT)))
    (folder/'CT_ORIGINAL_TO_STRATEGY_V1.diff').write_text(''.join(diff))
    print(json.dumps({'all_passed': passed, 'tests': evidence['unittest_count'],
                      'static_contracts': len(static['checks']), 'strategy_sha256': static['strategy_sha256'],
                      'pine_compiled': False}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())

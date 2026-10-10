"""Reproducible source fingerprints, structural checks and input-data inventory."""

import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from .io import timestamp


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_audit(root):
    root = Path(root)
    original_path = root / "pine/eaa/EAA_HMA_MIDDAY_ORIGINAL_V1.pine"
    fixed_path = root / "pine/eaa/EAA_HMA_MIDDAY_EXEC_FIXED_V1.pine"
    ct_path = root / "pine/eaa/reference/CT_SCALPER_PUBLIC_BACKTEST_SOURCE_V1.pine"
    original, fixed, ct = [p.read_text() for p in (original_path, fixed_path, ct_path)]
    def expr(source, name):
        return next(line for line in source.splitlines() if line.startswith(name + " ="))
    checks = {
        "hma_long_condition_byte_equivalent_after_newline_normalization": expr(original, "longCondition") == expr(fixed, "longCondition"),
        "hma_short_condition_unchanged": expr(original, "shortCondition") == expr(fixed, "shortCondition"),
        "hma_all_original_inputs_unchanged": re.findall(r"^.*\binput.*$", original, re.M) == re.findall(r"^.*\binput.*$", fixed, re.M),
        "hma_original_session_retained": "t = time(timeframe.period, '0830-1545:23456')" in fixed,
        "hma_no_active_short_entry": not any("strategy.entry" in line and "strategy.short" in line and not line.lstrip().startswith("//") for line in fixed.splitlines()),
        "hma_no_active_security_request": not any("request.security" in line and not line.lstrip().startswith("//") for line in fixed.splitlines()),
        "hma_cancel_and_immediate_session_flat": "strategy.cancel_all()" in fixed and "immediately = true" in fixed,
        "hma_pyramiding_zero": "pyramiding = 0" in fixed,
        "ct_public_source_is_strategy_not_indicator": ct.splitlines()[8].startswith("strategy("),
        "ct_public_footprint_call_count_one": len(re.findall(r"request\.footprint\(", ct)) == 1,
        "ct_public_smart_exit_disabled_both_directions": ct.count("math.max(16.0, math.min(16.0,") == 2,
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    return {"status": "VERIFIED_STATIC_ASSERTIONS_NOT_PINE_COMPILE", "checks": checks, "sources": [{"path": str(p.relative_to(root)), "sha256": sha(p), "bytes": p.stat().st_size, "lines": len(p.read_text().splitlines())} for p in (original_path, fixed_path, ct_path)], "pine_compiled": False, "tradingview_executed": False}


def market_data_audit(path):
    rows, duplicates, unordered, bad_ohlc, offtick, negative_volume, gaps = 0, 0, 0, 0, 0, 0, 0
    previous, first, last = None, None, None
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            at = timestamp(r["time"])
            o, h, l, c, v = [float(r[k]) for k in ("open", "high", "low", "close", "volume")]
            first = first or at
            last = at
            rows += 1
            duplicates += previous == at
            unordered += previous is not None and at < previous
            gaps += previous is not None and (at - previous).total_seconds() > 60
            bad_ohlc += not (0 < l <= min(o, c) <= max(o, c) <= h)
            offtick += any(abs(x * 4 - round(x * 4)) > 1e-8 for x in (o, h, l, c))
            negative_volume += v < 0
            previous = at
    return {"file": Path(path).name, "sha256": sha(path), "rows": rows, "first": first.isoformat(), "last": last.isoformat(), "adjacent_duplicate_timestamps": duplicates, "out_of_order": unordered, "invalid_ohlc": bad_ohlc, "offtick_bars": offtick, "negative_volume": negative_volume, "gaps_gt_60_seconds": gaps, "canonical_dataset_verified": False, "note": "Gaps include normal closures; neither full market coverage nor roll-policy identity is verified."}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--bars", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = {"source_audit": source_audit(args.root)}
    if args.bars:
        result["market_data_audit"] = market_data_audit(args.bars)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

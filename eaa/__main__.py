from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys

from .funded import Rules, bootstrap, rolling, summarize
from .io import attach_paths, load_calendar, load_trades
from .ohlcv import attach_ohlcv


def main():
    p = argparse.ArgumentParser(description="EAA conditional MNQ challenge replay; never firm certification")
    p.add_argument("trades", type=Path)
    p.add_argument("--calendar", type=Path, required=True)
    p.add_argument("--rules", type=Path, required=True)
    data = p.add_mutually_exclusive_group()
    data.add_argument("--paths", type=Path)
    data.add_argument("--bars", type=Path, help="1m OHLC envelope; approximate, not an exact equity path")
    p.add_argument("--export-timezone")
    p.add_argument("--sheet")
    p.add_argument("--column-map", type=Path)
    p.add_argument("--contracts", default="1,2,3,4,5,6,8,10,15,20")
    p.add_argument("--extra-slippage", default="0,1,2")
    p.add_argument("--commissions", default="1,2,3")
    p.add_argument("--risk-budget", type=float)
    p.add_argument("--horizon", type=int, default=15)
    p.add_argument("--bootstrap", type=int, default=0)
    p.add_argument("--block", type=int, default=5)
    p.add_argument("--seed", type=int, default=20261009)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        rules = Rules(**json.loads(args.rules.read_text()))
        mapping = json.loads(args.column_map.read_text()) if args.column_map else None
        trades = load_trades(args.trades, args.export_timezone, mapping, args.sheet)
        if args.paths:
            trades = attach_paths(trades, args.paths, args.export_timezone)
        if args.bars:
            trades = attach_ohlcv(trades, args.bars)
        calendar = load_calendar(args.calendar)
        quantities = sorted(set(int(v) for v in args.contracts.split(",")))
        slippages = sorted(set(float(v) for v in args.extra_slippage.split(",")))
        commissions = sorted(set(float(v) for v in args.commissions.split(",")))
        scenarios = []
        for qty in quantities:
            for slip in slippages:
                for commission in commissions:
                    scenario = replace(rules, commission_rt=commission, additional_slippage_ticks_side=slip)
                    results = rolling(trades, calendar, scenario, args.horizon, qty, args.risk_budget)
                    record = {"contracts_cap": qty, "additional_slippage_ticks_side": slip, "commission_rt": commission, "summary": summarize(results), "windows": [asdict(r) for r in results]}
                    if args.bootstrap:
                        resamples = bootstrap(trades, calendar, scenario, horizon=args.horizon, iterations=args.bootstrap, block=args.block, seed=args.seed, contracts=qty, risk_budget=args.risk_budget)
                        record["bootstrap"] = summarize(resamples)
                    scenarios.append(record)
        # Compare sizing only at the declared base costs; never select cheapest
        # friction to make a sizing recommendation look more attractive.
        eligible = [s for s in scenarios if s["additional_slippage_ticks_side"] == rules.additional_slippage_ticks_side and s["commission_rt"] == rules.commission_rt and s["summary"]["fail_pct"] <= 30]
        ranked = sorted(eligible, key=lambda s: (-s["summary"]["pass_within"]["10"], -s["summary"]["pass_pct"], s["summary"]["fail_pct"], s["contracts_cap"]))
        files = [args.trades, args.calendar, args.rules] + ([args.paths] if args.paths else []) + ([args.bars] if args.bars else []) + ([args.column_map] if args.column_map else [])
        report = {"version": "1.0.0", "rules": asdict(rules), "inputs_sha256": {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}, "horizon": args.horizon, "seed": args.seed, "bootstrap_block": args.block, "source_trades": len(trades), "session_count": len(calendar), "best_examined_contracts": ranked[0]["contracts_cap"] if ranked and ranked[0]["summary"]["pass_pct"] > 0 else None, "selection_status": "EXPLORATORY_IN_SAMPLE_NOT_OPTIMAL_OR_APPROVED", "approximate": True, "rules_verified": False, "assumptions": ["EOD pass; strict 50% consistency without provider cushion", "No holiday/early-close certification; explicit calendar still required", "America/New_York is a modeling timezone, not proof of provider EST/DST interpretation", "Prices already include exported fills; additional slippage is incremental", "Filtering/liquidation does not regenerate signals absent from the original export", "Intraday paths are sampled; gaps and unknown fill order remain", "Profit stop is an observed liquidation trigger, never a guaranteed maximum; overshoot retained"], "scenarios": scenarios}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"output": str(args.output), "scenarios": len(scenarios), "best_examined_contracts": report["best_examined_contracts"], "approximate": True}))
        return 0
    except (ValueError, KeyError, OSError) as error:
        print(f"INPUT/CONFIG ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""CT Scalper EAA TV-ledger vs EAB RR gate: reproducible matched-trade research.
NO TradingView EAB rerun, NO footprint/signal reconstruction, NO funded/live approval.

Run:
python ct_eab_rr_ledger_qa.py --zip D01042_CT_SCALPER_RESEARCH_REPRODUCIBLE_2026-10-12.zip --out out_ct

Uses EAA original 1MNQ TradingView List-of-Trades contained in the existing owned ZIP.
This only REMOVES trades by RR computed at entry FILL. Pine EAB gates at SIGNAL CLOSE.
It therefore cannot recover trades newly enabled when a rejected trade frees a slot.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import math
import random
import re
import zipfile
from collections import defaultdict
from pathlib import Path

TV_FILE_PREFIX = "EAA_CT_Scalper_STRATEGY_V1_CME_MINI_MNQ1!"
RE_LEVELS = re.compile(r"CT_([LS])_([A-Z]+)\|SL=([0-9.]+)\|TP=([0-9.]+)")
MODELS = ("FADE", "DIV", "TRAP", "AGG", "ABSORB", "VRZ")


def load_tv(zip_path: Path):
    with zipfile.ZipFile(zip_path) as z:
        filenames = [n for n in z.namelist() if n.startswith(TV_FILE_PREFIX) and n.endswith(".csv")]
        if len(filenames) != 1:
            raise RuntimeError(f"Expected one reference TV CSV, found: {filenames}")
        with z.open(filenames[0]) as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig", newline=""))
            pairs: dict[int, dict] = {}
            for row in reader:
                tid = int(row["Trade number"])
                state = pairs.setdefault(tid, {"id": tid})
                typ = row["Type"]
                if typ.startswith("Entry"):
                    m = RE_LEVELS.fullmatch(row["Signal"])
                    if not m:
                        raise ValueError(f"Missing immutable structural levels for trade {tid}")
                    side, model, stop, target = m.groups()
                    if model not in MODELS:
                        raise ValueError(f"Unexpected model: {model}")
                    if ("long" in typ) != (side == "L"):
                        raise ValueError(f"Trade {tid} side mismatch")
                    state.update(entry_time=row["Date and time"], side=1 if side == "L" else -1,
                                 model=model, entry=float(row["Price USD"]),
                                 stop=float(stop), target=float(target))
                elif typ.startswith("Exit"):
                    state.update(exit_time=row["Date and time"], pnl=float(row["Net PnL USD"]),
                                 exit_reason=row["Signal"])
            trades = [pairs[k] for k in sorted(pairs)]
    for t in trades:
        if not {"entry_time", "exit_time", "model", "pnl", "stop", "target"}.issubset(t):
            raise AssertionError(f"Missing entry or exit for {t['id']}")
        s = t["side"]
        risk = (t["entry"] - t["stop"]) * s
        reward = (t["target"] - t["entry"]) * s
        if risk <= 0 or reward <= 0:
            raise AssertionError(f"Invalid risk/target at trade {t['id']}: {risk}, {reward}")
        t["rr_fill"] = reward / risk
        t["year"] = int(t["entry_time"][:4])
        t["date"] = t["entry_time"][:10]
        t["quarter"] = (int(t["entry_time"][5:7]) - 1) // 3 + 1
    return filenames[0], trades


def allowed(t, policy):
    if policy == "A_ALL": return True
    if policy == "B_ABSORB_RR2": return t["model"] != "ABSORB" or t["rr_fill"] >= 2.0
    if policy == "C_ABSORB_RR2_FADE_RR1p5":
        return ((t["model"] != "ABSORB" or t["rr_fill"] >= 2.0)
                and (t["model"] != "FADE" or t["rr_fill"] >= 1.5))
    if policy == "CONTROL_NO_ABSORB": return t["model"] != "ABSORB"
    raise ValueError(policy)


def metrics(trades, extra_cost=0.0):
    p = [t["pnl"] - extra_cost for t in trades]
    gross_win = sum(max(0.,x) for x in p)
    gross_loss = sum(max(0.,-x) for x in p)
    net = sum(p)
    bal=peak=dd=0.
    for x in p:
        bal+=x
        peak=max(peak,bal)
        dd=max(dd,peak-bal)
    return dict(n=len(p),net_usd=round(net,2),
                pf=round(gross_win/gross_loss,4) if gross_loss else None,
                avg_usd=round(net/len(p),3) if p else None,
                win_pct=round(100*sum(x>0 for x in p)/len(p),2) if p else None,
                closed_trade_dd_usd=round(dd,2))


def paired_day_bootstrap(source, policy, repeats=10000, seed=20261012):
    # Resample distinct DATES WITH ORIGINAL TV TRADES, not individual trades.
    # Dates are chart-export dates, not verified CME settlement-day grouping.
    byday = defaultdict(lambda: {"diff":0., "retained_pnl":0., "retained_n":0})
    for t in source:
        x=byday[t["date"]]
        if allowed(t,policy):
            x["retained_pnl"]+=t["pnl"]
            x["retained_n"]+=1
        else:
            x["diff"]-=t["pnl"]
    days=list(byday.values())
    n=len(days)
    if n<3: return None
    rng=random.Random(seed)
    diffs=[]
    filtered_means=[]
    for _ in range(repeats):
        ds=[days[rng.randrange(n)] for _ in range(n)]
        diffs.append(sum(x["diff"] for x in ds)/n)
        total_n=sum(x["retained_n"] for x in ds)
        if total_n:
            filtered_means.append(sum(x["retained_pnl"] for x in ds)/total_n)
    diffs.sort()
    filtered_means.sort()
    def q(xs,p):return round(xs[int(p*(len(xs)-1))],3)
    return dict(active_dates=n,
                difference_usd_per_original_active_date=round(sum(x["diff"] for x in days)/n,3),
                difference_ci95_per_active_date=[q(diffs,.025),q(diffs,.975)],
                filtered_trade_mean_ci95=[q(filtered_means,.025),q(filtered_means,.975)],
                bootstrap_probability_improvement=round(sum(x>0 for x in diffs)/len(diffs),3))


def run(zip_path, out):
    name,ts=load_tv(Path(zip_path))
    if len(ts)!=1197 or round(sum(t["pnl"] for t in ts),2)!=-447.50:
        raise AssertionError("Original TradingView ledger does not match 1197 / -447.50 USD")
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    policies=["A_ALL","B_ABSORB_RR2","C_ABSORB_RR2_FADE_RR1p5","CONTROL_NO_ABSORB"]
    details=[]
    boot=[]
    for year in (2024,2025,2026):
        t=[x for x in ts if x["year"]==year]
        for policy in policies:
            v=[x for x in t if allowed(x,policy)]
            for extra in (0,2,4):
                details.append(dict(year=year,policy=policy,extra_usd_per_mnq=extra,
                                    **metrics(v,extra_cost=extra)))
            if policy!="A_ALL":
                boot.append(dict(year=year,policy=policy,
                                 **paired_day_bootstrap(t,policy,seed=20261012+year)))
    for quarter in (1,2,3,4):
        t=[x for x in ts if x["year"]==2026 and x["quarter"]==quarter]
        for policy in policies:
            details.append(dict(year=f"2026Q{quarter}",policy=policy,
                                extra_usd_per_mnq=0,**metrics([x for x in t if allowed(x,policy)])))
    import hashlib
    sha=hashlib.sha256(Path(zip_path).read_bytes()).hexdigest()
    meta=dict(source=name,archive_sha256=sha,original_count=len(ts),original_net_usd=round(sum(t["pnl"] for t in ts),2),
              model_counts={m:sum(x["model"]==m for x in ts) for m in MODELS},
              qa_type="FILL_RR_ON_ORIGINAL_FILLED_TRADES_ONLY",
              passed_tv_original_baseline=True,
              note="Does NOT reconstruct TradingView Pine EAB signal-close gate, new entries, order fill, or funded.")
    (out/"CT_EAB_RR_QA_SUMMARY.json").write_text(json.dumps(dict(meta=meta,metrics=details,paired_bootstrap=boot),indent=2),
                                                   encoding="utf-8")
    print(json.dumps(dict(meta=meta,metrics=details,paired_bootstrap=boot),indent=2))


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--zip",required=True)
    a.add_argument("--out",default="out_ct")
    x=a.parse_args()
    run(x.zip,x.out)

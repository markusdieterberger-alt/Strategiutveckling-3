#!/usr/bin/env python3
"""
FVG Magnet Study v1 — MNQ
Purpose:
  Test whether nearby untouched 30m/1h/4h FVGs act as statistically useful magnets,
  before building a trading entry model.

Design:
  - Causal resampling from 1m OHLCV.
  - Standard 3-candle FVG:
      bullish: low[t] > high[t-2], zone = [high[t-2], low[t]]
      bearish: high[t] < low[t-2], zone = [high[t], low[t-2]]
  - FVG becomes active only after its timeframe bar is completed.
  - FVG remains active until first touch.
  - Trend filter: completed 30m EMA20 slope + price side of EMA20.
  - Event: first qualifying minute per FVG where price is on the correct side,
    trend points toward the FVG, and near edge is within MAX_ATR_DIST * 1m ATR14.
  - Outcome: did price touch the near FVG edge within HORIZON_MIN before first
    adverse excursion of X ATR from event price?
  - One event per FVG to avoid minute-by-minute duplication.

Outputs:
  fvg_magnet_events.csv
  fvg_magnet_summary.csv
  fvg_magnet_overlap_summary.csv
"""

from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

TF_MAP = {"30m": "30min", "1h": "60min", "4h": "240min"}
DIST_BUCKETS = [0, 0.5, 1.0, 1.5, 2.0, np.inf]
DIST_LABELS = ["<=0.5", "0.5-1.0", "1.0-1.5", "1.5-2.0", ">2.0"]


def detect_columns(df: pd.DataFrame):
    cols = {c.lower(): c for c in df.columns}
    time_candidates = ["ts_event", "timestamp", "datetime", "date", "time"]
    def first(names):
        for n in names:
            if n in cols:
                return cols[n]
        raise ValueError(f"Missing one of {names}; columns={list(df.columns)}")
    return {
        "time": first(time_candidates),
        "open": first(["open"]),
        "high": first(["high"]),
        "low": first(["low"]),
        "close": first(["close"]),
        "volume": first(["volume", "vol"]),
    }


def load_1m(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    c = detect_columns(df)
    out = df[[c["time"], c["open"], c["high"], c["low"], c["close"], c["volume"]]].copy()
    out.columns = ["time", "open", "high", "low", "close", "volume"]
    out["time"] = pd.to_datetime(out["time"], utc=True, errors="coerce")
    out = out.dropna(subset=["time"]).sort_values("time").drop_duplicates("time")
    out = out.set_index("time")
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["open", "high", "low", "close"])
    return out


def resample_ohlcv(m1: pd.DataFrame, rule: str) -> pd.DataFrame:
    # label/closed right makes each HTF candle timestamp represent completion time.
    return (
        m1.resample(rule, label="right", closed="right")
          .agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
          .dropna(subset=["open","high","low","close"])
    )


def atr(df: pd.DataFrame, n=14) -> pd.Series:
    pc = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - pc).abs(),
        (df["low"] - pc).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()


@dataclass
class FVG:
    fvg_id: str
    tf: str
    direction: int
    formed_at: pd.Timestamp
    low: float
    high: float
    touched_at: pd.Timestamp | None = None


def build_fvgs(htf: pd.DataFrame, tf: str) -> list[FVG]:
    out = []
    for i in range(2, len(htf)):
        r = htf.iloc[i]
        r2 = htf.iloc[i-2]
        t = htf.index[i]
        # bullish gap
        if r["low"] > r2["high"]:
            out.append(FVG(
                fvg_id=f"{tf}|B|{t.isoformat()}",
                tf=tf, direction=1, formed_at=t,
                low=float(r2["high"]), high=float(r["low"])
            ))
        # bearish gap
        if r["high"] < r2["low"]:
            out.append(FVG(
                fvg_id=f"{tf}|S|{t.isoformat()}",
                tf=tf, direction=-1, formed_at=t,
                low=float(r["high"]), high=float(r2["low"])
            ))
    return out


def completed_30m_trend(m1: pd.DataFrame):
    m30 = resample_ohlcv(m1, "30min")
    m30["ema20"] = m30["close"].ewm(span=20, adjust=False).mean()
    m30["ema20_prev"] = m30["ema20"].shift(1)
    # Map last completed 30m candle forward to 1m.
    trend = m30[["ema20","ema20_prev"]].reindex(m1.index, method="ffill")
    return trend


def first_touch_time(m1: pd.DataFrame, fvg: FVG):
    after = m1.loc[m1.index > fvg.formed_at]
    if after.empty:
        return None
    if fvg.direction == 1:
        hits = after[after["high"] >= fvg.low]
    else:
        hits = after[after["low"] <= fvg.high]
    return None if hits.empty else hits.index[0]


def evaluate_event(m1, t0, direction, target_edge, atr0, horizon, adverse_mults):
    px0 = float(m1.at[t0, "close"])
    w = m1.loc[(m1.index > t0) & (m1.index <= t0 + pd.Timedelta(minutes=horizon))]
    if w.empty:
        return {}
    result = {}
    if direction == 1:
        target_hits = w.index[w["high"] >= target_edge]
        touch_t = target_hits[0] if len(target_hits) else pd.NaT
        for x in adverse_mults:
            adverse = px0 - x * atr0
            adv_hits = w.index[w["low"] <= adverse]
            adv_t = adv_hits[0] if len(adv_hits) else pd.NaT
            result[f"touch_before_{x:g}atr_adverse"] = bool(
                pd.notna(touch_t) and (pd.isna(adv_t) or touch_t <= adv_t)
            )
    else:
        target_hits = w.index[w["low"] <= target_edge]
        touch_t = target_hits[0] if len(target_hits) else pd.NaT
        for x in adverse_mults:
            adverse = px0 + x * atr0
            adv_hits = w.index[w["high"] >= adverse]
            adv_t = adv_hits[0] if len(adv_hits) else pd.NaT
            result[f"touch_before_{x:g}atr_adverse"] = bool(
                pd.notna(touch_t) and (pd.isna(adv_t) or touch_t <= adv_t)
            )
    result["touch_within_horizon"] = pd.notna(touch_t)
    result["touch_minutes"] = ((touch_t - t0).total_seconds()/60.0) if pd.notna(touch_t) else np.nan
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, default=Path("research/fvg_magnet/results"))
    ap.add_argument("--max-atr-dist", type=float, default=2.0)
    ap.add_argument("--horizon", type=int, default=240)
    ap.add_argument("--session-start", default="13:30")  # UTC default ~ US cash open, DST imperfect
    ap.add_argument("--session-end", default="20:00")
    args = ap.parse_args()

    m1 = load_1m(args.csv)
    m1["atr14"] = atr(m1, 14)
    trend = completed_30m_trend(m1)
    m1 = m1.join(trend)

    fvgs = []
    for tf, rule in TF_MAP.items():
        h = resample_ohlcv(m1, rule)
        fvgs += build_fvgs(h, tf)

    # Precompute first touch and only consider untouched interval.
    for f in fvgs:
        f.touched_at = first_touch_time(m1, f)

    records = []
    adverse_mults = [0.25, 0.5, 0.75, 1.0]

    for f in fvgs:
        start = f.formed_at
        end = f.touched_at if f.touched_at is not None else m1.index[-1]
        w = m1.loc[(m1.index > start) & (m1.index < end)].copy()
        if w.empty:
            continue

        # Price must be on correct side of the target.
        if f.direction == 1:
            w = w[w["close"] < f.low]
            w["target_edge"] = f.low
            w["distance"] = f.low - w["close"]
            trend_ok = (w["close"] > w["ema20"]) & (w["ema20"] > w["ema20_prev"])
        else:
            w = w[w["close"] > f.high]
            w["target_edge"] = f.high
            w["distance"] = w["close"] - f.high
            trend_ok = (w["close"] < w["ema20"]) & (w["ema20"] < w["ema20_prev"])

        w = w[trend_ok & w["atr14"].notna() & (w["atr14"] > 0)]
        if w.empty:
            continue
        w["distance_atr"] = w["distance"] / w["atr14"]
        w = w[w["distance_atr"] <= args.max_atr_dist]
        if w.empty:
            continue

        # One event per FVG: first moment it becomes a qualifying magnet.
        t0 = w.index[0]
        row = w.iloc[0]
        ev = {
            "fvg_id": f.fvg_id,
            "tf": f.tf,
            "direction": "long" if f.direction == 1 else "short",
            "formed_at": f.formed_at,
            "event_time": t0,
            "event_price": float(row["close"]),
            "target_edge": float(row["target_edge"]),
            "atr14": float(row["atr14"]),
            "distance_atr": float(row["distance_atr"]),
        }
        ev.update(evaluate_event(
            m1, t0, f.direction, float(row["target_edge"]),
            float(row["atr14"]), args.horizon, adverse_mults
        ))
        records.append(ev)

    events = pd.DataFrame(records)
    args.out.mkdir(parents=True, exist_ok=True)
    events.to_csv(args.out / "fvg_magnet_events.csv", index=False)

    if events.empty:
        print("No events found.")
        return

    events["distance_bucket"] = pd.cut(
        events["distance_atr"], DIST_BUCKETS, labels=DIST_LABELS,
        include_lowest=True, right=True
    )

    metrics = ["touch_within_horizon"] + [f"touch_before_{x:g}atr_adverse" for x in adverse_mults]
    summary = (
        events.groupby(["tf","distance_bucket"], observed=True)[metrics]
              .agg(["count","mean"])
              .reset_index()
    )
    summary.to_csv(args.out / "fvg_magnet_summary.csv", index=False)

    # Confluence: another active FVG edge of a different TF within 0.25 ATR of target.
    # Approximate using event-time contemporaneous geometry.
    event_lookup = events[["event_time","target_edge","atr14","tf","direction","fvg_id"]].copy()
    confluence = []
    for _, e in events.iterrows():
        peers = event_lookup[
            (event_lookup["event_time"] == e["event_time"]) &
            (event_lookup["direction"] == e["direction"]) &
            (event_lookup["tf"] != e["tf"]) &
            (event_lookup["fvg_id"] != e["fvg_id"])
        ]
        overlap = ((peers["target_edge"] - e["target_edge"]).abs() <= 0.25 * e["atr14"]).any()
        confluence.append(overlap)
    events["htf_confluence_025atr"] = confluence
    events.to_csv(args.out / "fvg_magnet_events.csv", index=False)

    overlap_summary = events.groupby(["htf_confluence_025atr"])[metrics].mean().reset_index()
    overlap_summary["n"] = events.groupby(["htf_confluence_025atr"]).size().values
    overlap_summary.to_csv(args.out / "fvg_magnet_overlap_summary.csv", index=False)

    print("Events:", len(events))
    print("\nOverall:")
    print(events[metrics].mean().to_string())
    print("\nBy TF:")
    print(events.groupby("tf")[metrics].agg(["count","mean"]).to_string())
    print("\nBy distance:")
    print(events.groupby("distance_bucket", observed=True)[metrics].agg(["count","mean"]).to_string())
    print("\nConfluence:")
    print(overlap_summary.to_string(index=False))


if __name__ == "__main__":
    main()

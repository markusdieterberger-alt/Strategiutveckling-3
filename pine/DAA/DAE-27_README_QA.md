# DAE-27 — Canonical 1m strategy and 1m shadow viewer

**Status: DEVELOPMENT / UNVERIFIED TRADINGVIEW COMPILE / PARITY FAIL UNTIL TESTED.**
DAE-26 and every CT V1/V2 instance and alert stay unchanged.

## Files
- `DAE-27_1M_CANONICAL_STRATEGY.pine`: native TradingView `strategy()` on **1m only**. A hard `runtime.error` prevents any 5m/30m native backtest or contradictory fills. Built on DAE-26 with default VA Far, risk/reward choices 1:1, 1:1.5, 1:2, 2:1, 3:1, maximum risk control 1–600 USD per contract (200 USD default), blue setups, TP and SL markers. Added explicit $0.50 commission per side as default for 1 MNQ. Entry, stop, target, FVG/CRT/VP calculations unchanged from DAE-26.
- `DAE-27_1M_EVENT_VIEWER_5M_30M.pine`: independent **indicator** for MNQ1! on 1m, 5m and 30m charts. Pulls 1m OHLCV with `request.security_lower_tf`, reconstructs causally completed 30m CRT+FVG, computes dynamic 1m OHLCV proxy VP, order levels, and **SHADOW** 1m fill outcomes. Uses original 1m timestamps for labels via `xloc.bar_time`; green TP / red SL, blue setups. 450 newest event marks retained by default, max 480 (Pine's 500-label cap): cannot promise unlimited historical markers.

## How to use
1. Open a STANDARD MNQ1! **1-minute chart** and install `DAE-27_1M_CANONICAL_STRATEGY.pine`. Compile, check Strategy Tester settings and confirm actual trade list.
2. On **5m** or **30m**, use **only** `DAE-27_1M_EVENT_VIEWER_5M_30M.pine` to inspect a 1m-derived shadow visualization. It is NOT the native 1m strategy ledger.
3. Synchronize entry level, RR, initial risk USD, initial TP, stop mode, trailing activation and distance ticks, VP rows/value area, and commission between scripts.
4. In the strategy on 1m, note trade ID/time/price/side/exits for at least 20 consecutive completed trades. Match against the viewer loaded with the SAME 1m data window on both 5m and 30m. Record mismatches. No performance claims or live release until reconciliation.

## Unavoidable differences and limitations
- Pine `strategy()` always uses chart timeframe. There is no TradingView API allowing a higher-TF indicator to read a separate strategy's `strategy.closedtrades` ledger.
- The viewer therefore uses a **separate conservative synthetic 1m emulator** (with gap handling, stop-first when both SL and TP touch within one 1m bar). This may differ from TradingView's true broker emulator and is not yet a verified copy of native 1m fills. Native one-minute Strategy Tester results remain the *only official* result.
- The 5m/30m viewer should be *internally consistent* across TFs only if both load the same 1m coverage and model state. Differences in 1m history limits, chart start date, replay behavior, missing minutes or platform data revisions can still cause divergences. Viewer dashboard explicitly displays `SHADOW` and `NOT VERIFIED`.
- Viewer 30m markers update on **closed** 30m bars, not minute by minute in live realtime. Events are anchored at 1m times when they become visible.
- `request.security_lower_tf` data has plan-specific history caps (often 100K 1m bars on nonprofessional plans). Loading 1m content from different starting times can alter state.
- Existing DAE trading and box logic may still contain independent issues. Stop slippage/gaps can exceed 600 USD initial intended risk cap. No live signals/actions activated.

## QA checklist before promotion
- Native Pine v6 compile on both scripts.
- At least 20 1m reference native orderfill pairs; same instrument/sessions/costs; compare with viewer 1m/5m/30m for setup, entry bar/price, exit bar/price, type and net USD.
- Dedicated same-bar entry+exit, both SL/TP reached, gap over stop, trailing, profile mitigation, missing intrabars and 30m candle boundary cases.
- Verify blue arrow/TP/SL retention after >1000 chart bars under 500-label limit.
- Document PASS/FAIL; leave original DAE-26/CT V1/V2 unmodified.

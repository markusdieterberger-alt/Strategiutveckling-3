# ZAC v2 alpha1 — C4 implementation notes

File: `pine/zac-v2/ZAC_v2_0_alpha1_C4_CLEAN_REBUILD.pine`

## Purpose
First clean C4-only Pine port using the pre-code blueprint. This is an execution/parity QA build, not a promoted strategy.

## Source choices made explicitly
- DS180 profile mechanics: preserved Python helper.
- Session: 07:00–14:29 America/Chicago.
- FVG execution semantic default: SAME_TYPE_SOURCE.
- Displacement execution semantic default: BODY_SOURCE, while BODY and EDGE are both counted.
- Pending fill-bar policy: fill priority if the resting limit was touched before bar-close invalidation can be evaluated.

## Problems intentionally solved in alpha1
- No early tick-rounding of synthetic profile levels.
- Manual completed-5m RelVol20 with denominator excluding numerator.
- Manual completed 1H/4H aggregation for FVGs.
- True interval overlap pruning.
- Explicit FVG create/prune state.
- strategy.closedtrades ledger.
- invisible same-bar RT counter.
- raw-vs-executable price visibility.
- qty0 / blocked / invalid / expiry counters.
- compact mobile dashboard.

## Known open items
- C4 displacement source ambiguity BODY vs EDGE remains a parity question; no performance-based choice is allowed.
- Exact canonical pending fill/invalidation ordering is not recovered from original generator.
- Exact reference hard-flat time is not source-locked in D00054. alpha1 therefore does not invent an extra flat rule; max hold remains 120m.
- TradingView MNQ1! and canonical Databento volume-roll series differ on roll/gap days.
- Full n376 parity requires desktop/Deep Backtest and ideally a recovered timestamped reference ledger.

## Mobile acceptance
From one screenshot we should be able to see:
freeze/balance, RAW L/S, BODY/EDGE displacement, FVG same/any, <=8ATR, RelVol, risk, 2R room, orders/qty0, blocked, invalid/expired, fill+invalid conflicts, position transitions, ledger closes/invisible RT, FVG creation/pruning, current RelVol/ATR and raw→exec entry.

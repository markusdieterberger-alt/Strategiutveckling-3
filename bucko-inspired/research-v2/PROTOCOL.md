# BUCKO INSPIRED V2 — preregistered research / execution blocked
Date: 2026-10-14. Independent hypotheses, NOT a reconstruction of Bucko's proprietary indicator.

## Three independent mechanisms, applied to canonical MGC 5m
1. **Sweep → reclaim:** wick beyond prior 20-bar high/low, bar CLOSE back inside level; directional candle; EMA21/EMA50/EMA200 directional context.
2. **Unfilled FVG retest → continuation:** three-bar gap, size >=0.1 ATR(14), a first subsequent bar touches zone then closes back outside zone in EMA directional trend; gap consumed after first touch; expires after 30 bars.
3. **Supply/demand rejection:** confirmed 3-left / 3-right local pivot; zone half-width 0.25 ATR at pivot; first subsequent revisit rejects; expires after 60 bars. Pivots **not active until confirmation close**.

## Common frozen execution
- Canonical 1m Databento MGC, UTC 5m, *exactly five* 1-minute rows per candle, one contract only; sessions with no complete candle dropped.
- Signal at closed 5m bar, NEXT 5m open entry, no entry across missing five-minute continuity or contract roll.
- 1 MGC, $10 per price point, 0.1 tick, 1 tick slippage per side, $1/side fee; 1.5x ATR(14) stop and fixed R:R 1,2,3; SL-first if same candle hits both.
- Gap/roll forcibly closes current trade at first available next bar; such closes flagged and audited separately.
- One open position per model; no pyramiding. No optimization from resulting returns.
- Development 2019–2023, validation 2024–2026-04-30, recent 2026-05-01–2026-10-02. The controls are *historical partitions* rather than unbiased fresh forward tests.

## Reproducibility
Run `python bucko_mgc_v2.py /path/to/MGC_CANONICAL_1M_V1_0_2026-10-05.csv.gz --out results`.
Expected summary and per-trade CSV. Requires pandas and numpy.
Full source in `bucko_mgc_v2.py`. Canonical source Google Drive ID 1mezHKoBtkIlDt72ec81QXEORtHdCNiCG. Manifest includes SHA-256 and 37 rolls.

## Research status / blocking
Python and container execution tools failed repeatedly during this session (ClientError; Python kernel failed). **The V2 script was committed but was NOT executed or syntax-/schema-tested**; this means no valid trade counts, P&L, PF or funded outputs can be claimed. First priority when runtime returns: inspect actual column names, run on source, assert chronological causality, rerun same-bar ambiguity and gap/roll sensitivity; audit indicator vs Python parity before promotion. Do not confuse plausible mechanisms with demonstrated edge. CT Scalper remains unaffected.

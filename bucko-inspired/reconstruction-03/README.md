# Bucko Replica V3 — research 03.1

Independent MNQ Pine v6 indicator research, 2026-10-17. These are explicit original research assumptions, not the proprietary Bucko algorithm. No demonstrated edge, trading orders, or live deployment.

- `BUCKO_REPLICA_V3.pine`: standard MNQ 1m/5m price indicator. Confirmed 2/2 pivots, BOS, sweeps, separate FVG and pivot supply/demand zones; ten transparent binary price factors and an unknown eleventh footprint factor. Raw candidates remain visible when score or regime filters reject them. The initial threshold is six; the nominal `/11` scale is not an identified original score.
- `BUCKO_NATIVE_FP_PILOT.pine`: optional Premium/Ultimate companion. Select the core's `BR3_BUS` plot and confirm the connection. Default Quality only preserves the core approval. Gate additionally requires a valid directional native delta share. Missing native data never becomes invented buy/sell volume. Native footprint classification and resolution must be audited independently.
- `reference_replay.py`: Python 3.11+ / pandas / numpy diagnostic reference, not a Pine compiler or certified TradingView emulator. Use `python reference_replay.py --csv /path/to/own_minute_ohlcv.csv --out /path/to/results`. Expected fields: time, open, high, low, close, volume; timezone-aware ISO timestamps converted to UTC. No market data is included in this public branch.
- `test_causality.py`: synthetic tests, run `python -m unittest test_causality -v`.

TradingView compilation, chart runtime, Python–Pine parity, and footprint live/reload verification have NOT been performed. Static review and Python reference tests do not certify native execution. No strategy(), SL/TP model, fills, news service, account-risk control, or broker integration is supplied. Existing strategy versions are unchanged.

All thresholds, zone lifecycle rules, factor formulas, grades, and gates are REPLICA ASSUMPTION. Freeze code and inputs before further validation. The private project deliverable contains the evidence matrix, detailed specification, test protocol, and limitations.

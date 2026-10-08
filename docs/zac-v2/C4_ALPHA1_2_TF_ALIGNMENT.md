# C4 alpha1.2 — Timeframe boundary alignment

## alpha1.1 mobile observation
- Closed 3, PF 0.642
- RAW L/S 59/55
- BODY displacement 97; EDGE 95
- FVG same/any 0/67
- Exec FVG 67
- <=8ATR 18
- RelVol pass 7
- Structural risk pass 3
- 2R room 3
- Orders 3
- Ledger closed 3
- Visible position fills/closes 2/2
- Invisible same-bar round trips 1
- 1H created bull/bear 70/39
- 4H created bull/bear 22/6
- First-valid-bar FVG touches 8

## Interpretation
Execution smoke path is now working end-to-end, including one same-bar round trip correctly captured by the ledger.

The next implementation-risk item is timeframe boundary alignment. alpha1.1 hand-built 5m/1H/4H bars using UTC epoch arithmetic. That can disagree with TradingView/exchange session alignment, especially 4H futures bars, and therefore alter FVG creation and RelVol timing.

## alpha1.2 change
No strategy rule or threshold changes.

Only aggregation boundary identification changes:
- 5m: `time("5")`
- 1H: `time("60")`
- 4H: `time("240")`

OHLCV remains manually accumulated from 1m bars and only completed aggregates are used.

This is a translation/alignment correction, not optimization.

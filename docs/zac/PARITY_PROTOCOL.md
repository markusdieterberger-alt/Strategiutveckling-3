# ZAC-01 parity protocol

## TradingView test environment
- Symbol: MNQ1!
- Standard candles
- Timeframe: 1 minute
- Deep Backtest: 2019-05-05 → 2026-10-02
- Mode: REFERENCE

## Module isolation
Test one module at a time.

### C4
- C4 ON
- Prime OFF
- ZAB OFF

Reference fingerprint:
- ALL: ~376 trades
- PF ~2.04
- Exp ~+0.53R
- 2025–26: n105 / PF ~2.83

## Current parity state
v1.1 isolated the break at:
RAW ~114 → Displacement ~95 → Directional FVG 0.

v1.2 is a diagnostic implementation. It must not be treated as a promoted strategy variant.

## Rule
Do not retune thresholds to force parity. Diagnose implementation semantics first.

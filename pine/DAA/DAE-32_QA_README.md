# DAE-32 – VA Close Breakout (5m confirmation + VA limit retest)

## Delivered
A single Pine v6 strategy `DAE-32_VA_CLOSE_BREAKOUT_5M_RETEST.pine`, separate branch so DAE-31 and CT V1/V2 are untouched.

**Choose `Entry Level = VA Close Breakout`. Default remains VA Far.**
- LONG (CRT direction long): wait until a fully completed 5-minute candle closes **strictly ABOVE the currently calculated dynamic value area high (VAH)**. Submit a **buy-limit at that VAH** after confirmation, filled only at the level or better on later eligible minutes.
- SHORT (CRT direction short): wait until a fully completed 5-minute candle closes **strictly BELOW value area low (VAL)**. Submit a **sell-limit at that VAL** for the retest.
- If close is equal to VAH/VAL, no breakout. No entry on the 5m-candle wick alone. No entry on a still-developing 5m candle. The value area is recalculated on the closed 1m bar used to confirm the 5m close, then frozen on order submission.
- The order is ALWAYS a limit, ignoring the independent Entry Order Mode selection in breakout mode only. Other modes VA Far / VA Close / POC preserve their DAE-31 behavior.
- The standard nearest qualifying FVG boundary remains TP; existing RR-stop, initial USD cap, BE percentage, fixed/trailing stop, setup expiry, pending cancellation and Sweden local 05–14/16–22 sessions remain.
- An unfilled entry limit is cancelled when its profile becomes inactive or its trading session closes.
- A blue `5m BRK` chart marker shows a confirmed 5m breakout and limit submission.

## Execution and accounting
- 1m TradingView chart: official native strategy ledger, subject to TV bar emulator behavior.
- Real 5m/30m TradingView chart: same one-file DAE shadow 1m simulator with a synthetically reconstructed 5m candle-close condition. This is **NOT** a direct read of the 1m native TradingView fill ledger. Exact cross-TF PnL parity remains UNVERIFIED.
- Shadow fills order on a later 1m candle when the VA limit is reached. Same-minute OHLC stop/TP ambiguity remains conservatively stop-first; gaps can alter fills. Some history/coverage or other pre-existing model differences may remain.

## Static QA
- Checked Pine v6 first-line, single strategy declaration, balanced brackets/strings and no duplicate global declarations.
- Verified both native 1m 5m-close filter and shadow 1m 5m-close filter are present, directional strict close tests, forced limit orders, unchanged default and risk/session/BE functionality.
- Case tests (independent arithmetic reference) pass: long 5m close above VAH, short below VAL, equal or inside ignored, unfinished 5m candle ignored, terminal session minutes disallow a new pending order.
- **Not tested in TradingView Pine Editor or Strategy Tester.** Compilation, historical forwardfill, dynamic volume profile persistence, actual trade parity, and robustness must be proven before any live/funded use.

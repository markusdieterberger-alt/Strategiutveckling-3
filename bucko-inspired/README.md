# BUCKO INSPIRED V1 — MGC 5m (original research)

Independent Pine v6 prototype inspired by **visually observed** characteristics (LONG/SHORT labels, graded signals, colored trend ribbon). **NOT Bucko Terminal ULTRA source code or verified replication.** Do not market or label it as genuine Bucko.

## Frozen signal rules
- Plot EMA 9 / 21 / 50 / 200. Directional trend is **mandatory**: 9 > 21 > 50 and close > EMA200 for long (inverse for short).
- RSI(14) >= 52 for longs / <= 48 for shorts, ADX(14) >=18, directional DI confirmation = momentum check.
- Relative volume = current volume / SMA(volume,20) >=1.1.
- A structural trigger requires close breaking the **prior five completed bars'** high/low, on a confirmed candle close; second condition blocks persistent repeated breakout labels.
- Score 3 (A+), 2 (A), 1 (B) over trend/momentum/volume checks. Trend mandatory; default minimum score A. Thresholds **hypotheses** not fitted to returns.
- ATR(14) x1.5 initial stop, RR 2 default. Strategy RR menu 1,2,3. One trade max at a time. Next-bar market fills, $1 per side per contract and 1 tick per order assumed. Verify broker costs.
- Exit policies: Fixed, break-even after **closed-bar** +1R, or trail once **closed-bar** profit >=2R by 1R from best close. Close-based updates avoid assuming that an intrabar extreme occurred before another fill.

## Validation status
- Pine text committed to repository, files verified present. **Not compiled in TradingView** or backed by MGC 5m bars yet. No reported P&L, PF, passrate or trade count.
- Strategy broker emulator assumptions are NOT real-world intrabar/tick/prop-firm parity. Default protective bracket is installed after the initial entry position is observed by script; review this exposure before any live testing.
- Prefer fixed train/holdout periods, document full trade export, verify session/timezone & futures symbol/roll history, commissions, slippage, intrabar ambiguity and paper trade behavior.
- Original CT Scalper and other strategies unchanged.

## Files
- BUCKO_INSPIRED_V1_INDICATOR.pine (visual signals and signal alerts)
- BUCKO_INSPIRED_V1_STRATEGY.pine (testing only; no live order bridge)

# DAE-33 – Market entry at confirmed 1m or 5m VA breakout close

**One Pine v6 `strategy()` source:** `DAE-33_VA_BREAKOUT_MARKET_1M_OR_5M_CLOSE.pine`.

## New settings

- **Entry Level → VA Close Breakout Direct**: new market-entry mode; alternative to the prior `VA Close Breakout` 5m-then-limit-retest. Legacy `VA Close`, `VA Far` and `POC` remain. **Default remains VA Far**, so select Direct explicitly.
- **DAE-33 Direct Breakout → Direct breakout confirmation candle → 5m or 1m** (default **5m**).
- Confirmed LONG: signal direction LONG + the close of the selected 1m/5m candle is **strictly above the current dynamic VP VAH**.
- Confirmed SHORT: signal direction SHORT + close strictly **below current VAL**.
- No wick-only confirmation; equal price at the edge fails. A fully closed 5m bar is the 1m bar ending at the 5m boundary; no 5m lookahead.
- In Direct mode, the entry PRICE is **the qualifying 1m close**, not the VAH/VAL. TP is still the nearest valid FVG boundary in the favorable direction, if available. Stop derived from RR and max risk per micro. No pending VA-limit order or retest.
- On a native 1m chart the strategy declaration uses `process_orders_on_close=true`, so **TradingView's historical broker emulator can simulate immediate market fills on the confirming 1m bar close**. For 5m confirmation, this is the final 1m close of that 5m candle. This setting is global and **may also change fills in the other entry modes** relative to DAE-32. It does not guarantee a real broker can fill at the historical closing price.
- On a real 5m/30m chart the one-file code uses a separate 1m **SHADOW** emulator. It opens the synthetic position at the 1m `cc` on the confirmation minute (no in-candle retrospective exit), annotating `1m MKT` / `5m MKT`. **This is not the native 1m Strategy Tester ledger, and parity remains unverified.**
- DAE-31 session rules **Europe/Stockholm 05:00–14:00, 16:00–22:00**, pending cancellation, forced flat, BE on/off default 70% of TP (yellow), 1:1/1:1.5/1:2/2:1/3:1 RR, VA Far default, max initial risk 600 USD per contract and all previous visual marks remain.
- If TP boundary is unavailable in the direction of the direct breakout, **no trade**; never generate an invalid target. Existing setup mitigation/expiry restrictions also remain.

## Static source QA

GitHub readback confirms Pine `//@version=6` first line, one strategy, balanced delimiters/strings, no duplicate globals, 10 plotshape calls, both directional guards and confirmation selectors present, native market entry calls without `limit` or `stop`, shadow immediate-close fills, sessions, BE and risk constraints unchanged. Small scenario logic checks confirmed only final minute of 5m candle qualifies in 5m mode and each confirmed 1m candle can qualify in 1m mode.

## Status

**Development only.** Neither authenticated TradingView Pine compilation nor historical trade matching / forward parity has been performed. Compare at least 20 matched entry/exit events between native 1m and higher-timeframe shadow before using performance numbers. Keep CT V1/V2 active files and alerts unchanged.

Reference on bar-close simulated fills: https://www.tradingview.com/pine-script-docs/concepts/strategies/

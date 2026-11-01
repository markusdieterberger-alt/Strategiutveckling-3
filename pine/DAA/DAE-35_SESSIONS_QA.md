# DAE-35 — configurable session groups, saved DAE-34 baseline

One standalone Pine v6 strategy source: `DAE-35_ASIA_NY_ALL_HOURS_CONFIGURABLE.pine`.

## New inputs (DAE-35 Trading Hours | Sweden Time)

| Switch | Default | Editable hours |
| --- | --- | --- |
| **Trade ALL available hours** | Off | Overrides all toggles, enables every data-bearing minute |
| ASIA night | Off | 22:00–05:00 (overnight) |
| ASIA/morning | **On** | 05:00–14:00 |
| Pre-NY | Off | 14:00–16:00 |
| NY opening | **On** | 16:00–22:00 |

All time ranges use `input.session`, so individual start/end times can be edited in TradingView Settings → Inputs. Always interpreted in **Europe/Stockholm**, automatically adjusting for Sweden daylight saving time. Group labels (Asia, NY) are operational names for selectable intervals, not claims about the precise local exchange cash-session opening; the actual clock range is authoritative.

With defaults, the original DAE-34 05–14/16–22 strategy rules are reproduced. With all-hours enabled, the filter allows every *available* 1m candle. **This does not create data/fills when CME is closed, and does not extend the loaded 1m history.** A position open when a selected session ends is forcibly closed and pending orders are cancelled (as in DAE-34); when enabled sessions are consecutive, the position can continue across their boundary.

## Saved user settings retained as DAE-35 defaults

Compared with DAE-34's code defaults, these have been set to the observed user-approved screenshot state: Entry Level = VA Close Breakout Direct, confirmation = 1m, RR 1:1.5, fixed SL, initial USD risk cap $400, BE Off (threshold 95% stored), lookback 3000 completed 30m bars, visible zones 30, and performance dashboard Bottom Left. All other DAE-34 controls and native / SHADOW simulator logic remain.

Reference screenshot result from DAE-34: **21 trades, 12W/9L, 57.1% win rate, PF 2.44, +251 USD net, $74.50 max closed-trade DD, average $11.95**. This is **not** a DAE-35 backtest result and cannot be extrapolated to enabled Asia night or 24h operation.

## QA and restrictions

- GitHub source readback verifies `//@version=6`, one `strategy()`, no duplicate globals, balanced braces/strings, shared f_inTradeHours for 1m native order filter and 5m/30m shadow engine.
- 16 test cases pass for default windows, boundary minutes (13:59, 14:00, 16:00, 21:59, 22:00), overnight wrap, contiguous NY+Asia, all-hours override, and no-session mode.
- **TradingView Pine compiler and native-to-shadow trade parity not verified**. Do not claim actual historical performance or live suitability.
- 30m dashboard remains a separate 1m SHADOW simulation; it is not native 1m Strategy Tester data.
- DAE-34 and active CT V1/V2 alerts remain unmodified.

# DAE-36: selectable CRT + FVG timeframe (30m / 1h / 4h)

**One Pine v6 strategy script:** `DAE-36_SELECTABLE_CRT_FVG_30M_1H_4H.pine`.

## User instruction and implementation

**Settings → Inputs → `DAE-36 CRT/FVG Source` → `CRT + FVG setup timeframe`**:
- **30** (30 minutes) = default / prior DAE-35 setup source.
- **60** (1 hour) = requires both **1-hour CRT + 1-hour FVG**.
- **240** (4 hours) = requires both **4-hour CRT + 4-hour FVG**.

The selected timeframe drives **the complete setup/signal source**: prior-bar CRT sweep-and-close-inside, nearby 3-candle FVG, zone geometry, the creator bar and time/mitigation of the active VP. The FVG nearest-boundary TP therefore also derives from **the selected setup timeframe**. No cross-mixing of 30m CRT and 1h FVG in the same test.

**Entry/timeframe remains independent:** Existing DAE-35 entry-method dropdown unchanged (VA Far, VA Close, POC, 5m confirmed limit retest and 1m/5m confirmed **Direct** breakout); VAH/VAL/POC calculated from chronological **1m profile data** regardless of setup TF. Previous user baseline defaults retained: VA Close Breakout Direct, 1m confirmation, RR 1:1.5, USD400 initial risk, fixed stop, BE disabled at saved 95% threshold, session defaults 05–14 +16–22 Europe/Stockholm, with Asia night/pre-NY/all hours individually selectable. The performance dashboard remains and displays source/setup timeframe.

## Technical QA

- Native on chart **1m** uses a single consistent `input.timeframe()` choice for all 11 `request.security` higher-timeframe expressions. Only `high[1]`, `low[1]`, `close[1]`, `high[2]`, `low[2]`, `high[3]`, `low[3]`, `time[1]` values are used in CRT and FVG, with `lookahead_on` on **confirmed** setup bars. `time` identifies the new setup bar (not signal price), avoiding future HTF OHLC.
- Larger 500-minute native/shadow rolling creator cache supports the full previous **240-minute** setup bar when profile is activated. Adjusted the lookback expiry to `lookbackBars * timeframe.in_seconds(setupTf) * 1000`. The 3000 setting is now measured in **selected setup bars**, not hard-coded 30m.
- On actual chart **5m, 30m, 1h, 4h**, the one script uses the pre-existing **1m SHADOW simulator**, now with configurable 30/60/240-minute HTF aggregation based on `time(setupTf)` inside `request.security_lower_tf`. Unlike dividing epoch millis by 4h, this follows the exchange/chart session's HTF candle start dates and avoids avoidable UTC-anchor drift. TP/SL/entries are still computed within 1m shadow bars rather than the higher chart candle.
- Tested the 3 choices for source selection and 500-minute creator cache coverage; 16 static QA checks PASS (Pine v6 header, single declaration, balanced delimiters, no duplicate global definitions, 11 HTF references all using chosen input, same native strategy entry order-call count and original user parameters).

## Important constraints

1. **1m chart** is the reference native TradingView strategy tester; the actual **30m / 1h / 4h chart** uses a **separate 1m SHADOW calculation**, and its results are **NOT guaranteed** to match native 1m orders. The difference between source setup TF and chart TF matters.
2. A 1h or 4h CRT is only known **after its candle closes**; entry logic may then act on subsequent 1m/5m candles, never before confirmation.
3. On 4h source, a 4h candle may straddle a selected trading session. Signal creation is gated by enabled sessions, and there are no fills outside chosen sessions. This is intentionally retained from DAE-35.
4. There is **no authenticated Pine Editor compile or TradingView fill-by-fill QA** yet for DAE-36. The code is **RESEARCH / NOT LIVE-APPROVED**. Compare ≥20 native 1m trades vs shadow at chosen TF per case before relying on displayed PF or funded pass likelihood.
5. This version changes ONLY a branch/new file. DAE-35, DAE-34, CT Scalper V1/V2 and active alerts remain untouched.

Pine reference: https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/

# DAE-34 — user settings & observed TradingView result (2026-11-01)

**Source:** Six user-supplied screenshots, around 06:49 Europe/Stockholm on 2026-11-01. Preserve as a fixed user-accepted research checkpoint. **These are observed screenshots, not independent backtest verification.** The user explicitly requested remembering the values and testing a substantially longer period.

## Current visible configuration (not necessarily source defaults)

| Group / Control | Screenshot value |
|---|---|
| Chart symbol / tested timeframe | MNQ1! / 1m |
| Strategy | DAE-34 |
| Lookback (completed 30m bars) | 3000 |
| Maximum visible zones | 30 |
| Bullish FVG / bearish FVG | visually muted teal / red; exact color code not readable |
| Show 30m CRT arrows | On |
| Maximum CRT arrows | 400 |
| CRT arrow color | Purple; exact RGB not readable |
| DAD VP rows | 60 |
| DAD value area | 0.70 (70%) |
| DAD max 1m candles | 4000 |
| DAD histogram maximum width | 45 minutes |
| DAD histogram / value area histogram / POC | Gray / muted from screenshot; exact RGB not readable |
| Blue setup arrows (30m CRT + FVG) | On |
| Green TP / red SL fill markers | On |
| Entry Level | VA Close Breakout Direct (dashboard label/preceding discussion; dropdown itself truncated) |
| Position box width | 2 hours |
| Max historical position boxes | 60 |
| Direct breakout confirmation candle | **1m** |
| Entry Order Mode | Auto (irrelevant to direct-market breakout mode) |
| Risk:Reward (FVG target fixed) | **1:1.5** |
| Stoploss mode | **Fixed** |
| Enable Take Profit | On |
| Trailing activation | 20 ticks (inactive for Fixed stop mode) |
| Trailing distance | 20 ticks (inactive for Fixed stop mode) |
| Maximum initial risk per contract | **400 USD** |
| Enable Break Even | **Off** |
| BE when % of TP reached | 95% (inactive because BE is Off) |
| Yellow BE activation and exit marks | On (does not activate BE by itself) |
| Show EXTRA date-window dashboard | Off |
| Extra From (UTC) | 2026-08-26 00:00 |
| Extra To (UTC; exclusive) | 2026-10-05 20:30 |
| Extra dashboard location | Top Left |
| Shadow round-trip commission per 1 MNQ | 1 USD (shadow settings, not the active native 1m mode) |
| Shadow blue setup arrows | On |
| Shadow entry marks | On |
| Shadow TP/SL marks | On |
| Shadow event label limit | 450 |
| Show PERFORMANCE DASHBOARD | On |
| Dashboard location | **Bottom Left** (seen on chart; selector truncated as 'Bottom...') |
| Dashboard font size | **Normal** |
| Sessions | 05:00–14:00 and 16:00–22:00 Europe/Stockholm (from DAE-34 code; not a screenshot input) |

## Observed 1m NATIVE dashboard — fixed checkpoint

| KPI | Value |
|---|---:|
| Win rate | **57.1%** |
| Profit factor | **2.44** |
| Net Profit | **+251 USD** |
| Closed trades | **21** |
| Wins / losses | **12 / 9** |
| Gross Profit | **425 USD** |
| Gross Loss | **174 USD** |
| Average / trade | **+11.95 USD** |
| Max closed-trade drawdown | **74.5 USD** |
| Session exits | **0** |
| Dashboard period | **'Loaded history'** – actual first/last timestamp not shown |
| Validation | 'TV TESTER', meaning native 1m strategy result, not a complete parity endorsement |

**Critical interpretation:** A user-selected EXTRA date window (Aug 26–Oct 5) exists, but that dashboard is **OFF**. It does **not** define the performance dashboard's period. Do not assign the 21 trades to those dates. The chart at screenshot is around October 30–November 1, but the exact loaded calculation range is NOT shown. The 21-trade result is an exploratory short-horizon checkpoint; **NOT statistically representative, not QA/live-approved**.

## User-requested next action: much longer test

- Preserve the configuration above unchanged for baseline comparison.
- Prioritize backtest on at least 12 months MNQ 1-minute data (available in project uploads: MNQ 1m MASTER approx 2025-10-01 to 2026-10-01; source/data continuity must be verified). When possible extend to multiple years, including different regimes. Historical data must align to actual contract rollover and costs.
- **TradingView standard chart 1m history is plan limited**; selecting 'Lookback 3000' is NOT increasing strategy-history bars. According to TradingView documentation, Essential/Plus chart limit ~10,000 intraday bars. Deep Backtesting (Premium+) processes more history but reports trades only in Strategy Report, not chart overlay.
- A Python reference backtest using 1m CSV data is a practical route, BUT full DAE-34 execution parity is NOT implemented or verified as of this checkpoint. Do not claim the longer period has already been tested.
- Crucial validation: compare identical first 20+ trade entry/exit pairs against TradingView native 1m before trusting extended Python performance. Include BE Off, RR=1:1.5, USD riskcap400, fixed stop, selected direct 1m breakout and Europe/Stockholm sessions.
- No changes to CT V1/V2 or active trading alarms.

TradingView source pages:
- https://www.tradingview.com/support/solutions/43000480679-historical-intraday-data-bars-and-limits-explained/
- https://www.tradingview.com/support/solutions/43000666265-how-deep-backtesting-works/

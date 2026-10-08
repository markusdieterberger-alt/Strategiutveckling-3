# PINE_SHADOW_RUNTIME_v1 — Execution contract

Status: SHADOW-CANDIDATE  
Purpose: emulate the TradingView/Pine historical strategy semantics used by ZAC closely enough to perform automated parity work before final TradingView verification.

## Why "candidate" and not "exact"

TradingView's runtime and broker emulator are proprietary. Official documentation defines most behavior needed by ZAC, but not every internal edge-ordering rule. Therefore exactness is split into two classes:

### A. Documentation-locked behavior
Implemented directly from current TradingView documentation:
- strategies execute once per historical bar at close under default calculation settings;
- with process_orders_on_close=false, newly created orders have a one-tick delay and earliest fill is the next available tick;
- market orders fill on the next available tick;
- limit orders fill at their requested price or a better price;
- marketable limit orders can fill at the next available tick;
- slippage applies to market and stop orders, not normal limit fills;
- backtest_fill_limits_assumption requires price to move beyond the requested limit while preserving fill at requested limit;
- historical broker emulation uses an OHLC/OLHC intrabar path;
- cash-per-contract commission is charged on both entry and exit;
- strategy.close(..., immediately=true) can fill on the current closing tick.

Official references:
- https://www.tradingview.com/pine-script-docs/language/execution-model/
- https://www.tradingview.com/pine-script-docs/concepts/strategies/
- https://www.tradingview.com/pine-script-docs/language/declaration-statements/
- https://www.tradingview.com/support/solutions/43000628599-strategy-properties/
- https://www.tradingview.com/support/solutions/43000786181-broker-emulator/
- https://www.tradingview.com/pine-script-docs/concepts/time/

### B. Calibration-locked behavior
Must be compared against TradingView before the runtime can be called TV-CONFORMANT:
- equal-distance OHLC/OLHC tie case;
- exact order priority if multiple eligible orders share the same intrabar price;
- exact mutation semantics when an existing pending order ID is modified;
- exact session alignment of time("240") on MNQ1! for all holidays/short sessions;
- any behavior affected by user-side Strategy Properties overrides;
- data differences caused by TradingView MNQ1! continuous-contract roll construction.

## Frozen ZAC runtime profile

The initial conformance target is intentionally narrow:
- standard 1m MNQ chart;
- historical bars;
- process_orders_on_close=false;
- calc_on_order_fills=false;
- calc_on_every_tick=false;
- pyramiding=0;
- no Bar Magnifier;
- one active portfolio position;
- integer quantity;
- market entries, resting limit entries, stop orders;
- strategy.exit stop+limit bracket;
- strategy.cancel;
- strategy.close / close_all;
- fixed 1-tick slippage;
- $0.50 commission per contract per side;
- limit verification 0 unless explicitly changed.

Unsupported features are not silently approximated. They must raise or be implemented in a new runtime version.

## Historical bar lifecycle

For each bar:

1. Existing eligible market orders process on the open tick.
2. Existing price-dependent orders are checked at open.
3. Remaining intrabar path is processed using TradingView OHLC/OLHC assumptions.
4. Existing brackets can become active after their entry fills and can close the position later on the same historical bar.
5. Pine strategy logic executes once at bar close.
6. Orders created by that close execution become eligible on the next tick/bar because process_orders_on_close=false.

This ordering is central to reproducing invisible same-bar round trips observed in TradingView.

## Slippage

RuntimeConfig.slippage_ticks is applied:
- BUY market/stop: fill + ticks*mintick
- SELL market/stop: fill - ticks*mintick
- normal limit fills: no adverse slippage

## Limit verification

If backtest_fill_limits_assumption_ticks = N > 0:
- BUY limit must trade N ticks below requested price;
- SELL limit must trade N ticks above requested price;
- recorded fill remains the requested limit price.

## Trade ledger

ClosedTrade is the shadow equivalent of strategy.closedtrades.

Parity comparisons should be performed trade-by-trade using:
- entry ID
- direction
- entry bar/time
- entry price
- exit bar/time
- exit price
- quantity
- exit reason
- gross/net PnL

PF is a final checksum, not a debugging primitive.

## Timeframe boundaries

SessionAlignedClock exists only as a configurable shadow of TradingView time(tf).

TradingView documents that timeframe bars align to the symbol session and exchange timezone. The exact MNQ1! 4H timestamps will be frozen through the conformance harness. Until then, session-aligned 4H boundaries are a candidate implementation, not a declared exact clone.

## Promotion gate

PINE_SHADOW_RUNTIME_v1 becomes TV-CONFORMANT only when:
1. unit tests pass;
2. calibration Pine harness produces matching fills/order timing on the same TradingView bars;
3. no unresolved ZAC-used edge case remains;
4. at least one C4 trace window matches event-by-event before Strategy Tester aggregate comparison.

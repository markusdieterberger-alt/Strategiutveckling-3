# PINE_SHADOW_RUNTIME_v1

A contract-focused historical TradingView/Pine strategy shadow runtime for the ZAC project.

## Exactness statement

This is not a Pine parser and cannot prove bit-for-bit identity with TradingView's proprietary runtime from documentation alone.

The target is stronger and more useful for this project: reproduce the documented TradingView historical strategy semantics used by ZAC, then lock remaining edge cases with a TradingView conformance suite.

Until the conformance suite passes, status is SHADOW-CANDIDATE, not TradingView exact.

## Implemented in v1

- historical once-per-bar-close strategy execution
- one-tick order delay / next-bar eligibility
- market, limit and stop orders
- strategy.exit stop+limit brackets
- same-bar entry/exit round trips
- TradingView historical OHLC/OLHC path assumption
- better-price limit fills at bar open
- limit-price verification
- fixed slippage on market and stop orders
- cash-per-contract commission
- strategy.cancel
- strategy.close / close_all including immediately=true
- strategy.closedtrades-equivalent ledger
- session-aligned timeframe helper
- deterministic pytest conformance tests

## ZAC execution profile

- standard 1m bars
- process_orders_on_close=false
- calc_on_order_fills=false
- calc_on_every_tick=false
- pyramiding=0
- slippage=1
- limit verification=0 unless explicitly changed
- commission=$0.50/contract/side
- MNQ mintick=0.25
- MNQ point value=$2.00

Current local verification at creation: 8/8 tests PASS.

TradingView remains the final oracle for undocumented edge ordering, exact equal-distance OHLC/OLHC tie behavior, exact symbol/session higher-timeframe boundaries, and data differences between TradingView MNQ1! and the Databento canonical series.

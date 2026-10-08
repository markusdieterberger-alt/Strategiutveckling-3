# TradingView conformance plan — Pine Shadow Runtime v1

## Goal

Turn SHADOW-CANDIDATE into TV-CONFORMANT for the exact Pine subset used by ZAC.

## Calibration sequence

1. Market order created at bar close -> next bar open.
2. Market slippage long/short.
3. Resting buy/sell limit touched intrabar.
4. Limit gapping through requested price -> better open fill.
5. Verify-price-for-limit-orders = 1 tick.
6. Stop order touched intrabar.
7. Stop order gapping through level.
8. Entry + stop same historical bar.
9. Entry + target same historical bar.
10. Both stop and target inside one historical bar; verify path ordering.
11. strategy.cancel before subsequent touch.
12. strategy.close immediate=false.
13. strategy.close immediate=true.
14. strategy.exit bracket created before entry fill.
15. 5m/60m/240m time() boundary timestamps around:
   - normal CME session;
   - DST transition;
   - Sunday reopen;
   - early-close holiday.

## Evidence format

The Pine harness logs machine-readable rows:

CASE|timestamp|bar_index|entry_id|entry_price|exit_price|closedtrades|position_size

Those rows are compared directly to shadow runtime output.

## Acceptance

Zero unexplained differences for all ZAC-used cases.

Any difference creates:
- one isolated regression test;
- one runtime version bump;
- one documented reason.

No ZAC signal threshold may be changed to compensate for broker-runtime mismatch.

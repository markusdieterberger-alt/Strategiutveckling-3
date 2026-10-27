# EAA CT Scalper V2 - isolated research, 2026-10-27

Status: **REVISE / native verification pending**. No live/funded approval.
This directory is additive. Do not replace, edit, restart or delete the active V1 or its alerts.

- `reference/EAA_CT_SCALPER_STRATEGY_V1.pine`: byte-frozen source, SHA256 `c386f4f7d3e30e3ebfe57ebe5e35e40c5560fda88b7f38296405d080ebbcf8e8`.
- `pine/EAA_CT_SCALPER_V2_DEV.pine`: fixed confirmed-HTF candidate, unique order IDs, immutable order-intent JSON and native observations.
- `pine/EAA_CT_DIAGNOSTIC_V1_V2.pine`: isolated diagnostic copy. Default HTF=LEGACY. Change ONE tested input/property per comparison.
- `build_v2.py` and `templates/`: deterministic derivation; original six entry models, shared filters and price functions are preserved.
- `diff/`: exhaustive source differences. Internal pattern shapes and the separate counterfactual stress ledger are removed; native TV remains the only trade book.
- `qa_tools.py`: reconciles exported JSONL order-fill messages. Synthetic examples are not historical CT signals.

Rebuild and local checks (Python standard library, 3.10+):

```sh
python3 build_v2.py
python3 -m unittest -v test_qa
python3 qa_tools.py operator_alerts.jsonl --out private_results
```

All V1 signal inputs, calculation defaults and test dates are preserved. **The inherited default test end is 9 October 2026.** For a new comparison, the operator must explicitly set and record identical test dates on the isolated copies. An expired date gate is not an alert failure. Do not edit the active V1 to obtain matching dates.

V2's 5/15/60/240m values use previous completed HTF bars, with the historical offset inside `request.security` and `lookahead_on`. The last 1m bar ending at an HTF boundary still uses the older value; the next 1m bar uses the newly completed HTF bar. This is a deliberate timing change, not V1 signal parity. External feeds, footprint reconstruction, roll adjustments and initialization can still change after reload.

V2 fails visibly on intrabar or repeated execution of the same bar. Properties must keep On every tick, After order is filled and On bar close execution OFF (orders at next available tick; `process_orders_on_close=false`). The diagnostic copy can observe alternate modes; it does not certify them.

One native position at a time; qty input default 1; SL/TP submitted with the entry and frozen. Stops may fill beyond their intended levels. Bar Magnifier and 1m OHLC do not establish real tick-path parity. Calendar/holiday or absent-last-bar force-flat remains a known limitation. Footprint guard is the original 11 observed non-na bars, not a resolution guarantee or an elapsed-minute continuity check.

For an operator-authorized new V2 alert, use a unique name (suggestion `CT_FORWARD_V2_QA_200_ORDER_LOG`), **order fills only**, and the exact `alert_order_fills_template.txt`. No webhook. `strategy.order.price` is supplied only by TV at fill, outside the intent payload; nested placeholders are not used. Diagnostic `alert()` calls are explicitly `DIAGNOSTIC_NOT_A_TRADE`, default OFF, and belong in a separate diagnostic alert. Creating alerts is a separate operator activation step.

Full private evidence, decision and operator checklist are delivered to the project inbox. Public repo contains code and synthetic QA only, no private order logs, screenshots, price data or account books. Native compile evidence and final statuses will be added in `QA_STATUS.json`; local tests alone never establish a native PASS.

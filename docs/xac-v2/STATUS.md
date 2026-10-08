# XAC v2 rebuild status

## A4 — alpha1.1
Mobile smoke-test: PASS.

Observed chart-history QA:
- 30m closed: 852
- CRT: 264
- Attached: 45
- Sweep 10–19: 17
- Recovery >=60%: 13
- Legacy time window: 4
- Qualified A4: 4 (1 long / 3 short)
- Cancelled by near-touch: 2
- HH/LL confirmations: 2
- Orders: 2
- Fills: 2
- Closed: 2

Execution marks were visibly rendered on mobile. This proves the clean A4 implementation reaches TradingView order/fill/exit state. It does NOT yet prove full historical parity.

## IB — alpha2
New isolated rebuild added.
Awaiting mobile compile/dashboard/execution-mark QA.

## Next
After IB smoke-test:
IBT isolated rebuild → POC isolated rebuild → Scalp isolated rebuild → combined router.

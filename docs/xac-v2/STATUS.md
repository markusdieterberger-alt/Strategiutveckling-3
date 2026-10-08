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


## IB — alpha2 mobile smoke-test
Observed chart-history QA:
- Days: 20
- IB built: 19
- Raw false-break H/L: 66/76
- First H/L: 15/16
- Volume passes: 6
- Orders: 5
- Fills: 5
- Closed: 5
- PF on visible chart-history: 4.149

Status: execution smoke-test PASS. One diagnostic discrepancy remains: Vol pass 6 vs Orders 5. This is not treated as parity failure yet; alpha2 did not separately expose qty=0 / position-block cause. Do not infer canonical parity from PF.

## IBT — alpha3
Isolated rebuild added with explicit candidate-before-volume semantics and counters for qty-zero / blocked-position.
Awaiting mobile QA.


## IBT — alpha3.1 mobile execution QA CONFIRMED
Observed:
- Strategy Tester closed: 9
- Orders: 9
- Ledger closed: 9
- Position fills: 5
- Position closes: 5
- Invisible RT: 4
- Qty0: 0
- Blocked pos: 0

Conclusion:
Four IBT trades are same-bar historical round trips that are invisible to simple position_size transition counters. For Pine parity diagnostics, strategy.closedtrades delta must be tracked alongside position transitions. This is now a required translation rule for all later modules.

## POC — alpha4
Isolated rebuild added.
Important explicit parity issue: intended Python stop geometry uses actual next-open -> POC distance, while Pine must choose order quantity before next open is known. alpha4 therefore:
- submits market order using provisional signal-close sizing,
- recomputes active stop from actual fill price,
- logs fill drift >= 1 tick,
- keeps this mismatch visible rather than silently treating it as canonical parity.
Awaiting mobile QA.


## POC — alpha4 mobile smoke-test
Observed:
- Days 20
- Profiles 1671; ATR ready 1692
- Raw magnets / first daily candidates: 19
- Candidate L/S: 12/7
- Trend pass: 7
- Orders: 4
- Position fills: 4
- Ledger closed: 4
- Invisible RT: 0
- Qty0: 3
- Fill drift >= 1 tick: 3
- Visible chart-history PF: 1.803

Interpretation:
Execution path works. Three of seven trend-qualified candidates produced qty=0 under $120 provisional signal-close sizing. Three of four actual fills differed from signal close by >=1 tick, confirming that next-open geometry is a real Python→Pine parity issue for this component. Preserve this as an explicit unresolved parity item; do not hide or retune it.

## Scalp — alpha5
Isolated 75m VAH trailing scalp rebuild added using preserved source ordering:
profile includes current completed 5m rejection bar; entry minute excluded from trailing; low-water begins at actual fill price; 30m cooldown from ledger exit time.
Awaiting mobile QA.

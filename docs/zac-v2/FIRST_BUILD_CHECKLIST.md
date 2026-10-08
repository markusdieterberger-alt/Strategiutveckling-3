# ZAC v2 — First-build checklist

## Before writing C4 Pine
- [x] A001 read/current
- [x] A003 updated/current
- [x] ZAC freeze reviewed
- [x] D00054 reviewed
- [x] D00053/D00052 lineage reviewed
- [x] preserved DS180 Python helper reviewed
- [x] D00055 reviewed
- [x] AMT canonical report reviewed
- [x] D00064 reviewed
- [x] prior ZAC parity report reviewed
- [x] prior Pine failure modes reviewed
- [x] XAC lab translation lessons captured
- [x] GitHub branch `zac-v2-rebuild` established

## C4 implementation must contain on day one
- [ ] margin_long=0 / margin_short=0
- [ ] real strategy.entry/exit
- [ ] strategy.closedtrades delta ledger
- [ ] same-bar invisible RT counter
- [ ] manual completed 5m volume engine
- [ ] manual completed 1H/4H FVG engine
- [ ] true interval-overlap prune
- [ ] first-valid creation timestamp
- [ ] raw DS180 levels without tick rounding
- [ ] executable order levels separate from raw levels
- [ ] exact prior-20 denominator for completed 5m RelVol
- [ ] localized displacement semantic switch/diagnostic
- [ ] localized pending-fill conflict policy
- [ ] qty=0 / blocked / invalid / expiry counters
- [ ] compact mobile dashboard
- [ ] explicit own execution markers
- [ ] embedded fingerprints and version identity

## Do not add yet
- [ ] Prime
- [ ] ZAB
- [ ] router
- [ ] funded blocks
- [ ] webhook
- [ ] parameter tuning

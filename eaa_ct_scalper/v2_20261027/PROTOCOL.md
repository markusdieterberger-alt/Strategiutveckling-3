# Frozen technical QA protocol — EAA CT V2 2.0.0

No performance optimization, new signal filter or promotion is authorized here. No active V1 instance or alert may be edited. Public fixtures are synthetic, not historical CT trades.

## Identity and inputs

Freeze source bytes, Git commit, all Inputs and all effective Strategy Properties for EACH isolated instance. The source-default inventory is `LOCKED_INPUTS.json`; it is not an export of an active server snapshot. Record exact exchange-prefixed ticker, standard candles, timeframe, chart timezone, session, contract adjustment/roll settings, data entitlement/delay, loaded first/last bar, date window, margin, capital, sizing, commission, slippage, limit verification, Bar Magnifier and three calculation/fill options. Record creation UTC and unique alert name.

Default date end is expired. For new research, set the same operator-declared start/end on both isolated copies before creating any authorized new alert. Keep the current V1 untouched. Source identity of an existing server alert cannot be inferred from code opened in the chart later.

## Controlled comparisons, in order

1. **D0 baseline identity:** diagnostic copy, `ONLY intervention: confirmed HTF=false`, identical source inputs/properties/feed/window to a separately saved V1 copy. Compare native order times/prices/model/SL/TP/exit before attributing later differences to HTF. Unique IDs and labels differ by design. D0 has NOT been run natively.
2. **D1 HTF only:** same diagnostic instance settings and synchronized data; toggle only confirmed HTF. Export all QA fields at closed 1m bars around 5/15/60/240m boundaries, including `KnownClose <= chart open`. Compare first divergent candidate, then gate, submit, native fill and exit. V2's HTF delay is deliberate, so identical V1 trades are not the success criterion.
3. **D2 footprint gate only:** using LEGACY diagnostic copies, change only existing `Require 11 consecutive footprint bars` true/false; do not change footprint request or inject OHLC substitutes. Observe actual `na`, POC freshness and streak. If no missing-data interval is available, classify the missing-data experiment BLOCKED; do not create synthetic footprint and call it empirical evidence. Reload-vs-live FP deltas require saved native observations before reload.
4. **D3 calculation mode only:** on diagnostic copies, vary one Property at a time; retain all others. V2 itself intentionally rejects intrabar/repeated calculation. An error is rejection of that configuration, not evidence of parity or a V1 root cause. Record effective Properties and instance timestamps.
5. **D4 bracket execution only:** same diagnostic signals/settings; compare Bar Magnifier off/on as a single intervention, then a separately paired slippage change only for execution QA. Restore source baseline between pairs. Capture entry fill, frozen intended bracket, stop/target fill and native exit comment. Where path is unknown, report ambiguous; never substitute a locally favorable price.
6. **D5 reload:** export chart telemetry and native trade list BEFORE reload, repeat after reload with identical inputs and range. Identify first changed source value, not only changed PnL. Separately label historical recomputation and true realtime observations.
7. **D6 forward:** only after native compile and operator authorization, create a unique V2 order-fill-only alert; keep current V1 running unchanged. Compare synchronized observations but do not assume that V1's hidden server inputs match V2. Record actual observation start/end and sample counts. No invented minimum sample or numeric tolerance grants PASS.

## Required native edge cases

Next-available-tick entry; entry and exit in same bar; adverse stopgap; both SL/TP in one bar; pattern exit competing with bracket; session close and missing last bar; end-date boundary; tick rounding; overnight gap; first valid footprint and missing footprint; all HTF boundaries; daylight-saving change; contract roll/data adjustment; reload. Each needs its own observed result or BLOCKED/NOT RUN, not a blanket pass.

## Telemetry interpretation

- Model masks: long FADE=1, DIV=2, TRAP=4, AGG=8, ABSORB=16, VRZ=32; short uses 64 times those bits. `eval` is reached branch, `flow` is model condition passed, `raw` is original-priority winner after target-distance check. `priority_skipped` is deliberately unevaluated, not false and not a missing independent signal. Shared filters precede these branches.
- `filter_mask`: liquidity1/downtrend2/uptrend4/overextension long8/short16/confidence long32/short64/no hidden veto long128/short256/HTF long512/short1024/ADX2048/enabled long4096/short8192.
- `exec_gates` snapshots before dispatch: dates1/session2/time4/footprint8/slot16/no conflict32/confirmed64. Candidate levels are only calculated after earlier gates pass; null is not proof of bad geometry.
- Block reason: 0 no candidate; 1 unconfirmed; 2 dates; 3 conflict; 4 busy; 5 time; 6 footprint; 7 invalid levels; 8 submitted; 9 residual/inspect. Only the first blocking gate is reported; masks preserve the other observable gates.
- `order_created_ms` is the script's closed-bar submission time, not the exchange arrival time. Native entry/exit observations may be emitted at a later Pine calculation than the fill. Outer `strategy.order.price` is supplied by TV at fill. Frozen context is intention, not actual risk or guaranteed fill.
- `strategy.closedtrades`, `strategy.opentrades` and server fill events are native evidence. `DIAGNOSTIC_NOT_A_TRADE` is never a trade. A chart-only marker, a blocked candidate, Alert Log event and phone notification are four different things.
- Chart data export is not Deep Backtesting telemetry. Pine Logs retain only the latest 10,000 historical messages; use bounded windows and save before reload. `v2TraceAllBars` is for a bounded diagnostic run. Full-bar diagnostic alerts can hit platform throttling and are not enabled by default.

## Remaining boundaries

An 11-bar non-na streak does not prove minute continuity, both-sided volume or footprint resolution. Confirmed HTF does not freeze external TICK/VIX/SPY/ES feeds, exchange revisions, roll adjustment, history initialization or footprint reconstruction. The previous completed HTF value becomes available on the next 1m bar; it is not used early on the last 1m bar ending at that boundary. No new warmup or continuity filter was silently inserted.

Original stops/targets are already frozen and submitted with entry. V2 improves provenance; it is not proof that a delayed original bracket caused a specific loss. Native gap risk remains. Original NY session logic is preserved; this is not verification of any provider's EST/EDT or holiday rules.

## Local replay of evidence tools

Run `python3 build_v2.py`, then `python3 -m unittest -v test_qa`, then `python3 collect_qa.py`. For actual operator exports use `python3 qa_tools.py alerts.jsonl --out PRIVATE_DIR`. Input must contain complete JSONL messages from the supplied template; malformed text should be repaired from original evidence, never guessed. Reconciler assumes 2 USD/point and 1 USD roundtrip commission per MNQ, and explicitly discloses ties, duplicates and unknown/future HTF. It is not a native fill oracle. A missing/ambiguous alert makes the sample incomplete.

## Acceptance

Local source/build tests can pass separately. Pine Compile requires an actual editor result, Execution requires native lifecycle evidence, Alert Parity requires saved paired realtime events, Non-Repaint requires before/after reload evidence including feed fields, and Bracket Risk requires intended vs actual fill evidence. Stop at first unexplained divergence. No funded or live authorization follows from this work.

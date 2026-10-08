# ZAC v2 — Coding blueprint v1

Status: READY FOR FIRST CLEAN C4 BUILD  
Purpose: minimize TradingView iterations by solving known Python→Pine translation failures before the first new Pine file.

## 1. Core design decision

ZAC v2 will not begin from the old Pine harness.

The first Pine file is a clean implementation built from:
- frozen strategy documents,
- verified helper mechanics,
- known parity failures,
- the new execution/observability rules learned on 2026-10-08.

The old ZAC v1.x files remain diagnostic history only.

## 2. Build architecture

The Pine code is separated into layers:

1. **Environment / execution shell**
2. **Deterministic 1m-derived aggregators**
3. **Shared feature engines**
4. **Module state machines**
5. **Raw analytical geometry**
6. **Executable order geometry**
7. **Order / fill / exit ledger**
8. **Mobile QA dashboard**
9. **Portfolio router**
10. **Funded layer**

Stages 9–10 are not added until all three modules pass individual implementation/parity gates.

## 3. Pine execution shell — fixed from first file

Use:
- Pine v6
- standard MNQ 1m chart only
- `pyramiding=0` during individual-module parity
- `process_orders_on_close=false`
- `calc_on_every_tick=false`
- `calc_on_order_fills=false` initially unless a module specifically requires it
- `margin_long=0`, `margin_short=0`
- commission = $0.50 per contract per side
- slippage = 1 tick
- integer quantity
- max 20 MNQ

Why:
Earlier TradingView runs produced signals but no historical fills until margin settings and real strategy orders were corrected.

## 4. Observability — mandatory from first file

Never infer trade count only from `strategy.position_size`.

Every module must track:
- raw signal count
- each gate count
- candidate count
- qty=0
- blocked-by-position
- orders submitted
- visible position-open transitions
- `strategy.closedtrades` delta
- invisible same-bar round trips
- ledger close count
- skip/cancel reason

Reason:
IBT QA proved 9 orders / 9 Strategy Tester closes but only 5 visible position transitions. Four trades opened and closed within one historical 1m bar.

### Mobile dashboard
Primary table:
- 10–15 rows
- explicit text/background colors
- compact gate funnel
- always show Strategy Tester closed and PF
- explicit own signal/order/fill/exit plotshapes
- native TradingView trade arrows are presentation only

## 5. Time and MTF construction

### Rule
Do not rely on ambiguous `request.security` offsets for core parity state when the same structure can be built deterministically from the 1m chart.

Prefer explicit 1m aggregation/state for:
- 3m
- 5m
- 15m
- 60m
- 240m

Each aggregate must define:
- start boundary
- completed timestamp
- first 1m bar at which completed OHLCV becomes known
- update ordering

### C4 first-known convention
The DS180 profile at a 5m boundary uses the **180 completed 1m bars immediately before that boundary**.

This follows the preserved Python helper:
`calc_profiles(... range(s,b))`.

Example:
At 07:00 CT freeze, use bars ending through 06:59, not the 07:00 bar.

### HTF FVG convention
FVG objects are created only from fully completed HTF candles.
Store:
- low edge
- high edge
- formation type
- source timeframe
- creation/first-valid 1m bar
- touched/pruned state

No new HTF object is allowed to become historically available before its HTF candle is complete.

## 6. Price-zone touch and FVG lifecycle

Correct interval overlap:
`barHigh >= zoneLow and barLow <= zoneHigh`

Never use one-sided tests such as:
- bullish `low <= gapHigh`
- bearish `high >= gapLow`

Those previously deleted untouched FVGs that price had never reached.

Update order must be explicit and fixed:
1. finalize completed aggregate(s)
2. create new objects
3. prune eligible old objects according to first-valid rules
4. choose nearest eligible object
5. evaluate signal
6. update pending orders
7. observe fills/exits

Creation-bar touch policy must be explicit. No accidental same-calculation creation/prune.

## 7. Raw analytical geometry vs executable order geometry

Maintain both representations.

### Raw
Used for strategy identity:
- DS180 VAH/VAL/POC
- FVG edges
- signal distance
- structural risk gate
- 2R-before-FVG test
- Prime profile POC/VA
- ZAB frozen POC

Do **not** tick-round raw synthetic profile levels.

### Executable
Used only when an exchange order must be sent:
- limit price
- stop price
- target price
- actual quantity calculation if specification requires executable geometry

Dashboard should expose raw→executable differences where they can change identity.

## 8. Next-open problem

Pine market orders submitted at signal close fill on the next bar under `process_orders_on_close=false`, but quantity is selected before next open is known.

This is material for any Python reference whose sizing/stop geometry uses exact next 1m open.

Known Prime:
- entry = exact next observed 1m open
- reference stops may be off-tick
- target distance code uses signal-close geometry before next open

Known legacy POC lab:
actual fill drift was >=1 tick on 3/4 fills, proving next-open mismatch is not theoretical.

Therefore:
- signal selection must not use future next open
- provisional sizing must be identified as provisional where unavoidable
- actual fill geometry must be recorded
- no hidden approximation may be called exact parity
- if quantity differs because next open was unknown, classify as explicit execution-parity issue, not signal failure

## 9. C4 clean implementation plan

### 9.1 Profile engine
From preserved DS180 Python:
- 180 completed 1m bars
- 60 bins
- 70% VA
- bar volume distributed equally across all bins touched
- POC = first max-volume bin because Python updates only on `acc > mx`
- VA expansion:
  - compare adjacent left/right volume
  - if right > left choose right
  - otherwise choose left
- raw VAH = upper boundary of high VA bin
- raw VAL = lower boundary of low VA bin
- raw POC = center of POC bin

Balance:
- comp <= 1.0
- efficiency <= 0.35
- inside-value closes >= 0.65

Freeze:
- every 5 minutes
- C4 signal session 07:00–14:29 America/Chicago

### 9.2 Rejection
REJ only.

Long:
- low <= frozen VAL
- close > frozen VAL
- bullish body / directional close condition per frozen lineage

Short inverse at VAH.

### 9.3 Displacement
Source evidence is not perfectly consistent:
- D00054/D00053 describe displacement >=0.10 ATR
- C4 static QA calls it body >=0.10 ATR
- old Pine v1.1 used close-to-VA-edge displacement

**Do not silently choose based on performance.**
First code will expose both diagnostics:
- body displacement = abs(close-open)/ATR
- edge displacement = distance close↔VA edge/ATR

Execution semantic will be labeled source-choice and kept isolated so one line can be switched after source resolution. This avoids rebuilding the rest of the engine.

### 9.4 FVG
Frozen requirement:
- untouched causal 1H/4H FVG in trade direction
- nearest relevant FVG
- distance <=8 ATR

Known old-Pine failures that first code must avoid:
- wrong direction filtering
- ambiguous `request.security` alignment
- incorrect prune condition
- rounding FVG edges
- unclear create/prune order

First code will build 1H/4H FVG state from completed aggregates and expose:
- created bull/bear
- active bull/bear
- pruned bull/bear
- nearest same-direction edge
- source TF
- distance ATR

### 9.5 RelVol
D00054 canonical conditioner:
latest completed 5m bar volume / previous 20 completed 5m bar volumes >=1.0.

Important denominator:
The latest completed 5m numerator must not also enter the prior-20 denominator.

Build manually from completed 5m volumes rather than an opaque security expression.

### 9.6 Pending limit state
- signal creates pending order
- resting limit at frozen raw VA edge, executable level separately normalized if needed
- valid <=10 minutes
- close-invalidation if close >1 tick through edge on wrong side before valid fill
- structural stop = 1 tick behind rejection wick
- raw structural risk >=0.25 ATR
- target = fixed 2R
- setup accepted only if FVG lies beyond the 2R target in trade direction
- **do not clip target to FVG**

### 9.7 Intrabar ordering
Canonical research says conservative stop-first for SL/TP conflict.

For pending limit fill bars there is still an explicit source ambiguity:
fill/retest vs close-invalidation vs expiry ordering.

First code will:
- expose counts for bars where fill and invalidation are both possible
- keep a named conflict policy constant in one section
- avoid scattering this semantic throughout code
- never retune the policy based on PF

### 9.8 C4 reference fingerprints
Canonical D00054:
- ALL n376
- WR 57.7%
- PF 2.04
- Exp +0.53R
- Net +198.70R
- MaxDD 25.47R

2025–26:
- n105
- PF 2.83
- Exp +0.75R
- DD 4.76R

2025-10+:
- n51
- PF 3.53

Year counts:
2019 28
2020 49
2021 51
2022 34
2023 61
2024 48
2025 71
2026 34

These are diagnostic fingerprints, never optimization targets.

## 10. Prime clean implementation plan

Frozen identity:
- Core v1 rules
- only material change: session 09:00–10:59 America/New_York
- 3m local auction
- minimum local balance 25m / 9 completed 3m bars
- acceptance = OOB persists into newly settled profile whose POC remains outside prior buffered VA in continuation direction
- entry = next exact 1m open after acceptance
- prior auction POC = structural invalidation; stop 1 tick beyond it on invalid side
- max hold 240m
- flat 16:45 America/New_York

External target semantic must preserve source-code behavior:
1. find nearest FVG among 15/30/60
2. require selected target TF == 15
3. distance rule is based on signal-close-derived `target_va`
Do NOT rewrite this as “search only 15m FVG” without a new approved identity.

Reference:
- n173
- 60 trades at 09 hour, 113 at 10 hour
- PF 2.0253116483
- Exp +0.1252426286R
- Net +21.6669747483R
- DD 2.7124448610R
- WR 85.5491%

Known unresolved:
- original helper `amt_ltf_research_mags.py` is missing
- one Prime stop differs by 1.30 points in reconstruction
- all 173 reference stops are off tick-grid
- target prices are on tick-grid

Therefore Prime can be implemented, but generator parity cannot be called exact unless the helper/source identity is explicitly resolved.

## 11. ZAB clean implementation plan

Frozen:
- frozen 180m VP / POC
- directional POC cross
- directional signal body
- later valid retest <=10m
- resting limit at frozen POC
- invalidation if close >1 tick through POC wrong way before retest
- structural stop behind cross-signal wick
- 30m cooldown applied BEFORE RelVol filter
- causal 15m RelVol >=2.5
- fixed 1.5R TP
- max hold 120m
- conservative stop-first
- FVG is metadata only
- no RSI
- no CRT
- no DS180 balance gate unless explicitly present in canonical source

Reference:
- n940
- PF 1.8202
- Exp +0.3738R
- Net +351.37R
- DD 12.16R
- WR 63.83%
- 2025–26 n228 / PF 2.4414 / Exp +0.5450R
- 2025-10+ n129 / PF 3.4451

Unresolved:
- exact 15m RelVol denominator/alignment
- exact cross/body interpretation
- active-position/cooldown state ordering

First ZAB code must make each of these a localized semantic constant/state block, not intertwined implementation.

## 12. Router design — later only

REFERENCE mode:
- raw module engines are never blocked by funded state
- preserve raw module signals/trades separately

FUNDED mode:
- same raw signals
- separate causal risk/router layer

Frozen portfolio risk:
- C4 $350
- Prime $500
- ZAB $250
- max 20 MNQ

Funded context from ZAC freeze:
- target +$1,250
- DLL $600 hard block on new trades
- MLL $1,000 trailing EOD
- 50% consistency
- daily realized profit stop +$500

Exact current Lucid timing/rules must be reverified before deployment; not needed for raw strategy parity.

## 13. First-code acceptance criteria

The first new C4 file should compile and answer all of these from one mobile screenshot:

- profile freezes occurring?
- balanced profiles count?
- raw rejection L/S?
- body displacement pass?
- edge displacement pass?
- FVG available?
- FVG <=8 ATR?
- RelVol pass?
- structural risk pass?
- 2R-before-FVG pass?
- pending orders?
- invalidated?
- expired?
- qty=0?
- orders?
- visible fills?
- ledger closes?
- invisible same-bar RT?
- current active pending/position state?
- Strategy Tester closed / PF?

If it cannot answer those questions, the code is under-instrumented and should not be the baseline.

## 14. What is deliberately NOT solved by the first mobile code

- full canonical n376 parity
- cross-data roll differences between Databento canonical and TV MNQ1!
- exact Prime missing-helper stop identity
- exact ZAB RelVol semantic if source remains unresolved
- funded router
- webhook/live

Those require later gates, but none should force a rewrite of the shared Pine architecture.

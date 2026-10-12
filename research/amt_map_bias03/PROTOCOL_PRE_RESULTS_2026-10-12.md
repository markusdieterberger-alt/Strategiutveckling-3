# AMT BIAS 03 — Daily-HVN rejection × Globex IB (förhandslåst testdesign)
Date: 2026-10-12 · Project Strategiutveckling · Status: research-only, no trading approval

## Why a new version?
D02031 compared independent IB/FVG/POC signals on only 3,128 structurally qualified neutral snapshots. Its follow-up was constrained to snapshots in the **local 150-bar value area**, all from NY in a subsequent subset, and previously called daily rejection was actually rejection of yesterday's *overall VAH/VAL*, not a named daily HVN edge. Those are different hypotheses. Do not rename the old result as evidence for node rejection. Legacy results are DEV; there is no blind OOS.

## Data, population, and locked construction
- Use only owned canonical MNQ 1m OHLCV, never purchase tick/VAP feeds. The canonical historical daily-contract selection is not fully causal; report 2019–2025 separately from the TradingView-master overlap.
- NY timezone: `America/New_York`; EU timezone: `Europe/Stockholm` (DST explicit). All features from completed bars only.
- Draw observation anchors independent of value position: EU 07:05–11:50 Stockholm every 15m; NY 09:35–11:50 New York every 15m. No momentum, FVG, POC, IB, profile, or outcome is used to *select* anchors. Deduplicate signals if active event has not resolved.
- Global map at anchor: 1,000 completed 1m bars, fixed 2.0 index-point bin (anchored at zero), smoothed 3-bin [1,2,1]/4; compare HL-equal-volume-per-touched-bin with CLOSE-only. A missing or rolled bar must be tagged; never bridge a weekend, contract roll, or invalid session just to keep a level alive.
- For local value, 150 completed 1m bars, 70% value area expanded greedily around POC. **Classify** anchor as ABOVE / WITHIN / BELOW local VA; do not filter out ABOVE/BELOW. This directly tests the selection limitation in D02031.
- Previous *fully completed NY cash session* 09:30–15:59 (not the evolving current day) is the HTF daily profile. Require at least 300 valid minute bars, and never compute from future/current day's RTH.
- Daily HVN = smoothed local-max price-bin >= 1.25× median non-empty smoothed profile volume; distinct neighboring HVNs >= 5 bins apart. The HVN *band*, NOT global 70% VA, is the contiguous region around this peak where smoothed bin-volume >= 0.60 × peak volume. Nearest daily HVN to current price is chosen **as-of**; ties choose lower price. LONG rejection = completed 5m probe beneath that band's lower edge and completed close back above it, within previous 30m; SHORT = symmetrical upper edge.
- Control is **previous full-day global VAL/VAH** rejection with precisely the same probe/reclaim logic and observation population. Strictly separate from daily-HVN-band.
- Globex IB = 18:00–18:59 New York for the *most recent completed* Globex opening. Label EXPANSION_LONG if current price above IB high, EXPANSION_SHORT if below IB low, else WITHIN; IB is not inferred from current day future.
- Direction for rejection events comes ONLY from which previous-day structure was rejected (lower -> LONG, upper -> SHORT). IB is a **conditioner**, not the direction chooser. Signed 120m momentum is a separate diagnostic control. No ex-post flipping to direction with an available HVN destination.
- Main control groups on identical preselected anchors: (A) HVN rejection + IB aligned, (B) HVN rejection + IB not aligned, (C) VA-edge rejection + IB aligned, (D) VA-edge rejection + IB not aligned. Report all n and abstentions; do not tune thresholds post hoc.

## Fixed outcomes, gates
1. Primary directional outcome, ALL rejection anchors (no map-selection required): signed next 30m return from next available 1m-open to 30m close, plus 60m; first touch of symmetric ±0.5 × previous day's completed RTH true range (or realized ATR14 5m if RTH range unavailable), with ambiguous within-bar treated as unresolved.
2. Secondary map outcome: when a valid *predefined* 1,000bar HVN B exists in the rejection direction and at favorable geometry (entry < target for long; vice versa short), first target hit before equal-distance mirror/adverse within 120m. Report what fraction has *NO ROUTE*; do not count route absence as profitable/negative trade.
3. Tertiary trade, ONLY after directional effect survives: 150bar VAL-limit vs 5m confirmed breakout vs OCO hybrid, stop beyond rejected band plus last 30m swing, target proximal edge HVN B. Start at next open, never same signal-bar fill; conservative stop-first, 1/2/3 Nasdaq-points round-trip costs, $2/point/MNQ, no funded probability until TV/Python parity.
4. Stratify year bands 2019–22, 2023–24, 2025–26, NY/EU, long/short, within/outside 150bar VA, source contract/roll quality and BOTH proxy methods. Day-block 95% bootstrap CIs; include zero sample explicitly.
5. Reject/hold if effect changes sign in different data/profile constructions; do not call overlapping historical windows out-of-sample. More independent data is only FUTURE, post-2026-10-12; no purchases.

## Engineering gates
- Bias semantics separate from setup semantics. Pine feasibility first: fixed bin grid, <=1000 bars, limit CPU/arrays, confirmed timeframes, NY IB timezone, no repaint or future-known daily HVN.
- Reproduce **same anchors and feature values** between Python and Pine before trade P&L comparisons. TradingView 1m OHLCV vs canonical may differ at roll.
- Keep AMT Node-to-Node V1, CT Scalper EAA/EAB, and all previous A001 versions frozen.
- **Computer priority 1 remains CT Scalper EAB A/B/C verification.** AMT code is an independent research branch.

Status meanings: code authored != code executed; static review != Pine compilation; favorable DEV return != validated tradeable edge.

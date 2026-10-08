# ZAC v2 rebuild — Python/ChatGPT → Pine translation contract

Status: ACTIVE IMPLEMENTATION CONTRACT

## Primary portfolio
ZAC = C4 + AMT Micro Prime + ZAB-02A.

This branch is the primary Pine rebuild track. XAC rebuild work is legacy technical QA only.

## Core principle
Pine is a port of frozen strategy identities, not a redesign. No threshold/session/edge tuning is allowed to force parity.

## Mandatory build order
1. Execution shell
2. Time/MTF construction
3. Feature/state engines
4. Object lifecycles
5. Gate funnel
6. Order state
7. Fill/exit ledger
8. Module parity
9. Router
10. Funded mode
11. Webhook/live

## Mandatory observability
Every module must expose:
- each gate count,
- qty=0,
- blocked-by-position/router,
- orders,
- visible position fills,
- strategy.closedtrades ledger closes,
- invisible same-bar round trips when present.

Never rely on position_size transitions alone.

## Mobile phase
Until desktop returns:
- compact dashboard (10–15 rows),
- explicit plotshape/labels for signal/order/fill/exit,
- Strategy Tester closed/PF when visible,
- strategy.closedtrades delta as trade ledger.

Native mobile execution marks are presentation only.

## Full-period source of truth
Deep Strategy Tester is required for final TradingView n/PF/PnL/DD parity.

## Known translation traps
- margin_long=0 / margin_short=0 required in our working MNQ shell.
- Same-bar round trips can be invisible to position_size transitions.
- HTF causality must define source bar and first-known 1m timestamp.
- Object lifecycle/update order is part of strategy identity.
- Price-zone touch means true interval overlap.
- Raw analytical level must be separated from executable tick price.
- Next-open sizing/stop geometry must be explicit.
- Pine multiline syntax should be compile-safe; syntax-only fixes get separate versions.
- Mobile tables need explicit colors and compact size.

## ZAC build sequence

### C4
Frozen reference fingerprint:
- ALL ~376 trades
- PF ~2.04
- Exp ~+0.53R
- 2025–26 n105 / PF ~2.83

Required single-code funnel:
RAW rejection → displacement → FVG available → <=8ATR → causal 5m RelVol → structural risk → 2R room → pending limit → fill → close.

### Prime
Reference:
- n173
- PF 2.0253
- Exp +0.12524R
- WR 85.55%

### ZAB
Reference:
- n940
- PF 1.8202
- Exp +0.3738R
- 2025–26 n228 / PF 2.4414

No module enters the combined router before individual parity is PASS or a known technical mismatch is explicitly documented.

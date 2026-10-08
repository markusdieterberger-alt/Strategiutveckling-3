# XAC v2 rebuild — Python/ChatGPT → Pine parity contract

Status: WORKING CONTRACT / rebuild branch

## Principle
XAC v2 is a port, not a redesign. No strategy thresholds are tuned to make Pine look better.

## Layer order
1. Execution shell
2. Component state engine
3. Component signal funnel
4. Order submission
5. Fill/exit state
6. Multi-component router
7. Funded gates
8. Webhook/live automation

A layer is frozen before the next one is added.

## Mobile-only phase
Until desktop access returns, evidence is restricted to:
- compact on-chart dashboard
- explicit plotshape/label execution marks
- TradingView visible closed-trade/PF fields when available

Native mobile execution arrows are not trusted as the only evidence.

## Stage 1: A4
Frozen source semantics are taken from the preserved XAC v1.6 source identity:
- 30m CRT
- attached same-bar FVG
- sweep minute 10..19
- recovery >=60%
- Stockholm windows 12:00–14:59 or 16:00–20:59
- cancel if NEAR is touched before confirmation
- 1m HH/LL confirmation
- structural stop one tick beyond CRT extreme
- target FAR FVG edge
- market order submitted at confirmation close, fill expected next 1m open
- risk $550, max 20 MNQ

## Stage-1 gate funnel
30m completed → CRT → attached → sweep → recovery → time → qualified
→ cancel/confirm → order → fill → close.

No downstream module is added until this funnel is visible and execution marks work on mobile.

## Source-of-truth
GitHub branch: xac-v2-rebuild
Older XAC code is reference evidence, not the active implementation.

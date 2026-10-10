# EAA validation factory v1

Start with `docs/eaa/EAA_SLUTRAPPORT_V1.md` and the short computer-session order.
Run `python3 -m unittest discover -s tests/eaa -v` from the repository root.
See `docs/eaa/EAA_FUNDED_SIMULATOR_V1.md` for data contracts and commands.

Status updated 2026-10-10: HMA and the newly delivered CT strategy await
TradingView compilation and execution. CT now uses the exact uploaded indicator
bytes, not the public BACKTEST reference. See `docs/eaa/EAA_CT_SCALPER_QA_V1.md`
and `docs/eaa/EAA_CT_DATORPASS_KORORDER_V1.md`.
Rebuild CT: `python -m eaa.build_ct`; verify: `python -m eaa.verify_ct`.
CT's Python execution oracle tests a contract, not the Pine runtime.
All challenge outputs are approximate conditional replays, not firm certification.

No network, brokerage access, order submission, or parameter optimization is used.
No ZAC/R1/frozen code is changed. Nothing is approved for live trading.

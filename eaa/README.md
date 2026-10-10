# EAA validation factory v1

Start with `docs/eaa/EAA_SLUTRAPPORT_V1.md` and the short computer-session order.
Run `python3 -m unittest discover -s tests/eaa -v` from the repository root.
See `docs/eaa/EAA_FUNDED_SIMULATOR_V1.md` for data contracts and commands.

Status: partial delivery. HMA ORIGINAL and EXEC FIXED are static-reviewed only.
CT's exact requested indicator source was not recovered. The public BACKTEST
reference is a different source identity, not the requested conversion.
All challenge outputs are approximate conditional replays, not firm certification.

No network, brokerage access, order submission, or parameter optimization is used.
No ZAC/R1/frozen code is changed. Nothing is approved for live trading.

# PineScripter ZAC baseline — 2026-10-08

Status: BASELINE / NOT PARITY APPROVED.

The operator supplied the first PineScripter-generated ZAC code in the project chat on 2026-10-08. It is preserved as the baseline for the PineScripter translation track.

Important audit findings:
- Prime/D00055 is intentionally stubbed: primeLongRaw=false, primeShortRaw=false.
- C4 and ZAB require parity corrections before use.
- HTF completed-bar timing, frozen-state timing, FVG lifecycle, RelVol timing, pending-order/router state and funded accounting require source-faithful review.
- Do not treat PineScripter's compiler/requirements checks as Python parity evidence.

Prime source clarification recovered from D00055 and AMT canonical report:
- Prime v2-DEV = AMT Micro Core v1 with the only material change being session 09:00–10:59 America/New_York.
- 3m local auction / acceptance-to-continuation.
- Minimum local balance: 25 minutes / 9 completed 3m bars.
- Acceptance: OOB persists into a newly settled profile whose POC remains outside prior buffered value area.
- Nearest untouched 15m FVG in continuation direction.
- Target distance <= 1.0x prior VA width.
- Stop = 1 tick beyond prior auction POC on invalid side.
- Entry = exact next observed 1m open after acceptance.
- Source execution: 1.0 MNQ index point total adverse friction, same-bar stop-first, flat 16:45 New York, max hold 240 min.
- Prime reference: n=173, PF≈2.025, Exp≈+0.1252R, Net≈+21.67R, MaxDD≈2.71R, WR≈85.55%.
- The original helper amt_ltf_research_mags.py remains unavailable; exact lower-level profile/buffer implementation is not yet source-complete.

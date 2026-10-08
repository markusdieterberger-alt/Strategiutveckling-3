# XAC v2 clean rebuild

Branch: `xac-v2-rebuild`

Current file:
- `pine/xac/XAC_v2_0_alpha1_A4_REBUILD.pine`

Stage 1 deliberately contains only A4 plus the verified execution shell and mobile QA instrumentation.

Why one module first:
A previous Pine rebuild compounded signal, state, MTF and execution mismatches. XAC v2 locks parity one layer/module at a time.

Next after A4 QA:
IB → IBT → POC → Scalp → router → funded gates.

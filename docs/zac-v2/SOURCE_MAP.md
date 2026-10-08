# ZAC v2 — Source map and authority hierarchy

Status: ACTIVE / pre-code source inventory  
Branch: `zac-v2-rebuild`

## Authority order

1. Operator's latest explicit decision
2. A001 — governance
3. Latest A003 — operational handover
4. ZAC-01 freeze
5. D00054 / D00055 / D00064 frozen component documents
6. Verified source code / reference ledgers
7. Reconstruction notes and legacy Pine
8. Legacy/XAC material only as technical implementation evidence

No lower source may silently override a higher one.

## Governing documents

| Source | ID / location | Role |
|---|---|---|
| A001 — Stående order | Google Drive ID `1TZ1hj1qBeOTIC0dDWgrUql-W53fnVxjBs670BsamvXc` | Governance |
| A003 — Handover Projektledare | Google Drive ID `1CfUzcWIWUkP1hKEqb39pYQy5dWnRz4pBmTDKqcL-ZrA` | Current operational state |
| ZAC-01 freeze | Google Drive ID `1RuclrpleQ19ZpXAADk9zTVj6V9Mfakm4sGJS5gKjEbc` | Frozen portfolio identity |
| ZAC work package | Google Drive ID `1smn34ZIZ8AvMj1ZXUL-jNnTIIstgiNHXiYuSzu5pDW0` | Restart/work protocol |
| Pine engineering spec v0.1 | Google Drive ID `1ZQPtreLdBpR_6rEvnKozF3rEZGkX9zX-` | Earlier implementation spec |
| ZAC parity report 2026-10-07 | preserved snapshot in this repo | Source/parity caveats |

## Component sources

### C4 / D00054
Drive ID: `1Fpa3lemWf0olqEdNXoInPQ-kl8F8UhiD4iNYsxh7o6E`

Supporting lineage:
- D00053: `1sbzi2u5kdZL6NCLSSIMlru6WgNgoAzLTZ8nYArcSo4o`
- D00052: `1fd200dhS8ZpcJ4a40ZdW6Ovybwmq6cfikQc3rGm37RY`
- C4 parity static QA: `1UqqA7s62_f9xQNh4OR4L6cImFqadTMS07Xwx7C3-HCw`
- Preserved DS180 Python source snapshot: `references/python/VP_DS180_CANONICAL_v1.py`

Important: VP_DS180 source is authoritative for profile construction mechanics only where source lineage agrees. Its own entry/trailing/cooldown rules are NOT C4 rules.

### AMT Micro Prime / D00055
Drive ID: `1jFq1R3qxAeTAhDD_JFU5RJK0BeeTgQEoQ1n-wez2GdI`

Supporting:
- AMT canonical report: Drive ID `1jLykE4WDjTqINUjuEvydmJsNgnLjRt4S`
- ZAC parity report snapshot in this repo.

Known missing source:
- original `amt_ltf_research_mags.py` helper was not recovered.
Therefore exact OHLC→stop generator parity is not proven even though the 173-trade reference subset and execution replay are recovered.

### ZAB-02A / D00064
Drive ID: `1GS6poCWcBawmdkk0zcFa10Z9CyTihJhrWXlF7H0mLwE`

Supporting:
- ZAC work package
- ZAC parity report
- DS180 profile helper for shared profile mechanics where applicable

Known unresolved source items:
- exact causal 15m RelVol denominator/alignment
- exact cross/body/state/cooldown ordering

## Canonical data

MNQ canonical:
- 2019-05-05 → 2026-10-02
- 2,614,900 1m bars
- UTC
- 30 volume-based front-month rolls
- no back-adjustment
- SHA256 `45cb26293d64d77b10062a3603c38b5eb66743d22dea7611a9672478f54e1ccd`

TradingView MNQ1! is a separate execution/parity source and will differ on roll/gap days. Such differences must not be confused with logic errors.

## Portfolio identity

ZAC = C4 + AMT Micro Prime + ZAB-02A

Frozen nominal risk:
- C4: $350
- Prime: $500
- ZAB: $250
- integer MNQ
- max 20 MNQ
- ORB OFF

No new filters, sessions, confluence, thresholds or target/stop changes are permitted inside ZAC-01 without a new version identity.

# Bucko Replica V3: frozen economic research harness

Separate RECON04 research branch. No changes to CT Scalper or original signal definitions. No live promotion.

The pre-result protocol is PROTOCOL_PRE_RESULTS.md (commit50c4794505ba40f4e3493a40c99edc85b6f9fea0). The original signal engine is under frozen/reference_replay.py; execution assumptions are separate. Native Pine and footprint are not executed by this harness.

Use the authorized private BUCKO_RECON_04 reproducible package for input data, full replay instructions, frozen golden excerpt, calendars, results and QA. No market-data files or private project logs are published here.

Python3.12; dependencies in requirements.txt. Run code/verify_package.py against the private package, then the13 unittest gates. Generate signals with code/signal_adapter.py for master, legacy and excerpt; execute code/run_economic.py for master/legacy; summarize with code/analyze.py and code/additional_diagnostics.py.

All RR and stress scenarios are retained separately. Do not select a winner or merge this branch into a production strategy without a new research decision.

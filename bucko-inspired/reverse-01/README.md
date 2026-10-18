# BUCKO REVERSE 01 - reproducera experimentet

Efterhandsinitierad DEV-studie, beställd efter RECON04-resultaten. Ingen del av denna historik är ny OOS. Ingen signal-, sessions-, regim- eller parameteroptimering ingår. Original-Python/Pine, footprintpilot och CT Scalper är oförändrade.

## Paket och källor

`baseline/` är det byteverifierade innehållet i levererat RECON04-paket. Dess `MANIFEST_SHA256.json` och egen QA beskriver källor, dataval och tidigare begränsningar. `results/source_audit.json` dokumenterar återkontroll av alla 156 manifestposter samt SHA256-matchning av de två tillgängliga rådatafilerna mot RECON04. De normaliserade master-/legacyfilerna, rullkalendern och helgdagslistan ingår i `baseline/data/`.

Fulla råa GLBX-källfilen (cirka388MB) distribueras inte en gång till; den behövs för att oberoende granska ursprungsrekonstruktionen med `baseline/code/prepare_data.py`. Den behövs inte för att återskapa denna studies frysta signaler och samtliga 36 exekveringsböcker från inkluderade priser. Referenshash finns i källinventeringen. Föräldrapaketets gamla rapporter, loggar och kod är historiska källor, inte nya REVERSE-resultat.

`PROTOCOL_PRE_RESULTS.md` är låst före spegelresultat. `protocol_lock.json`, `code_lock_pre_economic.json` och `analysis_lock.json` skiljer förhandslåst protokoll/exekvering/statistik från senare rapporttext. Git-protokollcommit: `dc50f8c44e6bc8e4038dd994b2c3b4cd979b1bbc`, separat branch `bucko/reverse-01-20261018` i projektets repository.

## Miljö

Verifierad miljö: Python3.12.14, pandas2.2.3, numpy2.3.5. Rapport: matplotlib3.10.8, reportlab4.4.9 och pypdf6.10.0. `requirements.txt` innehåller versionerna. Poppler används endast för visuell PDF-kontroll. Använd Python3.12 och ett eget virtualenv; installation ingår inte i nedanstående körkommandon.

## Exakta kommandon

Kör från denna README:s katalog. Använd `python` från miljön ovan. Kör inte gamla `baseline/code/run_economic.py` eftersom den skriver till originalets resultatkatalog. Låt `baseline/` vara orörd.

```bash
mkdir -p work results cache/signals
python code/verify_package.py
python baseline/code/test_execution.py > work/original_tests.txt 2>&1
python code/test_reverse.py > work/reverse_tests.txt 2>&1
python code/make_signals.py --dataset master > work/master_signals.log 2>&1
python code/make_signals.py --dataset legacy > work/legacy_signals.log 2>&1
python code/run_experiment.py --dataset master > work/master_economic.log 2>&1
python code/run_experiment.py --dataset legacy > work/legacy_economic.log 2>&1
python code/analyze_experiment.py > work/analysis.log 2>&1
python code/write_deliverables.py
python code/build_report.py
```

Signalcacherna återskapas från frysta priser och är inte med i leverans-ZIP:en. Ekonomikoden importerar originalets execution.py byteoförändrad och jämför alla18 originalböcker, kandidatloggar, dagsserier och sammanfattningsmått mot RECON04. Exekveringen avbryts vid avvikelse. Nya resultat skrivs atomärt till `results/economic_master/` respektive `results/economic_legacy/`. Förväxla inte dem med `baseline/results/`.

## Ledger och analys

`BUCKO_REVERSE_01_Trade_Ledger.csv.gz` är UTF-8 CSV komprimerad med gzip. Den innehåller alla36 separata exekveringsböcker, både ORIGINAL och REVERSE; summan av alla rader är inte en enda portfölj. Pandas öppnar direkt med `pd.read_csv(path)`; standardverktyg kan packa upp till `.csv`.

- `variant`, `dataset`, `model`, `scenario`, `rr`: unik bok och hypotes.
- `direction`: faktiskt handlad riktning, +1 LONG/-1 SHORT. `source_direction`: den ursprungligen godkända signalens riktning. Vid REVERSE gäller exakt `direction == -source_direction`.
- `score`, `signal_factor_mask`, `signal_type`: ORIGINAL-signalens godkända poäng, komponentmask och trigger. De räknas aldrig om för att godkänna motsatt sida.
- `signal_time`: signalbarens open; `signal_close_time`: tidigaste beslutstid; `entry_time`: nästa observerade open. `exit_time` för INTRABAR är barens slut som övre tidsgräns, inte en känd ticktid.
- `entry_open`: oslipat open; `entry_fill`: adverse slippage; `stop`: ny sidas frysta pivot +/-tick; `target`: omräknat från faktisk entryfill, nytt stop och RR.
- `risk_usd`: initial entryfill-SL-risk för1 MNQ, utan extra exitfriktion. `net_R = net_usd / risk_usd`. Detta är rörlig monetär risk, inte positionsstorlek med konstant USD-risk.
- `gross_before_costs_usd`: samma exekverade bok, utan entry-/exitfriktion/kommission. Inte en ny nollkostnadsbacktestbok. `effective_exit_price`: kostnadsjusterad ekvivalent; targetens adverse kostnad är en explicit haircut, ingen sämre limitfill påstås.

Kandidatloggarna innehåller varje godkänd signal, inklusive SL_INVALID_AT_SIGNAL, EXEC_WINDOW, POSITION_OPEN och NEXT_OPEN_PAST_STOP. Raw-eventflödet finns i regenererbara signalcacher. Utförda affärer är en delmängd, inte samtliga godkända signalbarer.

Alla36 körningar ingår i Test_Matrix. `results/analysis/` innehåller månads-/års-/veckoresultat, faktisk LONG/SHORT och ursprungsriktning, score/trigger/regim, halvor, kostnad före/efter, vinnarkoncentration, bootstrap, parad dagsnettoskillnad och gap-/riskdiagnostik. Inga undergrupper har valts som nya filter.

Månader baseras på RECON04:s NY-handelsdatum (lokal väggtid plus6h), inte UTC-datum. Både första och sista månaden kan vara delmånader. Mastern och legacy överlappar inte i faktiska barer; NY-handelsdatum2025-10-01 förekommer på var sin sida av periodgränsen.

## Avgränsning

OHLCV-only. Ingen historisk aggressordelta, footprint, DOM eller intragap-tickbana rekonstrueras. TradingView-kompilation, native signalparitet, live-footprint och Tradovate-fills är inte utförda i detta experiment. Tidigare dokumenterade Python/Pine-skillnader följer med. Rapporten gör inget funded-/automationgodkännande. Bootstrap och tre-RR-intervall kan inte avlägsna efterhandsvalet av inversion eller all tidigare forskning.

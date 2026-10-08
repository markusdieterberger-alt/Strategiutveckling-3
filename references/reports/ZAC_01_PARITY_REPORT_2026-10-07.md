# ZAC-01 — källgranskning och Prime-parity

Datum: 2026-10-07. Uppdrag: WORK PACKAGE v1.0.

## Slutsats: BLOCKED

Canonicaldata är verifierad. Prime-referensen är återvunnen ur den bevarade Core-loggen och samtliga 173 trades har återspelats mot canonicaldata. En oberoende regenerering av signalerna reproducerar alla trade-tidpunkter/riktningar, men inte alla stoppriser. **Prime generator-parity är därför FAIL, inte PASS.** C4/ZAB saknar ännu verifierade generatorer. Pine och funded-rerun är inte genomförda.

Ingen signalregel, session, threshold, riskbudget eller marknadsperiod har optimerats eller ändrats.

## Resultat och gates

| Kontroll | Status | Verifierat i denna körning |
|---|---|---|
| Canonical filidentitet | PASS | CSV SHA256, gzip SHA256, 2 614 900 rader, UTC, schema, start/slut, unika sorterade timestamps och 30 kontraktsbyten |
| Prime referenssubset | PASS — återvunnen logg | 173 trades = 60 kl. 09 + 113 kl. 10 New York; alla publicerade fingerprintmått matchar vid angiven decimalprecision |
| Prime execution-replay | PASS för givna entry/stop/target | 0 avvikelser i entrypris, exittid, exitpris eller exitorsak; största skillnad i R är 2,22e−16 från flyttals-/CSV-aritmetik |
| Prime OHLC→signal→trade | PARITY FAIL | Alla 280 Core trade keys matchar, inklusive 173 Prime. Fyra Core-stoppar avviker, varav en Prime-stop |
| C4 / D00054 | BLOCKED / NOT RUN | Fryst beskrivning och gammal DS180-eventkod finns; verifierad D00054-generator/reference-log saknas i hämtat underlag |
| ZAB / D00064 | BLOCKED / NOT RUN | Rapporter/fingerprints finns; exakt executable RelVol/state-definition och verifierad generator saknas i hämtat underlag |
| Gemensam canonical ZAC-ledger | NOT CREATED | Kan inte skapas som verifierad när C4/ZAB saknas och Prime-generatorn avviker |
| Pine source / compile / TV parity | NOT CREATED / NOT RUN / NOT RUN | Avvaktar verifierad source och ledger |
| Funded-rerun | NOT RUN | Kräver verifierad ledger samt ny kontroll av Lucids aktuella regler |

Senaste verifierade gate: **dataidentitet + återvunnen Prime-logg + execution-replay**. Gate A är inte godkänd i sin helhet. Uppdraget är inte COMPLETE.

## Prime: resultat från referensen respektive regenereringen

| Mått | Återvunnen referens | Återspelning | Generator: bin_width |
|---|---:|---:|---:|
| Trades | 173 | 173 | 173 |
| PF | 2,0253116483 | 2,0253116483 | 2,0253516984 |
| Expectancy R | 0,1252426286 | 0,1252426286 | 0,1252450441 |
| Net R | 21,6669747483 | 21,6669747483 | 21,6673926223 |
| MaxDD R | 2,7124448610 | 2,7124448610 | 2,7124448610 |
| Win rate | 85,54913295 % | 85,54913295 % | 85,54913295 % |

Liknande totalmått kompenserar inte för fel stoppris. Ingen generell paritytolerans har införts.

Referensen hämtas deterministiskt ur AMT_MICRO_CORE_V1_TRADES.csv, enbart genom det redan frysta sessionsurvalet 09:00–10:59 America/New_York. Det är **inte** samma sak som att signalmotorn har verifierats. Referensen saknar bland annat fulla original-ID:n för profil och FVG; sådana ID:n har inte hittats på.

### Den avvikande Prime-traden

- Entry: 2025-12-31 14:15:00 UTC, LONG, entrypris 25 700,50.
- Referensstop: 25 645,37.
- Rekonstruerad stop: 25 644,07.
- Skillnad: −1,30 indexpunkter. Båda modellerna ger SL men olika risk och R-resultat.
- Alla fyra Core-avvikelser finns i CORE_REGENERATION_COMPARISON.csv. De övriga tre infaller kl. 11 New York och ingår inte i Prime.

## Vad som prövats utan retuning

Den levererade AMT-koden importerar `/mnt/data/amt_ltf_research_mags.py`. Filen saknas i AMT-paketet. Sökning efter exakt filnamn och eventfil gav inga träffar. Även närliggande VPB/AMT- och OMMAX-paket granskades.

En explicit rekonstruktionskandidat byggdes från bevarad OMMAX-helperlogik:

1. Det levererade `detect_accept` och `execute` återanvänds utan ändrade strategivillkor.
2. OMMAX TPO-profil, 200 rows, 70 % VA och ATR14 används som dokumenterad närliggande källa, inte som påstått original.
3. Strikta kompletta 3m-buckets och FVG-buckets 15/30/60 används enligt anropen i AMT-koden.
4. Profilens binindex beräknas först som `(pris−low)/bin_width`. Detta ger samtliga 280 Core trade keys och fyra materiella stopavvikelser.
5. En enda alternativ numerisk tolkning prövades: `(pris−low)/(high−low)*rows`. Den ger 278 gemensamma Core trade keys, två saknade och två extra; större prisavvikelser. Den **avvisas**, trots högre PF. Se normalized_diagnostic.

Detta är två diskreta numeriska tolkningar av en saknad helper, inte en threshold-, session- eller performance-sweep. Ingen trade har korrigerats manuellt för att matcha referensen.

Helper-QA: 50 exakta profiljämförelser och 40 exakta ATR-arrayjämförelser mot den bevarade OMMAX-koden godkändes. Det bevisar överensstämmelse med OMMAX-helpern, inte att den är den förlorade AMT-helpern.

## Kritiska source/execution-frågor före Pine

### 1. Stoppar mellan ticknivåer

Alla 173 Prime-stoppar i den bevarade referensen ligger utanför 0,25-punkters tickgrid. Samtliga targets ligger på tickgrid. Exakt ekonomisk parity kan därför inte antas för verkliga börsorder utan uttrycklig avrundningspolicy och redovisad effekt. Stopparna har **inte** avrundats i denna kontroll, eftersom det annars skulle ändra den frysta referensekonomin.

### 2. Text och kod beskriver inte målurvalet identiskt

Rapporten säger entry→target ≤1,0×prior VA width. Den bevarade koden beräknar `target_va` från **signal-close**, före nästa open. Koden anropar dessutom närmaste FVG bland 15/30/60 och filtrerar sedan `target_tf == 15`; det är inte generellt samma sak som att först söka endast 15m-FVG. Rekonstruktionen bevarar koden. Slutlig spec måste uttryckligen fastställa semantiken innan Pine fryses.

### 3. Gap-stop

Den levererade AMT-executionkoden använder stopnivån även när en bar öppnar genom den. Separat gap-aware diagnostik på de 173 bevarade tradesen hittade **inga** sådana stopp och inga saknade minuter under deras innehav. Det begränsade utfallet gör inte source-koden generellt gap-safe. Ingen alternativ executionserie har ersatt referensen.

### 4. C4 och ZAB

VP_DS180_CANONICAL_v1.py är en äldre strategi med annan entry, stop/trailing, friktion och cooldown. Den är relevant som profil-/eventkälla men är **inte** D00054- eller D00064-generatorn.

För C4 behöver exakt displacementmått, HTF/FVG-aggregering, kausal RelVol-baslinje och ordningen fill/retest/close-invalidation stängas mot source eller en godkänd rekonstruerad regelidentitet. D00052 låser TP till 2R endast när FVG ligger bortom TP; detta får inte tyst ersättas av ett klippt FVG-target.

För ZAB behöver bland annat 15m-RelVol-definitionens denominator/alignment och exakta state-/cooldownövergångar återvinnas. Ingen DS180 balance-gate, sessionsregel eller annan saknad regel har lagts till genom gissning. Originalets 940 trades har inte återskapats i denna körning och dess publicerade PF har inte presenterats som ett nytt testresultat.

## Exakt nästa steg för Projektledaren

1. Tillför originalet `amt_ltf_research_mags.py` (eller paketet som faktiskt innehåller det). Om originalet saknas: lås en explicit reviderad canonical-identitet/avrundningspolicy med spårbara avvikelser; detta är inte ett tekniskt PASS av nuvarande referens.
2. Tillför C4/D00054- och ZAB/D00064-generatorerna från senaste rekonstruktionen, om de finns. Annars komplettera de exakta source-semantikerna ovan innan fortsatt rekonstruktion.
3. Återuppta Gate A. Acceptera inte den numeriskt närliggande Prime-kandidaten som exakt verifierad.
4. Efter verifierade moduler: bygg separat raw ledger och routed ledger, därefter Pine, TV-parity och funded-rerun enligt arbetsordern.

Ingen ändring av A001, A003, ZAC-01 eller modulernas frysta risk 350/500/250 har gjorts. ORB förblir OFF. Operativa filnamn följer arbetsorderns ZAC-prefix; Projektledaren tilldelar vid behov permanent D-ID.

## Källor

- [Arbetsorder](https://docs.google.com/document/d/1smn34ZIZ8AvMj1ZXUL-jNnTIIstgiNHXiYuSzu5pDW0/edit)
- [ZAC-01 freeze](https://docs.google.com/document/d/1RuclrpleQ19ZpXAADk9zTVj6V9Mfakm4sGJS5gKjEbc/edit)
- [A001](https://docs.google.com/document/d/1TZ1hj1qBeOTIC0dDWgrUql-W53fnVxjBs670BsamvXc/edit)
- [A003](https://docs.google.com/document/d/1CfUzcWIWUkP1hKEqb39pYQy5dWnRz4pBmTDKqcL-ZrA/edit)
- [D00054](https://docs.google.com/document/d/1Fpa3lemWf0olqEdNXoInPQ-kl8F8UhiD4iNYsxh7o6E/edit), [D00055](https://docs.google.com/document/d/1jFq1R3qxAeTAhDD_JFU5RJK0BeeTgQEoQ1n-wez2GdI/edit), [D00064](https://docs.google.com/document/d/1GS6poCWcBawmdkk0zcFa10Z9CyTihJhrWXlF7H0mLwE/edit)
- Exakta paket, source-snapshots, käll-ID:n och checksums följer restartpaketet.
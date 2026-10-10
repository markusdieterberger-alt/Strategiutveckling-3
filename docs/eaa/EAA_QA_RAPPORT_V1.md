# EAA - teknisk QA v1

Datum: 2026-10-09; CT-status uppdaterad 2026-10-10. Status: HOLD for promotion. Ingen Pine-fil har kompilerats eller korts i TradingView i detta arbete. Ingen ny strategiprestanda eller funded-sannolikhet ar verifierad.

## Kallor och identitet

- A001 och aktuell A003 lasta fran projektets Drive. Senaste arbetsordern styr EAA-prioriteringen; inga andringar i ZAC, R1 eller frysta strategier.
- HMA: [QuantByBojis publicering](https://www.tradingview.com/script/pjZmjlZB-NQ-HMA-Midday-Strategy/), publik Pine-ID `PUB;f519c1242fb945e5b86b0cc06a3a2d1e`, version 1.0, publicerad 2026-05-08. Full kalltext hamtad och bevarad byte-for-byte inklusive CRLF. Chattextens identitet kan inte jamforas byte-for-byte eftersom chattsokningen endast returnerade sammanfattningar.
- CT: [Crispiginos BACKTEST-publicering](https://www.tradingview.com/script/1kEKmbb9-NQ-MNQ-CT-Scalper-BACKTEST/), publik Pine-ID `PUB;867afbc0326d4786827e49eac073f5d7`, version 1.0, publicerad 2026-04-21. Detta ar INTE den efterfragade indikatorns verifierade original. Filen ar redan `strategy()`, med `pyramiding=20`, och bada smart-exit-trosklarna ar lasta till 16 trots hogst 15 monsterpoang.
- Fulla SHA256, filstorlekar och statiska assertions finns i `evidence/source_and_data_audit.json`. Originalens licens-/forfattarkommentarer ar bevarade. Ingen tredjepartsprestanda ar adoptiv evidens.

## HMA: original och execution-fixed

`EAA_HMA_MIDDAY_ORIGINAL_V1.pine` ar oforandrad publik originalkod, inte en ny rekonstruktion. `EAA_HMA_MIDDAY_EXEC_FIXED_V1.pine` ar en separat exekveringskandidat.

| Omrade | Original | EXEC FIXED | Status |
|---|---|---|---|
| Long-/short-uttryck och inputs | HMA high/low, EMA, ROC3, sessions- och positionsfilter | Samma uttryck och samtliga ursprungliga inputs | VERIFIERAT genom textassertions, inte signalparitet |
| Short | Villkor beraknas, ingen aktiv entry | Fortfarande ingen short-entry | STATISKT GRANSKAT |
| Session | `0830-1545:23456`, implicit borstidszon | Samma session och borstidszon | STATISKT GRANSKAT |
| Sista bar | Entry kan skickas pa sista sessionsbar; flat begars forst nar en senare bar ar utanfor | Inga nya order pa baren som stanger 15:45; annullera alla order och close-all omedelbart pa denna bar | STATISKT GRANSKAT; TradingView-fill ej verifierad |
| Limitorder | Close-limit kan leva vidare efter session | Behalls/reprisas vid ny giltig signal som tidigare; annulleras vid sessionsslut | STATISKT GRANSKAT |
| TP/SL | ATR till ticks via hardkodad 0.25; samma exit-ID for long och inaktiv short | Aktiva long-exit har unikt ID; `syminfo.mintick`; target avrundas ned, stop upp, minst 1 tick | STATISKT GRANSKAT; avrundning ar dokumenterad beteendeskillnad |
| HMA-langd | `len_h / 2`, `len_l / 2` | Explicit `int(...)` for WMA:s heltalslangd; default 10 ger 5 i bada fallen | Statisk typkompatibilitetsfix; ingen konstaterad compiler-run |
| Positioner | Explicit 1 kontrakt; standard-pyramiding | Explicit 1 kontrakt, pyramiding 0; ingen dagskvot | STATISKT GRANSKAT |
| Kostnader/testmiljo | Implicita Pine-defaults | $25 000, $0.50 provision/sida, 1 tick slippage, marginal 5%, magnifier pa, limit-verifiering 1 tick | Testantaganden, inte nya handelsfilter |
| Diagnostik | Plot av avg-price kan vara na fore fill | Originalplot kvar; closedtrades och same-bar-rundturer tillagda | STATISKT GRANSKAT |

Viktigt: HMA tar inte uttryckligen hogst en affar per dag. Ingen sadan regel har lagts till. Sessionen ar 08:30-15:45 Chicago for MNQ, alltsa normalt 09:30-16:45 New York, INTE en antagen 10:30-13:00-session. Chartens visningstidszon andrar inte `time()`-sessionens bortidszon.

Ingen aktiv `request.security` finns i HMA; den kommenterade `open[-1]`-raden exekveras inte. Inga aktiva framtidsindex hittades. Pine v6:s lazy evaluation i befintliga sammansatta uttryck och historikberoende funktioner ar bevarad, inte omskriven. Originalets typfraga kring WMA-langd ska redovisas som compiler-risk, inte som bevisat compilerfel. Originalet far inte fixas tyst.

## Same-bar: viktig begransning

En vanlig Pine-bracket med vilande stop och target ger INTE en generell stop-first-garanti nar bada nivaerna ligger i samma OHLC-bar. TradingViews broker-emulator valjer sin prisvag; Bar Magnifier/Bar detalization kan ge mer intrabardata men inte skapa saknad tickordning. Att efter barens slut byta en redan fylld TP till SL vore efterhandsinformation, inte riktig `strategy.exit()`.

Darfor ar detta krav fortfarande EJ VERIFIERAT i Pine. Same-bar-affarer flaggas; kvarvarande tvetydiga stop/target-traffar ska granskas mot underliggande tidsupplosning. Simulatorns OHLC-lage provar adverse fore favorable och markerar alltid approximation; det ersatter inte TradingViews handelsbok och bevisar inte Pine-paritet. Ingen positiv promotion innan relevant tvetydighet ar upplost eller konsekvensen uttryckligen bedomd.

## CT: portning levererad 2026-10-10, TradingView-test aterstar

Det uppladdade indikatororiginalet har nu hamtats, hashverifierats och bevarats. `pine/eaa/EAA_CT_SCALPER_STRATEGY_V1.pine` ar byggd fran just detta original, med alla sex entrymodeller och oforandrade signaluttryck. Den publika BACKTEST-referensen ovan ar endast historiskt granskningsunderlag och anvands inte av byggskriptet.

Se **[EAA_CT_SCALPER_QA_V1.md](EAA_CT_SCALPER_QA_V1.md)** for aktuell kallidentitet, samtliga andringar, statiska kontroller, syntetiska kontraktstester och begransningar. Full rad-diff och logg finns i `evidence/CT_ORIGINAL_TO_STRATEGY_V1.diff` och `evidence/CT_VERIFICATION_V1.json`. Den nya korningen gav 87 godkanda tester, varav 37 nya CT-tester, samt 25 CT-textkontrakt. Inga nya Pine-kompilerings- eller prestandabevis finns.

Originalets smart exits ar aven har avstangda; oforskjutna HTF-varden och repaint-risk bevaras. Riktiga enpositionsorder, fryst och konsekvent SL/TP, dagsslutsskydd, footprint-datasparr och separat pessimistisk fillkontroll ar tillagda. Native stop-first ar inte garanterat. **[Kort CT-kororder](EAA_CT_DATORPASS_KORORDER_V1.md)** ersatter tidigare uppmaning att hoppa over CT.

## Simulatorns verifieringsstatus

VERIFIERAT: syntetiska unittester och CLI-smoke i lokal Python. Testlogg finns i `evidence/verification.json`. Bland annat: EOD-high-water, intradags-MLL, DLL-dagslas, gap genom flera granser, kostnader, consistency, positionsavrundning, kalenderdagar utan trades, DST, import och seed-reproducerbar block-bootstrap.

EJ VERIFIERAT: verklig TV-export, Pine-kompilering, historiska strateginyckeltal, trade-for-trade-paritet, livefills, kontots exakta avtal/holiday schema och garantier mellan intradagssamplingar. Samtliga replayrapporter har `approximate=true` och `rules_verified=false`.

## Officiella tekniska kallor

- [TradingView strategies, ordertiming, exits, magnifier och export](https://www.tradingview.com/pine-script-docs/concepts/strategies/)
- [TradingView HTF/footprint, Premium/Ultimate och na-data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/)
- [Pine v6 division och marginaldefault](https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-6/)

Referenser kontrollerade 2026-10-09. Dessa dokument beskriver plattformen, inte att vara filer har kompilerats.

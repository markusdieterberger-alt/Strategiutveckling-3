# EAA CT Scalper – QA och ändringsrapport V1

Datum: 2026-10-10. **Status: portning och lokal QA klara; inväntar TradingView-kompilering och test. Ingen prestanda eller liveanvändning är godkänd.**

## Leverans och källidentitet

- Strategi: `pine/eaa/EAA_CT_SCALPER_STRATEGY_V1.pine` – en fristående Pine v6-fil, 1 949 rader  118 129 bytes.
- Enda signalkälla: [det uppladdade indikatororiginalet](https://drive.google.com/file/d/1zsoCvNPmFF6KMVaC5ETRwWF0DnYT2oFO/view), `EAA_CT_SCALPER_INDICATOR_ORIGINAL_FROM_CHAT_2026-10-10.pine` – 1 871 rader, 110 723 bytes.
- Original SHA256: `9fa2463f2b27ae54554ea24290c38b9cd068ac240b61da7ca7b7cf44feed2b30`.
- Strategi SHA256: `c386f4f7d3e30e3ebfe57ebe5e35e40c5560fda88b7f38296405d080ebbcf8e8`.
- Originalets bytes bevaras under `pine/eaa/reference/`. Storlek och hash stämmer med A003:s uppladdningsuppgift. Deklaration, samtliga tolv entrygrenar, sex modeller, footprintdel och avslutande sex alertconditions finns. Strängar och parenteser har strukturellt kontrollerats. Inga tecken på avklippt fil hittades.
- A003 beskriver originalfilen som en transkription från två chattmeddelanden. Byteidentitet mot de tidigare chattmeddelandena eller upphovsmannens egen indikator är **inte** oberoende verifierad. Fullständighet gäller den levererade filen.
- Den separata publika BACKTEST-versionen används **inte** av byggskriptet. Den ligger kvar som äldre granskningsreferens.

## Vad som faktiskt verifierats

`evidence/CT_VERIFICATION_V1.json` innehåller kördatum, Pythonversion, kommandon, exitkoder, hela testloggen och källhashar. Körningen gav **87 godkända unittest-metoder**, varav **37 nya CT-tester**, samt **25 godkända statiska kontrakt**. De tidigare 50 testerna gäller HMA/simulator/import. Python compileall lyckades; det är inte en Pine-kompilering.

Textkontrollerna jämför hela indikator-/featurekedjan, alla 20 ursprungliga inputs, hela entrydelen med enbart orderkropparna bortnormaliserade, modellprioriteten och hela smart-exitdelen. Strategin kan återskapas exakt från det hashbundna originalet och fem mallar. Inga signaltrösklar eller modellparametrar har optimerats.

Syntetiska tester täcker båda riktningarna för alla modeller, prioritet, upptagen position, riktningskonflikt, ingen fill på signalbaren, entry och exit på nästa bar, SL/TP-kollision, negativa priser, tickavrundning, stopgap, avgifter, annullering, data-/tidsblock, återentry, dagsslut, helger, DST och fördröjd rapportering av omedelbar exit. Dessa tester kör en **Pythonmodell av exekveringskontraktet**, inte Pine eller TradingViews broker-emulator. De bevisar inte att Pine-implementationen beter sig likadant.

| Nivå | Resultat |
|---|---|
| Filidentitet, källfullständighet inom uppladdningen, deterministisk byggning | Verifierat lokalt |
| Bevarade signaluttryck/inputs och syntetiska kontrakt | Verifierat enligt ovan |
| Pine-typkontroll, kompilering, resursgränser och runtime | Ej verifierat – kräver TradingView |
| Marknadsdata, footprinttäckning och signalparitet | Ej verifierat – kräver TradingView |
| Verklig affärslista, intrabarordning, avgifter och marginalutfall | Ej verifierat – kräver TradingView |
| PF, netto, equity-DD, funded PASS/FAIL eller lönsamhet | Inte testat; inga sådana resultat levereras |

## Ändringar jämfört med originalet

Varje radändring finns i `evidence/CT_ORIGINAL_TO_STRATEGY_V1.diff`. Tabellen förklarar avsikten; diffen är den fullständiga ändringsförteckningen.

| Del | Ändring och följd |
|---|---|
| Deklaration | `indicator()` ersatt med `strategy()`. Forskningsstatus och källrisker tillagda. Originalets inledande beskrivning och funktionskommentarer bevaras, även äldre formuleringar om fem modeller; koden innehåller sex. |
| Miljö | USD 25 000, fast 1 kontrakt, pyramiding 0, provision USD 0,50 per kontrakt/sida, 1 tick slippage, limitverifiering 1 tick och Bar Magnifier på. Marginal long/short 5% är ett uttryckligt backtestantagande, inte Lucids faktiska marginalavtal. NQ och större storlek kan ge avvisning/marginalingrepp. |
| Beräkning | Bar-close-beräkning, `calc_on_every_tick=false`, `calc_on_order_fills=false`, `process_orders_on_close=false`. Originalets möjliga intrabaralerts ersätts med bekräftade bar-signaler. Historiska uttryck är bevarade; intrabar-/realtimeparitet påstås inte. |
| Protokollinputs | Ny separat EAA-grupp: heltal 1–20 kontrakt, start 2026-09-09 00:00 New York, slut exklusivt 2026-10-09 00:00, footprintspärr på och 1 tick stress-slippage. Första baren kräver standardcandles, MNQ/NQ futures, 1 minut och giltigt datumintervall. `max_bars_back=500` anger historikbuffert, inte testperiod. |
| Signalkedja | Samtliga ursprungliga inputs, indikatorer, HTF-anrop, externa symboler, footprintberäkningar, VRZ-tillstånd, filter, prioritet och kandidat-SL/TP-formler bevaras. Exakt en `request.footprint(50, 70)`. Ingen OHLCV-ersättning för footprint. |
| Sex entrymodeller | FADE → DIV → TRAP → AGG → ABSORB → VRZ, i båda riktningarna. Tolv originala actionkroppar ersätts med råkandidatens modell/riktning/SL/TP. Råkandidater beräknas även när order blockeras; VRZ-tillståndet fortsätter därför enligt originalet. |
| Positionsägande | Visuella `TixEntry`-objekt, ticket-array och ticketmotorns TP-först-resultat tas bort. Faktisk strategi-position och closedtrades är facit. Högst en position eller reserverad entry; inga pålägg, reverseringar eller nya entries på exitbaren. Samtidig long/short-kandidat blockeras. Senare signaler får inte flytta en pågående bracket. |
| Entry | En gemensam market-entry efter bekräftad signal; normalt fill nästa bars öppning plus slippage. Entry och skyddande bracket skickas i samma beräkning, inte först när nästa bar-close ser positionen. |
| SL/TP | Originalets `f_openTicket`-minimiavstånd appliceras en gång på faktiska ordernivåer. SL och TP låses vid signalen. Long-SL rundas ned/TP upp; short-SL upp/TP ned till instrumentets tick. Ogiltiga nivåer blockeras. Avrundningen flyttar nivåerna mindre än en tick: stop längre bort, target svårare att nå men med större utfall om fylld. Detta är inte en generell lägre avkastningsgräns. |
| Gap och orderfel | Faktisk entry kan hamna utanför signalens bracket efter ett gap; detta flaggas, inte raderas i efterhand. Ett uppenbart ofyllt/avvisat market-försök frigör slotten och räknas. Avvikande positionsstorlek, delstängning eller upptäckt likvidation avbryter körningen med runtime-fel. Dessa skydd kräver runtime-verifiering och är ingen full garanti mot alla emulatoringrepp. |
| Dagsslut | Regelbunden New York-session: inga nya signalorder från 16:43; omedelbar close-all vid bar-close 16:44, en minut före publicerad 16:45-gräns. Annullera order, stäng också vid testslut eller `session.islastbar`. Återöppning 18:00 söndag–torsdag; inga weekendentries. Originalets Chicago-baserade signalfilter ändras inte. |
| Smart exits | Ursprungliga score-/tröskelfunktioner bevaras. Båda trösklarna är 16 och högsta score 15: de är redan avstängda i detta indikatororiginal. Eventuell PAT-exekvering är kopplad till riktig close-order men förblir onåbar med originalet. Ingen tyst aktivering. |
| Diagnostik | Separat SL-först-stressbok, råmodell/skickad modell, faktisk exit-tid, netton, footprint- och felräknare tillagda. Tidigare indicator-alerts tas bort; strategy order-fill-meddelanden är endast diagnostiska och saknar broker/webhook-konfiguration. |
| Visuellt | Fyra divergence-markeringar flyttas från bakåtritat pivotdatum till bekräftelsebaren (`offset=0`). Signalberäkningen ändras inte. Övriga ursprungliga plots/dashboard bevaras; faktisk positionsstatus används och aktiv SL/TP visas. Ticketetiketter ersätts av strategins affärsmarkeringar. |

## Konservativ behandling av tvetydiga fills

En bar vars high/low når både låst SL och TP flaggas som **potentiellt tvetydig**, även på entrybaren efter den föregående signalbaren. Hela exitbarens OHLC används; det kan inkludera pris efter en redan inträffad exit och därmed överflagga. Native bracket-order hanteras av TradingView; vi skriver inte om dess affärslista i efterhand.

Den separata stressboken ersätter för denna accepterade affär exitpriset med SL, eller sämre öppningspris vid gap, plus negativ stop-slippage. Vid flera flaggade barer används det sämsta stresspriset. Samma entrypris, riktning, kvantitet och rapporterad provision används; stressnettot är alltid högst native-nettot för samma affär. Stress-slippage-input måste matcha Properties; den ändrar inte verkliga strategiorder.

Detta är en känslighetskontroll för **samma accepterade affärer**, inte en full omkörning med alternativa positionstider, en intradagskurva, funded-simulering eller matematisk gräns för en annan strategi. Stop-först gäller den syntetiska kontrollen, **inte garanterat native Strategy Tester**. Bar Magnifier förbättrar underlaget men undanröjer inte automatiskt alla okända intrabarordningar. Kvarvarande tvetydighet är en öppen QA-punkt innan resultat kan godkännas.

Omedelbar sessions-/datumexit kan bli synlig för skriptet först vid nästa beräkning. Bokningen använder affärens faktiska exit-tid och granskar inte följande bars OHLC som exponering. Finns ingen senare bar kan sista exit saknas i den separata boken tills nästa beräkning. Reconcile closed/audited och exportens antal; native-exporten är facit.

## Bevarade originalbegränsningar och datakrav

- Oförskjutna 5/15/60/240-minutersvärden med `lookahead_off` kan ändras i realtime/efter reload. En confirmed-HTF-variant skulle ändra signalidentiteten och ingår inte. Dagspivots använder föregående dags värden `[1]` med `lookahead_on`. Ingen liveparitet eller generell repaintfrihet påstås.
- `ctMinConf` används inte av originalets entrygate; den dynamiska funktionen börjar på hårdkodat 3. `showVwapBands` är också ett bevarat input utan aktiv koppling till en motsvarande plot. Ingen av dessa ursprungliga egenheter har reparerats.
- Originalets fallback vid saknad footprint (bland annat noll delta, ratio 99 och kvarvarande POC) finns kvar i råsignalerna. Nytillagd orderspärr kräver elva giltiga footprintbarer i följd: ett dataskydd för aktuell bar och tiobars-historik, inte bevis för kvalitet i all äldre pivot-/VRZ-historik. Att slå av spärren är en separat diagnostikkörning, ingen godkänd baskörning.
- Footprint kräver plattformsrättighet och faktisk historiktäckning. Funktionen kan returnera `na`; den bygger köp/säljklassning på underliggande prisrörelser, inte ett verifierat rått aggressorflöde från börsen. Externa USI:TICK, CBOE:VIX, SPY och ES1! är oförändrade; tillgång och semantik måste kontrolleras i TradingView.
- New York/DST är ett uttryckligt tidsantagande; Lucids text använder EST. Ingen full helgdagskalender ingår. Tidigare börsstängning, saknade slutbarer eller datagap kan förhindra stängning i tid. `session.islastbar` är ett extra skydd, ingen garanti. Körningen certifierar inte funded-regler, dagsförlustgränser eller liveberedskap.
- Ursprungliga kommentarer med äldre lönsamhetstal är endast bevarad källtext och utgör inte resultat från detta uppdrag.
- Chartläge och Deep Backtesting har olika historik/starttillstånd. Diagrammets tabell och CSV-plots beskriver chartkörningen; de får inte kopplas till Deep-rapportens affärer utan separat kontroll. Otillräcklig chart-historik betyder en partiell period, inte ett genomfört 30-dagarstest.

## Återstår i TradingView

Följ `EAA_CT_DATORPASS_KORORDER_V1.md`: kompilera, kör det fasta MNQ 1m-protokollet och exportera rapporten. Work ska därefter kontrollera period/täckning, faktiska fills, kostnader, gap, dataspärrar, signalparitet mot exakt original med samma data samt diagram-/Deep-skillnader. En affär per modell behövs för dynamiskt bevis; utebliven modell i sample är inte bevis på fel eller täckning.

Ingen ny testperiod, parameteroptimering, historisk OHLCV-backtest utan footprint, brokerkoppling eller ändring i R1/ZAC/frysta strategier har gjorts.

## Reproduktion och källor

Från reporoten: `python -m eaa.build_ct`, därefter `python -m eaa.verify_ct`. Mallar, tester, testlogg, manifest och full diff finns på EAA-branchen. Pine-filen kräver inga Pythonfiler eller externa importer i TradingView.

Officiella referenser kontrollerade 2026-10-10; de beskriver plattform/regler, inte verifierad körning av denna fil:

- [TradingView – strategier, ordertiming, bracket, kostnader och export](https://www.tradingview.com/pine-script-docs/concepts/strategies/)
- [TradingView – footprint och andra tidsupplösningar](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/)
- [TradingView – repainting och HTF](https://www.tradingview.com/pine-script-docs/concepts/repainting/)
- [TradingView – Deep Backtesting och separat chartkörning](https://www.tradingview.com/support/solutions/43000666265-how-deep-backtesting-works/)
- [Lucid – ordinarie handelstider och tidigare helgstängningar](https://support.lucidtrading.com/en/articles/11404729-allowed-trading-times)

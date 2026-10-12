# AMT Node Proxy V2 DEV — QA

2026-10-12. **Python QA godkänd för den dokumenterade DEV-modellen. Pine ej kompilerad. Ingen promotions-QA PASS.**

## Genomförda kontroller

- Canonical: 2 614 900 rader, 1 918 handelsdagar, 30 kontraktsrullar. Matchande A002-SHA256 för komprimerad fil och CSV. Inga dubbla timestamps, ogiltig OHLC, saknade värden eller priser utanför 0.25-grid.
- 5 791 observerade tids-/kontraktsavbrott nollställer profiler; ingen roll skedde mellan två minuter utan tidslucka. Avbrotten inkluderar normal maintenance och helger, inte bara kvalitetsfel.
- 26 exekverbara tester: volymmassa, HL/CLOSE/TPO-definition, binavrundning, känd tvånodskorridor, frysta framtidsoberoende profiler, A/B-sekvens, gränslikhet, short-symmetri, stop-gap, SL/TP-dubbelträff, target-gap, entrytid, skydd under entryminuten, okänd datalucka, cutoff och dagbootstrap.
- En separat långsam volymfördelning jämfördes med den snabba differensarraymetoden på 100 historiska profilfönster. Max absolut avvikelse i råvolym cirka 1.1e-11 volymenheter.
- De första 50 000 datapunkternas signalprefix återskapades efter att ALLA senare priser ändrats kraftigt. Samtliga 37 HL-signaler och deras frysta nivåer var oförändrade.
- Alla publicerade trades kontrolleras för entry nästa datapunkt, exit efter/vid entry, profil före signal, tickriktiga SL/TP, korrekt R/point/USD-beräkning och högst en position per separat testvariant. Gruppsummeringar stämmer med fullständiga loggar.
- Degraded-datum bevaras. Separat känslighet exkluderar exponering i profil-/signalkälla eller trade; inga datum filtreras bort tyst i huvudresultaten.

D02010 innehåller maskinläsbar köridentitet, D02016 diagnostik och D02018 själva test-/körutskriften. Rapporterade tester är lokala Python-tester, inte Pine-tester.

## Statisk Pine-granskning

Strategin använder 1m-data direkt; inga request.security-anrop, framtida HTF-data eller footprint-antaganden. 150m-fönster kräver obruten historik. Frysta nivåer uppdateras först efter att en episod förbrukats/utgått. A/B avgörs enbart på bekräftade 5m-closes. Ingen lookahead, ingen varip och inga fill-recalculations.

Profilen använder 150 bariterationer plus högst cirka 73 prisbin; inga tick×historik-nästlade profilberäkningar. Arrays allokeras bara vid profilbyggnad. Historikbuffer 200; orderstorlek 1; pyramiding 0; `strategy.risk.max_position_size(1)`. Detta är en resursdesign, INTE bevis för TradingViews faktiska tidsgräns. Full historik kan fortfarande timeouta.

Marketentry skickas vid signal-close. SL/TP är kända och skickas tillsammans med entry. `process_orders_on_close`, `calc_on_every_tick`, `calc_on_order_fills` är avstängda. Closedtrades-export används för same-bar roundtrips. Inga trails, inga efterhandsändrade stops och inga dolda IB-/FVG-filter.

## Rättningar och avvikelser

1. Ny signal vid en föregående trades exitbar-close tillåts när positionen redan är stängd. Tidig Pythonkod använde en för strikt indexjämförelse; den rättades. Resultat omkörda.
2. Flyttalsdamm och exakt platåhantering standardiserades i båda språken, med sex decimalers smoothed volymprecision. Ingen marknadströskel ändrad.
3. Preliminära lokala D010-ID:n ersattes efter att senaste A003/Drive visade andra samtidiga projektleveranser. Slutliga ID:n är separat reserverade i A003. Inga befintliga filer skrevs över.
4. Native TradingView-fills kan ge TP först vid dubbelträff. Python väljer SL först om open inte redan avgör ordningen. TV:s slippage läggs inte på limits på samma sätt som Pythonreferensen; gynnsamma target-gap kan också ge olika fill. De är öppna parityfrågor, inte en verifierad port.
5. Python gap-exit använder första återkomst-open; Pine utan tickberäkning kan reagera först vid återkomstbarens close. Sådana trades är uttryckligen datalucks-QA och måste utredas/exkluderas i motsvarande paritydiagnostik.
6. Open-trough-DD i CSV är en konservativ adverse-excursion-serie jämförd med stängd-equity-toppar, INTE en exakt tickbaserad peak-to-trough open-equity/DD eller funded-riskberäkning. Closed-trade DD är separat redovisad. Full funded-open-equity kräver senare detaljvalidering.

## Gräns för slutsatsen

Den här QA:n visar att Pythonmodellen genomför de specificerade reglerna under de testade antagandena och att resultaten kan reproduceras. Den visar inte sann tickvolym, verklig orderprioritet, Pine-kompilering, full Pine-parity, aktuell Lucid-regeluppfyllelse eller lönsamhet på orörd framtid. Se separat D02012.

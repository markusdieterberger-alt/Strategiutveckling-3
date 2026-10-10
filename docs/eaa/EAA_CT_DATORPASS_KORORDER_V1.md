# EAA CT – kort körorder V1

**Koden är färdig för kompileringstest. Ingen TradingView-körning är ännu verifierad. Behåll alla signalinputs.**

1. Öppna `CME_MINI:MNQ1!`, **1 minut**, vanliga candles, full/elektronisk session, back-adjustment av. Visa tider i **America/New_York**. Pine-footprint kräver Premium/Ultimate och tillgängliga data.
2. Öppna `EAA_CT_SCALPER_STRATEGY_V1.pine` från projektledarens inkorg, kopiera **hela filen**, klistra in i Pine Editor och välj **Add to chart**. Filen innehåller allt; inga andra kodfiler behövs. Vid fel: fotografera hela feltexten och radnumret, lämna tillbaka till Work och avbryt denna fil.
3. Behåll defaults: **1 kontrakt**, start **9 september 2026 00:00**, slut **9 oktober 2026 00:00 exklusivt**, footprintspärr på, stress-slippage 1 tick. Properties: **USD 25 000; USD 0,50 provision per kontrakt/sida; 1 tick slippage; limitverifiering 1 tick; marginal 5%/5%; pyramiding 0; Bar Magnifier på**. Om UI i stället visar **Bar detalization**, behåll tillämpad inställning och ta bild. Inga extra tick-/fill-/on-close-recalculations.
4. Öppna **Strategy Tester / Strategy report**. För hela 30-dagarsprovet: välj rapportintervallet **8 september–10 oktober 2026** i Deep Backtesting och **Update report**; datumfiltret i koden begränsar själva handeln till 9 september–8 oktober. Det extra dygnet före ger uppvärmning och efter ger tid att bokföra slutexit. Om Deep eller footprint inte fungerar: exportera det som finns, ta felbild och stoppa. Förkorta inte perioden eller byt signalkälla.
5. Ladda ned **hela rapporten som XLSX**. Om bara CSV erbjuds: exportera **Trades/List of trades** och **Metrics/Performance**. Namn: `EAA_CT_V1_MNQ1_20260909_20261008_DEEP`. Ta bilder av **Inputs, Properties, rapportens period/symbol och EAA-tabellen**. Tabellen på diagrammet gäller chartkörningen, inte Deep-rapporten; bilden ska därför märkas **CHART**. Om enkelt tillgängligt: exportera även diagramdata som `EAA_CT_V1_CHART.csv` för SL/TP- och stresskontrollen.

Lämna exporter och bilder i [00 – Inkorg till Projektledare](https://drive.google.com/drive/folders/1W6dB7lc6t6st2oKr4zSEj9wfwdUVaaIG) eller bifoga till Work från mobilen. Vid noll affärer: bild av rapporten och EAA-tabellen räcker för att Work ska utreda; ändra inga parametrar vid datorn.

**Work gör resten:** kontroll av täckning, originalsignalernas paritet, same-bar/gap, kostnader och resultat. Native fills är inte garanterat SL-först; den separata stressboken är en kontroll. HTF/reload-risk är bevarad från originalet. Ingen live- eller fundedstart i detta pass.

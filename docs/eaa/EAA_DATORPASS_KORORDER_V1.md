# EAA - Datorpass kororder v1

**Ingen optimering. Ingen felsokning pa datorn. Pine ar annu inte TV-kompilerad.**

1. Oppna `CME_MINI:MNQ1!`, vanliga candles, **15 minuter**, full/elektronisk session. Visa klockan i **America/New_York**. Back-adjustment **av**. Detta ar ett valt testprotokoll, inte bevis pa samma rollserie som canonical CSV.
2. Klistra in **`EAA_HMA_MIDDAY_ORIGINAL_V1.pine`** i Pine Editor och valj **Add to chart**. Behall alla signalinputs oforandrade. Vid compilerfel: ta bild med filnamn, rad och hela feltexten, avbryt denna fil. Andra inte originalet.
3. Oppna panelen under chart: **Strategy Tester / Strategy report**. Testperiod **2025-10-01 till 2026-09-30**, helst Deep Backtesting. Properties: **$25 000, USD, 1 kontrakt, $0.50 provision per kontrakt/sida, 1 tick slippage, marginal long/short 5%, pyramiding 0, Verify price for limit orders=1 tick, Bar Magnifier/Bar detalization pa**, inga extra recalc/on-close-val. Originalkoden ar oforandrad; dessa ar dokumenterade jamforelseegenskaper.
4. Ladda ned **hela XLSX-rapporten** via rapportmenyn om den finns. Annars exportera **List of trades/Trades CSV** och **Performance/Metrics CSV** var for sig. Namn: `EAA_HMA_ORIGINAL_MNQ15_20251001_20260930`. Ta en bild av Inputs + Properties och rapportens period/symbol. Bevara antal, PF, netto och max equity-DD.
5. **CT hoppas over nu:** exakt indikatororiginal saknas. Kor INTE `CT_SCALPER_PUBLIC_BACKTEST_SOURCE_V1.pine` som ersattning. Nar korrekt CT-port finns ar den nummer2: MNQ1!, 1m, forst 30 dagars smoke, sedan faststalld period; en ny exakt kororder ska folja filen.
6. Ta bort originalet fran chart. Kor **`EAA_HMA_MIDDAY_EXEC_FIXED_V1.pine`** med samma symbol, period, inputs och Properties. Exportera som `EAA_HMA_EXEC_FIXED_MNQ15_20251001_20260930`. Ingen parameterandring aven om resultatet ar samre.
7. Lamna exporter och bilder till Work fran mobilen. Om export inte fungerar: bilder av hela Metrics/Overview, Trades-listans borjan/slut och radantal, Inputs/Properties samt period/symbol. Bilder ersatter INTE komplett handelslista. Vid noll affarer, runtime-/compilerfel eller fel session: bild och stopp, ingen datorfelsokning.

**Kvar for Work:** jamfora affarer, kontrollera same-bar-fills och intradagsequity, kora funded-scenarier. Ingen live- eller fundedhandel ar godkand genom denna kororder.

Resultatmall: fil/version; symbol; timeframe; tidszon; period; antal; PF; netto; max equity-DD; exporter bifogade; feltext. GUI-namnen kan skilja sig mellan TradingViews aktuella och aldre rapportlayout.

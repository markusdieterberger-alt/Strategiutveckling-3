# D02001 — AMT Node Proxy V2 DEV: forskningsrapport och överlämning

2026-10-12 · Canonical MNQ 2019-05-05–2026-10-02 · **Beslut: REVISE. Ingen promotion till live/funded.**

Den prövade frysta HVN/LVN-modellen visar inte den riktningsfördel som krävs. I HL-huvudprofilen är 60m target-minus-mirror-asymmetrin negativ i samtliga åtta modell/session/riktningsgrupper. Några handelsvarianter har positivt DEV-netto, men ingen konstruktion/familj/session klarar hela robusthetskedjan. Populationerna är dessutom mindre än protokollets minimikrav. Detta underkänner denna operationalisering som färdig strategi; det bevisar inte att all AMT är omöjlig.

Pine v6-prototypen är skriven tidigt, men **INTE kompilerad eller exekverad**. TradingView-navigering timeoutade två gånger, även efter återställning. Omfattande strategioptimering, oberoende validering och funded-simulering är därför **inte utförda**, enligt arbetsorderns hårda Pine-grind. Separata statusrapporter redovisar detta utan att ersätta testbevis med statisk granskning.

## Var projektledaren hittar allt

**Drive:** Strategiutveckling → [00 – Inkorg till Projektledare](https://drive.google.com/drive/folders/1W6dB7lc6t6st2oKr4zSEj9wfwdUVaaIG). Sök på **D02001–D02019**; serien reserverades i A003 för detta arbete. Börja med denna rapport, körordern D02013 och Pine D02003.

**GitHub:** [research/amt-node-proxy-v2-dev-2026-10-12](https://github.com/markusdieterberger-alt/Strategiutveckling-3/tree/research/amt-node-proxy-v2-dev-2026-10-12). Kod: `research/amt-node-v2/` och `pine/amt-node-v2/`. Dokument: `docs/amt-node-v2/`. Fullständiga stora CSV-loggar ligger komprimerade i git och är direkt läsbara med pandas; Drive får även vanliga CSV-versioner.

**A003:** [operativ status och fortsatt körorder](https://docs.google.com/document/d/1CfUzcWIWUkP1hKEqb39pYQy5dWnRz4pBmTDKqcL-ZrA). CT/EAA/EAB, R1, ZAC och deras frysta resultat är orörda. Nya D-ID:n behövdes eftersom parallella CT/EAB-leveranser hade tilldelats de preliminära lokala numren.

| ID | Innehåll |
|---|---|
| D02001 | Denna forskningsrapport, baseline och beslut |
| D02002 | Exakta V2 DEV-regler och dokumenterade skillnader från låst V1 |
| D02003 | Pine v6 strategy-prototyp, två valbara A/B-familjer |
| D02004 | Python-generator och konservativ fillmotor |
| D02005 | Samtliga 35,546 eventrader, även OFF-session och blockerade utfall |
| D02006 | Samtliga 2,095 trades över tolv separata testvarianter |
| D02007 | Fenomen per år/period, sida, session, konstruktion och 30/60/120m |
| D02008 | Baseline per år/period samt 1/2/3p-kostnader |
| D02009 | Matchade vanliga balanskontroller och pseudo-korridorer; även saknade matchningar |
| D02010 | Körmanifest, datakontroller, parametrarnas källhashar och gate-funnel |
| D02011 | 26 automatiserade handräknade tester |
| D02012 | Separat validerings-/Pine-/funded-status |
| D02013 | Kort körorder för nästa TradingView-pass |
| D02014 | QA-rapport och kända begränsningar |
| D02015 | Optimeringsrapport: faktiskt utförda känsligheter och spärrad parameteroptimering |
| D02016 | Kvantiler, regimer, IB, profilöverensstämmelse, matchning och degraded-sensitivitet |
| D02017 | Reproducerbar generator för fördjupad QA/diagnostik |
| D02018 | Faktiska test- och körutskrifter samt webbläsarblocker |
| D02019 | Leveransmanifest med SHA256, byteantal och Drive-länkar |

## Tidigare forskning och vad den betyder

Det låsta [Node-to-Node V1-protokollet](https://docs.google.com/document/d/1bL5JgsSCJtm59zgjFUt8h_dAFXn3wl9a6l76Z3c69YY/edit) skilde redan mellan fenomen, implementation och validering. Denna leverans ändrar inte V1. Den gör tidigare odefinierade detaljer mekaniska i en separat V2 DEV: origin-bin, binankare/ties, frysning/cooldown, LVN-band, mitt kontra proximal kant, 30m-balanskontroll och exakt kostnads-/gapmodell. Baseline körs diagnostiskt även om fenomenet underkänns; detta avviker uttryckligen från V1:s sekventiella stopp före tradingtest.

[D00037](https://docs.google.com/document/d/1K2FMgmUkGblgj55V9Mlz9765T6Kne_CO1o43vzjTvnU/edit) och [AMT Micro-rapporten](https://drive.google.com/file/d/1jLykE4WDjTqINUjuEvydmJsNgnLjRt4S/view) gav användbar kontext, men deras lovande Micro Core-resultat (n280, PF1.492, +0.0795R) använder ett externt FVG-mål och utgör inte bevis för ren HVN→HVN. Den tidigare 180m-modellens PF1.42 föll till cirka 0.671 när stop-gap och A001-kostnader korrigerades i [C0006 QA](https://docs.google.com/document/d/1vHiBNrbEes1E0Tav4i176gRZrT32-zOTAqHQLspk5CA/edit). Därför är realistiska fills centrala här. Den alternativa D00037-QA-länk som fanns i protokollet returnerade 404; den har inte påståtts vara läst.

Extern primär dokumentation stöder profilens beskrivande användning, inte en garanterad magnetedge. [Sierra Chart](https://www.sierrachart.com/index.php?ID=141&Name=Volume_by_Price&page=doc/StudiesReference.php) skiljer transaktionsvolym per pris från jämn fördelning av aggregerade staplars volym. [TradingView](https://www.tradingview.com/support/solutions/43000502040-volume-profile-indicators-basic-concepts/) beskriver historiska volymprofiler som reaktiva nivåbeskrivningar. [Cont, Kukanov och Stoikov](https://arxiv.org/abs/1011.6402) finner samband mellan orderboksobalans och kortsiktiga prisförändringar i 50 amerikanska aktier; deras data är inte MNQ och resultatet verifierar inte vår OHLCV-nodmodell. Min slutsats är därför att marknadsmikrostruktur gör hypotesen rimlig att mäta, men inte motiverar att kalla minutvolym för orderflöde.

## Data och metod

A002:s **MNQ_CANONICAL_1M_V1_0**: 2,614,900 rader, 1 918 handelsdagar, 30 rullar, 2019-05-05 22:03 UTC–2026-10-02 20:59 UTC. Båda SHA256 matchar. Inga duplicerade tider, ogiltiga OHLC, NaN eller off-grid-priser. 5 791 tids-/rollavbrott observeras inklusive normala marknadsstängningar; profiler får aldrig passera dem. Degraded-datum finns kvar och känslighetsredovisas.

Profil: 150 kontinuerliga 1m-bars, beslut endast efter komplett 5m-close. HL lika volym per nått bin; CLOSE all volym på close; TPO en tidsenhet per bin/minut. Dessa är tre olika approximationer, **inte true VAP eller footprint**. Frysta episoder kräver origin-HVN, tydlig LVN och nästa HVN, 150m mellan nya frysningar. A kräver probe + två ytterligare destinations-closes; B återgång inom tre bars innan A. Följande open är första möjliga entry. Fenomenmål är HVN2-mitt/POC; ordermål A är HVN2:s proximala kant. Exakta avrundningar och alla val finns i D02002.

EU och NY undersöks separat med IANA/DST. Alla 2019–2026-resultat är **redan exponerad DEV**. Ingen årsdel kallas OOS. Konfidensintervall är 1 000 bootstrapdrag av handelsdagar med fast seed, inte ett korrigerat multipeltest eller nytt oberoende bevis.

## Fenomen: target mot lika avlägsen mirror

60 minuter, HL, båda nivåerna lika långt från nästa open. Positivt tal skulle gynna nodmålet. Alla sannolikheter, asymmetrier och CI nedan är procent/procentenheter; `side=1` long och `-1` short. Dubbelträff utan avgörande open räknas adverse först. Censurerade fönster utesluts ur respektive horisont men finns i eventloggen.

| family | cohort | side | n | target_first | mirror_first | asymmetry | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | EU | -1 | 180 | 44.444 | 53.333 | -8.889 | -22.778 | 5.659 |
| A | EU | 1 | 167 | 46.108 | 50.299 | -4.192 | -18.566 | 9.639 |
| A | NY | -1 | 60 | 40.000 | 55.000 | -15.000 | -38.333 | 10.000 |
| A | NY | 1 | 68 | 44.118 | 50.000 | -5.882 | -29.412 | 16.176 |
| B | EU | -1 | 57 | 43.860 | 45.614 | -1.754 | -23.214 | 22.807 |
| B | EU | 1 | 80 | 37.500 | 60.000 | -22.500 | -42.500 | -1.250 |
| B | NY | -1 | 51 | 41.176 | 50.980 | -9.804 | -35.294 | 15.686 |
| B | NY | 1 | 39 | 43.590 | 53.846 | -10.256 | -38.462 | 20.513 |

Ingen av dessa åtta grupper når 300 giltiga events. Ingen har positivt konfidensintervall helt över noll. Att en negativ delgrupp har CI under noll ger inte rätt att promovera en inverterad efterhandsstrategi. 30/120m, varje år och perioder finns i D02007; MFE/MAE, avstånd, tid och signed 5/15/30m return-kvantiler i D02016.

**Signalernas geometri är ett konkret implementeringsproblem:**

| family | cohort | signals | valid_geometry | valid_phenomenon |
| --- | --- | --- | --- | --- |
| A | EU | 673 | 327 | 347 |
| A | NY | 376 | 120 | 128 |
| B | EU | 440 | 137 | 137 |
| B | NY | 272 | 90 | 90 |

Många signaler kommer när det gamla målet inte längre ligger framför priset eller när SL/TP inte omsluter signal-close. A NY har 376 signaler men bara 120 giltiga ordergeometrier. B:s globala gamla POC ligger ofta åt fel håll. Loggarna behåller dessa fall; de försvinner inte ur signalpopulationen. Det förklarar en del av den låga handelsfrekvensen, men skapar inte i sig en ny lönsam lösning.

## Balans, pseudo-korridor och IB

Vanlig lokal balans fryser tidigare 30m high/low och använder samma acceptans-/rejectionsekvens. Matchningspoolen begränsas till profiler utan kvalificerat nodpar. Nod- och kontrollhändelser matchas på familj, år, sida, session, 30m klockblock, ATR inom faktor två och profilålder ±30m. Kontrollutfallet använder nodhändelsens exakta initiala avstånd.

386 av 702 giltiga HL-events har en vanlig balansmatch; 646 har pseudo-match. Vissa 60m-fönster censureras, så tabellens n kan bli mindre. Matchning sker med återläggning, har inte perfekt kovariatbalans och är deskriptiv. Ingen matchad lift ges ett påhittat oberoende p-värde.

| control | family | cohort | n | unique_control_events | node_asymmetry | control_asymmetry | mean_lift |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BALANCE | A | EU | 216 | 172 | -5.556 | -14.352 | 8.796 |
| BALANCE | A | NY | 66 | 60 | -18.182 | -19.697 | 1.515 |
| BALANCE | B | EU | 61 | 58 | -18.033 | 0.000 | -18.033 |
| BALANCE | B | NY | 42 | 38 | -2.381 | -50.000 | 47.619 |
| PSEUDO | A | EU | 322 | 285 | -6.211 | -8.385 | 2.174 |
| PSEUDO | A | NY | 125 | 118 | -11.200 | -11.200 | 0.000 |
| PSEUDO | B | EU | 116 | 107 | -23.276 | -23.276 | 0.000 |
| PSEUDO | B | NY | 83 | 77 | -9.639 | -2.410 | -7.229 |

A EU är bättre än sin svaga balanskontroll men har fortfarande negativ absolut asymmetri. B NY:s stora relativa lift bygger på 42 matchade events och en mycket dålig kontrollpopulation. Det är inte ett positivt nodbevis. Pseudo-korridoren skiljer generellt lite eller inget från nodhändelserna på matchat avstånd.

IB 18:00–18:59 NY respektive 00:00–00:59 Stockholm klassificeras endast efter 60 verkliga minuter; 1 823 kompletta IB-fönster per definition finns. Alignment, nivåavstånd/ATR och IB-width/prior full day range finns i loggen. D02016 redovisar marginala IB-grupper och deskriptiva volatilitetskvartiler. **Ingen inkrementell IB-gate väljs**, eftersom basfenomenets grind inte passerats. Ett positivt IB-underurval skulle annars vara efterhandsselektion. Ingen IB används som obligatoriskt TP.

## Baseline före optimering

Varje rad är en **separat** konstruktion/familj/session, 1 MNQ, högst en position i den varianten. Summan av alla loggar är inte en verifierad gemensam portfölj. Basfriktion: $1 RT-kommission + en tick adverse per sida = nominellt 1 punkt RT. Python debiterar även limitexit den extra konservativa tickkostnaden. R mäts mot planerad risk vid signal-close; inga signaler får väljas bort retroaktivt därför att nästa open gapar.

| construction | family | cohort | n | trades_per_day | PF | mean_R | net_usd | closed_DD_USD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CLOSE | A | EU | 299 | 0.156 | 0.574 | -0.291 | -664.000 | 844.500 |
| CLOSE | A | NY | 93 | 0.048 | 1.127 | -0.310 | 114.000 | 352.500 |
| CLOSE | B | EU | 255 | 0.133 | 0.643 | -0.101 | -1071.500 | 1111.500 |
| CLOSE | B | NY | 152 | 0.079 | 0.538 | -0.149 | -1737.000 | 1862.500 |
| HL | A | EU | 327 | 0.170 | 0.746 | -0.203 | -558.500 | 648.000 |
| HL | A | NY | 120 | 0.063 | 1.063 | -0.280 | 97.500 | 613.000 |
| HL | B | EU | 137 | 0.071 | 0.910 | -0.101 | -116.500 | 333.000 |
| HL | B | NY | 90 | 0.047 | 1.087 | 0.068 | 149.000 | 472.500 |
| TPO | A | EU | 320 | 0.167 | 0.560 | -0.227 | -1204.500 | 1215.500 |
| TPO | A | NY | 121 | 0.063 | 0.559 | -0.260 | -1023.500 | 1179.500 |
| TPO | B | EU | 125 | 0.065 | 0.922 | -0.023 | -100.000 | 502.500 |
| TPO | B | NY | 56 | 0.029 | 1.207 | 0.017 | 186.500 | 401.500 |

PF på pengar och medel-R kan ha olika tecken eftersom riskavståndet varierar mellan trades. Exempelvis A NY har positivt dollarresultat men negativt genomsnittligt R. Ingen riskstorleksoptimering används för att dölja detta. `trades_per_day` dividerar med samtliga 1 918 canonical-handelsdagar, inte bara dagar med signal.

**HL per huvudperiod och 2026:**

| family | cohort | period | n | PF | mean_R | net_usd |
| --- | --- | --- | --- | --- | --- | --- |
| A | EU | 2019-2022 | 150 | 0.758 | -0.154 | -199.000 |
| A | EU | 2023-2024 | 103 | 0.557 | -0.289 | -307.500 |
| A | EU | 2025-2026 | 74 | 0.924 | -0.184 | -52.000 |
| A | EU | 2026 | 36 | 0.817 | -0.412 | -79.000 |
| A | NY | 2019-2022 | 58 | 0.485 | -0.388 | -441.500 |
| A | NY | 2023-2024 | 24 | 0.551 | -0.504 | -144.000 |
| A | NY | 2025-2026 | 38 | 2.841 | 0.026 | 683.000 |
| A | NY | 2026 | 14 | 1.914 | -0.119 | 222.000 |
| B | EU | 2019-2022 | 75 | 0.714 | -0.173 | -208.000 |
| B | EU | 2023-2024 | 36 | 1.333 | -0.028 | 100.000 |
| B | EU | 2025-2026 | 26 | 0.968 | 0.008 | -8.500 |
| B | EU | 2026 | 10 | 0.833 | 0.063 | -23.000 |
| B | NY | 2019-2022 | 47 | 1.180 | 0.150 | 120.000 |
| B | NY | 2023-2024 | 24 | 0.605 | -0.062 | -217.500 |
| B | NY | 2025-2026 | 19 | 1.495 | 0.029 | 246.500 |
| B | NY | 2026 | 7 | 2.192 | 0.356 | 273.000 |

A NY:s PF2.841 år 2025–2026 bygger på endast 38 trades och föregås av negativa äldre perioder. B NY har 7 trades 2026. TPO A NY misslyckas trots att HL A NY ser bättre ut senare; CLOSE B NY är svag. Ingen variant klarar protokollets hela krav på periodrobusthet och konstruktion.

**HL kostnadsstress, samma trades:**

| family | cohort | cost_points | PF | net_usd |
| --- | --- | --- | --- | --- |
| A | EU | 1 | 0.746 | -558.500 |
| A | EU | 2 | 0.530 | -1212.500 |
| A | EU | 3 | 0.383 | -1866.500 |
| A | NY | 1 | 1.063 | 97.500 |
| A | NY | 2 | 0.915 | -142.500 |
| A | NY | 3 | 0.790 | -382.500 |
| B | EU | 1 | 0.910 | -116.500 |
| B | EU | 2 | 0.726 | -390.500 |
| B | EU | 3 | 0.578 | -664.500 |
| B | NY | 1 | 1.087 | 149.000 |
| B | NY | 2 | 0.983 | -31.000 |
| B | NY | 3 | 0.887 | -211.000 |

2/3p är extra kostnadsavdrag på frysta fills, inte en kö-/likviditetssimulering. Årsvis win rate, medelvinst/förlust, R och drawdown finns i D02008. Huvud-HL har sju tvetydiga SL/TP-minuter. Över alla tolv varianter finns 47 sådana fall, ett dataluckstrade och 37 entries där next-open redan passerat target; inget av detta väljs bort efteråt. Degraded-exklusion ändrar inte slutsatsen: HL A EU n324, PF cirka0.746, övriga HL-varianter oförändrade.

Closed-trade-DD ovan är verifierat från loggen. Det extra `open_trough_DD_points` i CSV mäter observerad adverse excursion mot stängda equity-toppar och är **inte exakt tickbaserad open-equity-DD**. Det får inte användas som ett färdigt funded-riskmått.

## Mätkänslighet och Pine-feasibility

På 4 213 identiska HL-fönster som senare gav någon signal, även utanför kohorterna, jämfördes nodlägen utan att välja vinnande trades:

| construction | n | median_poc_delta_bins | corridor_available | same_side | lvn_within_one_bin |
| --- | --- | --- | --- | --- | --- |
| CLOSE | 4213 | 1.000 | 43.318 | 33.159 | 22.146 |
| TPO | 4213 | 0.000 | 56.231 | 54.522 | 49.656 |

Procentkolumnerna visar tillgänglig korridor nära samma origin-close, samma riktning respektive LVN inom en HL-binbredd. CLOSE upprepar alltså samma riktning och ungefärliga LVN i bara cirka22 procent, TPO i cirka50 procent. POC kan ändå ligga närmare. Detta hindrar att tolka resultatet som ett stabilt, datakällsoberoende volymnodfenomen.

Pine-prototypen använder en differensarray: cirka150 baroperationer plus högst cirka73 bin per profil, ingen footprint och inga lower-timeframe-requests. 26 handräknade tester, 100 oberoende profilkontroller och 37 prefixsignaler passerade Python-QA. Men [TradingViews resursbegränsningar](https://www.tradingview.com/pine-script-docs/writing/limitations/) måste prövas genom faktisk körning. [Native broker-emulatorns OHLC-ordning](https://www.tradingview.com/pine-script-docs/concepts/strategies/) är inte vår stop-first-regel. D02012/D02014 listar alla öppna skillnader, inklusive limit-slippage, gap och data/roll. Statisk kodgranskning räknas inte som kompilering.

## Beslut och fortsättning

**REVISE för forskningsspåret; ingen kandidat promoveras.**

- **PHENOMENON:** den specificerade V2-transfer/rejection-hypotesen får inget robust stöd; allmän AMT är inte motbevisad. Små populationer, negativa mirror-effekter och konstruktionsskillnader hindrar promotion.
- **IMPLEMENTATION:** confirmationen förbrukar ofta målsträckan; gammal global POC är ofta felvänd. Stop/fillproblem från äldre forskning har behandlats konservativt. Ny mekanisk version får undersöka detta efter Pine-grinden, med alla ändringar registrerade före körning.
- **VALIDATION:** faktiskt Pine-test, parity och orörd framtid saknas. Ingen SIM-FWD-period har uppfunnits. TRUE FWD kan börja först efter framtida kandidatfrysning och exponeringskontroll.

Nästa konkreta datorpass är D02013: klistra in D02003 på MNQ 1m, kompilera, kör HL/A/NY och exportera trades, Properties och QA-plots. Work jämför därefter signaler och fills och stänger bara de gates som fått bevis. Ingen omfattande optimering eller funded-simulering startas dessförinnan. Om grundporten inte fungerar ska implementationen rättas, inte ersättas med en annan ekonomisk logik för att få snygg parity.

## Reproducera utan TradingView

Python 3.12.14, pandas 2.2.3, NumPy 2.3.5. Hämta canonical från [A002:s Drive-fil](https://drive.google.com/file/d/1TYXUr5ZRrt7TevcI1URJGt6SYdWhlhBm/view); lägg inte marknadsrådata i publikt git. Från repositoryroten:

```bash
python research/amt-node-v2/D02011_tests.py
python research/amt-node-v2/D02004_research.py --data /absolute/path/MNQ_CANONICAL_1M_V1_0.csv.gz --out research/amt-node-v2/results
python research/amt-node-v2/D02017_qa_diagnostics.py --data /absolute/path/MNQ_CANONICAL_1M_V1_0.csv.gz
```

Kod och data-SHA finns i D02010/D02019. Den sista publicerade körningen skapade 35,546 eventrader och 2,095 trades på cirka 93.4 sekunder lokalt. Reproduktion av Python är inte TradingView-kompilering eller performancevalidering.

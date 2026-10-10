# EAA Strategy Validation Factory v1 - delleverans

Datum: 2026-10-09. Leveranskontroll uppdaterad 2026-10-10. **Status uppdaterad 2026-10-10: CT-KOD OCH LOKAL QA LEVERERADE / TRADINGVIEW-TEST ATERSTAR / INGEN LIVE-PROMOTION.**

## Levererat

- Ofordarvad publik HMA originalfil och separat execution-fixed med oforandrade long-filter och inputs, inga short-entries.
- Teknisk QA med exakta andringar, kallidentiteter, repaint-/HTF-/same-bar-risker och tydliga verifieringsnivaer.
- Ateranvandbar Python-simulator med CSV/XLSX-import, EOD-trailing, intradagsmarkering, mjuk DLL, profit-stop, consistency, kontrakts- och kostnadsscenarier, rullande fonster och seedad dagblock-bootstrap.
- 50 godkanda automatiska tester, CLI-smoke med 8 kostnads-/storleksscenarier och block-bootstrap, kallhashar och datainventering. Testlogg anger faktisk Pythonversion, kommandon, exitkoder och antal tester. Alla prestationssiffror i smoke-filen ar syntetiska.
- CT-strategi fran det exakta uppladdade indikatororiginalet, separat CT-QA, full diff och 37 nya CT-tester. Den samlade senaste testsuiten ger 87 godkanda tester.
- Kort datorpass-kororder: HMA ORIGINAL, CT, HMA EXEC FIXED. CT:s separata kororder anger MNQ 1m och fast 30-dagarsprov. Ingen optimering vid datorn.

## Inte levererat som klart

**CT-konverteringen ar nu levererad:** tidigare blockerande kallkod finns nu som en uppladdad transkription av indikatorn. Filen ar hashverifierad mot A003 och bevarad. Strategin har samtliga sex modeller; publika BACKTEST-koden anvands inte. [Aktuell CT-QA och alla andringar](EAA_CT_SCALPER_QA_V1.md). Identitet mot de tidigare chattmeddelandena eller upphovsmannens egen indikator ar fortfarande inte oberoende byteverifierad.

**Pine-/prestandavalidering:** ingen TradingView-kompilering eller Strategy Tester-korning gjord. Inga verkliga PASS/FAIL-tal, PF eller optimal kontraktsstorlek finns. Det som korts ar syntetiska programkontroller, inte historisk strategivalidering. En Pine-kompatibilitetsfix ar aldrig compilerbevis.

**Konservativ TP/SL-ordning:** native stop/target-brackets kan inte lova stop-first i en okand OHLC-sekvens. Kvarvarande filltvetydighet ar en synlig QA-gate, inte maskerad av Bar Magnifier. Simulatorns konservativa OHLC-envelope ar uttryckligen approximativ.

## Regelskillnader som hanterats

- Senaste orderns $550 profit-stop finns i en egen EAA-profil. Aldre A003:s $500 realiserade stop bevaras separat. A001 har inte skrivits om.
- LucidFlex har aktuell valbar DLL ON/OFF; soft breach/dagslas ar inte automatiskt account FAIL. Projektets $600 ar inte certifierat som det individuella Flex-avtalets belopp.
- Strikt 50% consistency utan leverantorens cushion anvands konservativt; kalender, helgdagar, EST/DST och exakta kontovillkor kravs fore officiella slutsatser.

## Tillgangliga data

MNQ-masterfilen innehaller **355 342 rader**, fran 2025-10-01 00:00 UTC till 2026-10-01 19:21 UTC. Grundkontroll: inga intilliggande timestampdubbletter, osorterade rader, ogiltig OHLC, off-tick-priser eller negativ volym. 260 luckor over en minut inkluderar normala stangningar och ar inte klassade som datafel. Filen ar INTE canonical-serien och har inte footprintdata.

metadata/manifest avser Databento-jobbet GLBX-20261003-KGLJVRFCYK, OHLCV1m MNQ.FUT. Vid forsta arbetspasset saknades historikfilen. Den 2026-10-10 blev en kopia tillganglig: verifierad storlek 387 681 110 bytes och SHA-256 `3b5e1a64723ad5dbb0753922d9b925075eef07fa6a4a032d9b11a4cddc45f140`, identiskt med manifestet. En andra uppladdning av samma fil misslyckades, men behovs inte om den avser samma bytes. Ingen historisk strategikorning eller ny radbaserad kvalitetskontroll av denna fil har gjorts inom leveranskontrollen. OHLCV-filen ersatter inte CT:s footprintdata eller TradingViews exekveringsfacit.

## Nasta faktiska steg

1. Kor det korta [CT-datorpasset](EAA_CT_DATORPASS_KORORDER_V1.md): klistra in hela strategin, kompilera, kor rapporten och exportera. Ingen ytterligare kallfil behovs.
2. Gor det korta HMA-datorpasset enligt korordern. Vid originalets eventuella typfel: rapportera exakt fel, inga improviserade andringar.
3. Work laser fulla exporter, gor trade-jamforelse, intradags-/same-bar-QA och funded-replay. Storlek valjs forst efter faktisk evidens, inte utifran syntetiska exempel.

Alla nya filer ligger under EAA-specifika mappar pa en separat utvecklingsbranch. ZAC, R1, befintliga README/statusfiler och frysta strategier ar ororda. Inget har mergats till main.

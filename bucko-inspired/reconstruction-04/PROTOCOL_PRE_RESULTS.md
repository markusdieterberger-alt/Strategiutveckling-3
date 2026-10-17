# BUCKO RECON 04 - protokoll låst före ekonomiska resultat

Datum 2026-10-17. Ekonomiska resultat har inte granskats när denna version fryses. Tidigare 10000-bars diagnostik med 95 godkända barer är exponerad och är inte en oberoende valideringsperiod. Alla nya ekonomiska regler nedan är EXECUTION ASSUMPTION, inte Buckos originalregler. Ingen parameteroptimering eller funded-PASS.

## Källor och signalidentitet

Fryst RECON03 ZIP SHA256 a2912d3b2bdbf074ab8e4fb216b57def837b2c360fe3057634942c1bab00ce6e. Samtliga 108 manifestposter verifieras. Originalreference_replay.py SHA256 bcd939b16deef1ae7652d55d6d8b7c0e9c7ab9f908925b58401de2e278360ec0. Originalets Pine/core och footprintpilot lämnas byteidentiska. F1-F10, threshold6, strict2/2, BOS, sweeps, FVG/SD-livscykel, CHOP-gate och avstängda sessions-/trendgates bevaras. F11 är NA. Alla råsignaler och godkända signaler räknas oavsett exekveringsfönster.

PRIMARY_ORIGINAL använder den oförändrade Pythonreferensen, anropad direkt. En subclass får registrera redan beräknade swings efter step utan att ändra dess tillstånd eller returnerade event. Denna telemetri används för SL. Därutöver görs en uttrycklig PINE_SEMANTICS_04_1-känslighetskörning: samma eventmotor och trösklar, men RSI Wilder med SMA-seed och HTF som accepterar befintliga partiella 15m-staplar, till skillnad från originalets EWM-seed och krav på 15 enminutsbarer. Detta är en specificerad approximation av Pine-semantik, inte native-paritet. Alla tre RR testas med grundkostnad. Original och korrigerad modell får aldrig blandas.

## Perioder och kontrakt

Primär: hela tillhandahållna mastern, 2025-10-01 00:00 till 2026-10-01 19:21 UTC, 355342 barer enligt RECON03. Faktisk slutbar inkluderas. Tid antas vara baröppning och konverteras från ISO-offset till UTC. Data har ingen kontraktskolumn eller verifierad roll/backadjustment-proveniens. Ingen fill-forward eller syntetisk volym. Mastersegmentet startar i första raden utan otillgänglig historik.

Äldre robusthet: original GLBX, endast outright-symboler MNQ[HMUZ][0-9], inga kalender­spreadar. Fasta kvartalskontrakt väljs med kalenderroll åtta kalenderdagar före tredje fredagen i förfallomånaden, från den nya handelsdagens föregående kväll 18:00 America/New_York. Ingen framtida volym används. Trade-date = lokalt datum, plus en dag från 18:00. H9 avser 2019, 0-6 avser 2020-2026. Inga prisjusteringar. Varje valt kontraktssegment kör referensmodellen från tomt tillstånd med dess ordinarie warmup; ingen indikator beräknas över ett syntetiskt prissteg vid roll. Saknade minuter förblir saknade och originalets gapreset gäller. Ingen återfyllnad från annat kontrakt. Urval slutar före 2025-10-01 00:00 UTC så att primär och äldre studie inte överlappar. Start bestäms av första tillgängliga giltiga valda kontraktsbar. Oanvändbara/dubblerade data får inte tyst korrigeras; blockerare redovisas.

## Entry och fryst stop

En signal är känd vid 1m-barens close. Om flat då skapas högst en väntande order. Inga reverseringar eller pyramider. Signaler under öppen position loggas som upptagna och ignoreras, även motsatta; SL/TP ändras inte. Om en position avslutas under signalbaren kan en ny signal vid dess close skapa nästa entry.

Entry sker på nästa tillgängliga bar-open, plus en tick adverse slippage i basfallet. En signal måste ligga inom dokumenterat exekveringsfönster och nästa öppning i samma tillåtna handelsdag. Pending över dagens entrygräns, helgdag eller ny handelsdag avvisas. Nästa tillgängliga öppning över ett datagap märks uttryckligen och hanteras utan fill på tidigare close.

LONG SL = senaste strikt bekräftade 2/2-swinglow vid signalclose minus 0.25. SHORT SL = senaste bekräftade swinghigh plus 0.25. Även en pivot som just har bekräftats är känd vid denna close. Saknat eller felvänt stop relativt signalclose avvisar entrykandidaten. Vid nästa open avvisas även signalen om det oslipade open redan är på/förbi stop. SL flyttas aldrig. Ingen ATR-fallback, riskkapning, min-/max-ATR eller exitoptimering läggs till om strukturellt stop är definierbart.

R-risk = positivt avstånd från faktisk adverse entryfill till fryst SL, gånger 2 USD. TP ligger 1.5, 2 eller 3 gånger detta avstånd från entryfill, avrundat utåt till 0.25-grid. Det kan ge marginellt högre nominellt RR än målet. Ingen flytt av target, BE, trailing eller del-exit. En MNQ, 2 USD/punkt, kommission 1 USD round-turn.

## Intrabar, kostnader och gaps

Bracket antas aktiv direkt från entryfill; faktisk broker-/Pine-aktivering är ej verifierad. Vid bar-open kontrolleras först stopgap, därefter mål och övrig OHLC. Om både SL och kvalificerat TP finns i samma återstående bar, vinner SL. Aldrig framtida bars information om vilken nivå som kom först. Stop touch räcker. TP kräver att priset handlas minst en tick genom target, även vid open. Positivt targetgap ger ingen prisförbättring: target är bokföringspris.

Entry-slippage är ett sämre marketfill. Alla exits belastas också med en tick (0.50 USD) adverse exekveringskostnad. På market/stop motsvarar detta ett sämre exitfill. På limit-TP bokas fyllnadspriset på target och ett separat konservativt kostnadsavdrag, inte ett påstått limitfill sämre än limit. Ledger skiljer referenspris, modellens effektiva pris och avdrag. Netto = prisrörelse från oslipat entry-open till exitreferenspris, minus entry- och exitfriktion och kommission. Brutto före alla kostnader redovisas på samma affärsbok, inte som en separat gratis-exekveringsoptimering.

En befintlig position vid ett oplanerat avstånd >60 sekunder stängs till första efterföljande observerade open med adverse exitkostnad. Ingen retroaktiv stängning på sista close före luckan. Ett stopgap fylls till sämre open, inte till önskat stop. Exitorsak GAP markeras och effekten särredovisas; okända intragappriser kan inte rekonstrueras. Testperiodens sista öppna position stängs på sista bar-close med kostnad, märkt END_SAMPLE. Detta är slutlikvidation, inte en löpande entryregel.

## Exekveringsfönster och kalender

America/New_York med DST, inte fast UTC-offset. Tillåtna handelsdagar mån-fre. Globexdelen öppnar föregående dag 18:00. Nya entries endast före 16:00 och alla normala positioner stängs vid 16:30-open, 15 minuter före Lucids angivna 16:45. Inga nya entries 16:00-18:00. Signalkärnans egna sessionpoäng ändras inte. Om cutoffquote saknas används första efterföljande observerade open, flaggat; ingen påhittad fill vid en saknad minut.

Konservativ helgdagspolicy: inga entries under hela handelsdagen för amerikanska federala observerade helgdagar enligt den sparade pandas-kalendern, Good Friday, fredagen efter Thanksgiving, 3 juli, 24 december och den särskilda 9 januari 2025. Policyn exkluderar även vissa öppna dagar och är inte en exakt CME-helgkalender. Den fryses före resultat och redovisas separat i signalfunneln. Helgdagarna sparas som explicit CSV. På så sätt undviks avsiktlig handel över kända förkortade sessioner; oförutsedda stängningar/gaps flaggas. Ingen nyhetsoptimering, riskprofil, daily-loss-spärr eller challenge-simulering ingår.

Primärkällor granskade 2026-10-17: https://support.lucidtrading.com/en/articles/11404729-allowed-trading-times (16:45 EST, återöppning18:00, helgdag tidigare stängning); https://support.lucidtrading.com/en/articles/11508978-approved-products-and-commissions (MNQ0.50 USD per sida); https://www.cmegroup.com/trading-hours.html ; https://www.cmegroup.com/content/dam/cmegroup/notices/ser/2025/01/ser-9499r.pdf . Lucid skriver EST; IANA New York används som dokumenterad operationshypotes, och faktisk brokerklocka/DST måste verifieras före funded. Ingen sådan promotion beslutas här.

## Förutbestämd begränsad matris

RR alltid 1.5, 2, 3. PRIMARY_ORIGINAL: (a) BASE1:1tick/sida, TPgenom1tick, stop-first; (b) SLIP2:2ticks/sida, övrigt lika; (c) TP_THROUGH2:1tick/sida, TPgenom2ticks; (d) NO_ENTRY_BAR_TP:1tick/sida, stop aktiv på entrybar men target tidigast följande bar. Totalt12 körningar. PINE_SEMANTICS_04_1: endast BASE1 för alla tre RR, totalt3. Äldre korrekt rekonstruerade serie: ORIGINAL BASE1 och SLIP2 för alla tre RR, totalt6. Totalt högst21 förutbestämda ekonomiska körningar. Ingen ytterligare RR-, entry-, stop-, score- eller session-sökning. Inga körningar summeras till en portfölj.

## Rapportering, osäkerhet och beslut

Alla affärer och alla kandidatavslag sparas per variant. Månader och veckor följer NY-handelsdatum; kalenderperiod och datum med faktiskt prisunderlag anges separat. Halvor delas vid 2026-04-01 00:00 UTC för mastern och kalender­mittpunkten för äldre historik. Netto, PF och winrate baseras på stängda affärer efter kostnader. Win = netto>0, breakeven räknas separat. R = trade-netto/fryst initial riskUSD. USD- och R-DD i realiserad stängd-affärskurva redovisas tillsammans med bar-close mark-to-market USD-DD. Det senare är inte worst-tick/funded-DD. Toppvinnare tas bort för top1,5,10 samt översta5% av vinnande affärer, som koncentrationsdiagnostik.

Bootstrap: 5000 resamplingar med seed20261017, cirkulära sammanhängande block om5 handelsdagar inklusive noll-affärsdagar i observationsperioden. Daggrupper bevarar affärers inbördes beroende samma dag. Rapportera 95% intervall för netto/expectancy och PF samt 98.333% tvåsidigt expectancyintervall (Bonferroni för tre primära RR). Samma indexdragningar används för de tre RR. Detta hanterar inte all tidigare projektforskning eller alla utforskade marknader. Legacy och PINE_SEMANTICS är robusthetskontroller, inte oexponerade bevis för originalets edge.

Signalfrekvens: råeventbarer/riktningar, godkända barer, SL-/tidsmässigt möjliga kandidater, upptagna signaler och faktiska entries. Deskriptiv episode = samma riktning och handelsdag, högst15 minuter mellan godkända signaler; motsatt signal bryter. Detta är inte en entryfilterregel eller bevis på en verklig unik marknadsrörelse. RECON03:s 10000-barsfönster återkörs separat med dess gamla state-start för frekvensavstämning; ekonomiska utfall från detta redan exponerade fönster blir inte validering.

GO kräver ekonomiskt stöd efter bas- och stresskostnader, rimlig halvårs-/månadsstabilitet, ingen materialitetsdrivande fill/datafråga, och ingen avgörande motsägelse från legacy/Pine-semantik. Ett osäkert positivt punktestimat, vinster som bärs av ett fåtal affärer eller stor paritetskänslighet ger HOLD. Om samtliga tre original-RR saknar positiv expectancy och kontrollerna inte visar en felaktig implementering eller avgörande alternativ förklaring ger studien NO-GO för nuvarande modell. Ingen vinnare utses som oberoende verifierad efter denna matris. Varje kandidat för fortsättning måste frysas på nytt och prövas oexponerat. GO avser endast en begränsad TradingView-kontroll, aldrig challenge/funded/live.

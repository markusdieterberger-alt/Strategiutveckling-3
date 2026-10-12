# AMT Node Proxy V2 DEV — regelprotokoll före resultat

Marknadsregler fastställda 2026-10-12 före första resultatkörningen. Forskningsidentitet, inte tilldelad strategikod. D02001–D02019 har reserverats i A003 som nya arbetsidentiteter efter kontroll av senaste A003 och Drive; slutlig klassning tillhör projektledaren. V1-protokollet och äldre resultat ändras inte.

## Population och status

Canonical MNQ 1m V1.0 från A002; 2019–2026 är exponerad DEV. Separata EU- och NY-kohorter, riktningar och år. Inget reserverat SIM-FWD finns i denna leverans. Ingen true VAP, aggressor, delta eller footprint används. Profilen är uttryckligen en OHLCV-approximation.

## Profil och kausal tid

Kör på standard 1m-candles. En 5m-close är känd efter UTC-minut 04,09,…59. Kräv 150 på varandra följande minuter, samma kontrakt, utan saknad minut. Vid lucka/roll: nollställ profil och pågående signalepisod; framtida utfallsfönster censureras vid luckan. Inga syntetiska staplar.

På en komplett 5m-close byggs profil av de senaste 150 minuterna INKLUSIVE den avslutade minuten. Signalsekvensen börjar först på en SENARE 5m-close. Binbredd i ticks = max(4, floor(rangeTicks/64 + 0.5)). Binankare = floor(minLowTicks/binWidthTicks)*binWidthTicks. Varje pris hör till ett halvöppet bin; high exakt på en bingräns tillhör det övre binet. Lika volym till samtliga bin mellan low/high; alternativa konstruktioner: all volym vid close respektive en TPO-enhet per berört bin och minut. Ingen parametergrid.

Smoothing [1,2,1]/4 med noll utanför profilen. Median av smoothede bin där värdet > 0. HVN: strikt större än båda grannar, minst 1.25 gånger medianen; ändbin kan inte vara HVN. POC: första/lägsta maximala bin. Endast intilliggande HVN-toppar granskas; avstånd minst fem bin. LVN: första/lägsta minimibin strikt mellan dem, högst 0.60 gånger lägre toppens volym.

Numerisk QA-precisering efter första diagnostiska körningen: råvolym under totalmassan × 1e-12 behandlas som flyttalsdamm; smooth-volym avrundas half-up till 0.000001 volymenheter i både Python och Pine före nodjämförelser. Syftet är att en matematisk platå inte blir en falsk strikt topp på grund av summeringsordning. Ingen pris-/signaltröskel optimeras. De publicerade resultaten är omkörda efter preciseringen. Detta är utvecklings-QA, inte oberoende validering.

Nodnivå = binmitt, kan ligga på halvt tick. Ordernivåer avrundas till tick enligt nedan. En korridor kan frysas endast när close ligger inom ursprungs-HVN:s bin (inklusive mitt ± halv binbredd). Båda sidor granskas, välj minsta avstånd close→LVN; lika avstånd väljer lägre HVN-par, sedan long. Ingen sortering efter framtida resultat.

Frys HVN1, LVN, HVN2, POC, binbredd, riktning och 150m-källfönster. Nya profiler tidigast 150 minuter efter föregående frysning; källfönster för frysta episoder överlappar därmed inte. En episod varar högst 150 minuter. Högst en signal per episod; efter signal väntar modellen till frysning+150m. Profiler kan använda redan observerad prisutveckling från föregående episod. Utfallen kan överlappa och är INTE oberoende observationer; osäkerhet blockas per handelsdag.

## Signaler

LVN-zon = mitt ± halv binbredd. För riktning d=+1/-1 är destinationssidan strikt bortom zonens bortre kant. Första 5m-close där är probe (räknare=1). Två YTTERLIGARE konsekutiva destinations-closes ger A. En close inne i LVN-zonen nollställer acceptansräknaren. En close på ursprungssidan inom tre följande 5m-bars och före A ger B i motsatt riktning. Annars avbryt efter den tredje följande baren. Probe-extrem inkluderar samtliga 1m-high/low från första probens femminutersbar till signalbarens slut.

A: riktning d, fenomenmål HVN2-mitt, order-TP HVN2:s proximala kant; SL en tick bortom LVN:s ursprungskant. B: riktning -d, fenomenmål/TP gammal global lokalprofil-POC om den ligger framåt; SL en tick bortom probe-extremen. Det globala POC-valet är explicit — inte ett i efterhand valt HVN-mål. Signaler utan framåtriktat mål loggas som blockerade, inte bortglömda.

EU: signalbarens close-klockslag 07:00–11:59 Europe/Stockholm. NY: 09:30–11:59 America/New_York. Övriga signaler konsumerar också episoden men tas inte in i kohorterna. Därmed kan inte sessionsurval påverka profilsekvensen. IANA-tidszoner hanterar DST. Inga samtidiga EU/NY-tider förekommer i denna historik.

## Lokal balans och kontroller

Separat kontrollmodell fryser senaste 30m high/low var 150:e minut efter första kompletta profilfönstret. Ingen efterhandsvald konsolideringströskel. Första 5m-close utanför intervallet är probe; samma tre-close-acceptans/återgång inom tre bars gäller. A-mål = en balansbredd utanför utbrottsgränsen; B-mål = balansens mitt. Balansmått redovisas deskriptivt. Episoder vars 150m-profil saknar kvalificerat HVN/LVN-par utgör vanlig break/reclaim-pool för matchning.

Mirror: samma avstånd på motsatt sida om nästa open. First-touch 30/60/120m; om båda nivåer träffas samma minut utan entydig open-ordning räknas adverse/mirror först. Redovisa även tie och censur. Pseudo-kontroll: flytta den FRYSTA korridoren en binbredd i proberiktningen och skapa en separat kausal signalsekvens. Utfallet jämförs på matchat eventavstånd; att bara flytta target och hävda oförändrat avstånd från samma entry vore algebraiskt fel.

Matcha nod-event mot vanliga balanshändelser (med återläggning): samma familj, år, sida, session och 30m klockblock, ATR inom faktor 2, profilålder ±30m. Välj minsta absoluta log-ATR-differens, därefter tidsstämpel. Utvärdera kontroll från dess egen entry med nod-eventets mål/mirror-avstånd; ingen matchning på framtida utfall. Saknad match redovisas. Kontroller med återläggning är inte nya oberoende bevis.

IB är enbart conditioner: senast fullständigt känd 18:00–18:59 NY respektive 00:00–00:59 Stockholm (60 verkliga minuter krävs). Rapportera position/alignment och ATR-normaliserade avstånd. IB-width jämförs med föregående fullständigt observerade handelsdygns range. Ingen IB-gate läggs på baseline. Inkrementell promotion kräver först överlevande baseffekt; marginala IB-undergrupper är inte bevis för lift.

## Exekveringsdiagnostik, inte godkänd handelsstrategi

Baseline körs som DEV-diagnostik även om fenomengaten underkänns, eftersom den nya arbetsordern efterfrågar ett första backtest. Detta är en uttrycklig avvikelse från V1:s sekventiella stopp före execution. Ingen strategi promoveras av detta.

En MNQ, ingen hävstångs-/storleksoptimering, pyramiding=0, max en position per familj+kohort+konstruktion. Signaler under innehav ignoreras. Signal-close måste ligga strikt mellan tickavrundad SL och TP. Marketentry skickas vid signal-close och fylls nästa verkliga 1m-open, med en tick adverse slippage. En oväntad lucka efter signal kan inte användas för att retroaktivt välja bort ordern: sådana trades loggas separat och exit sker konservativt på första tillgängliga open. De ingår i P&L men inte i kontinuerliga fenomenutfall.

Fast SL/TP, inga trails eller break-even. SL avrundas bort från positionen; TP mot entry. Stop-gap på sämre open, därefter slippage; gynnsamt target-gap krediteras högst limitpriset. Stop före TP om båda nås i samma 1m och open inte redan entydigt passerat någon nivå. Vid gap över TP före intrabarstopp är TP först. Ingen stop/target före entry. Tidsexit efter 120 faktiskt observerade sammanhängande minuter, beslut vid minutens close, marketfill nästa open. Oväntad datalucka i position: befintliga stop/target prövas vid återkomstens open innan konservativ gap-exit på samma open. Detta är osäker execution, flaggas och känslighetsrapporteras.

Inga nya signaler efter sessionsslut. Stäng återstående position senast 12:00 i respektive kohorts tidszon genom order på 11:59-minutens close, fill 12:00-open. Detta tidiga forskningscutoff undviker normal eftermiddags-/overnight-exponering och är INTE ett bevis om helgdagar eller någon firms regler. Om data saknas vid cutoff används nästa tillgängliga open och överträdelsen flaggas.

Planerad risk i R = avstånd signal-close + en tick adverse till SL, före entry. Actual entry-risk och gapgeometri rapporteras separat; ingen framtida open används för att välja signal. Bas: $1 kommission RT (=0.5p) plus 0.25p adverse entry och 0.25p adverse ALLA exits, även limit, sammanlagt nominellt 1p RT. Stress 2p/3p ökar roundtripkostnaden med 1p/2p på samma frysta trades. Detta är kostnadskänslighet, inte omsimulering av likviditet. 1p= $2/MNQ. DD från stängda trades OCH open-equity rapporteras separat; ingen funded-sannolikhet beräknas före gates.

## Pine-grind och avvikelser

Minimal Pine v6 strategy byggs FÖRE resultat. Native bracketorders kan inte tvinga TradingViews historiska emulator att alltid välja stop först vid dubbelträff. Native limitfills saknar också vår extra konservativa exitslippage. Därför exporteras nivåer, signaler och closedtrades-diagnostik; Python konservativa fillmotor är QA-referens, INTE påstådd exakt native P&L-paritet. Dessa avvikelser måste lösas/avgränsas med verkliga TV-data innan promotion.

Ingen omfattande strategioptimering före faktisk kompilering och resurstest. Konstruktionskontrollerna HL/CLOSE/TPO, pseudo-korridor och 1/2/3p-kostnader är förhandsbestämd mätkänslighet, inte vinnarurval. Alla utfall redovisas. Frysta V1, R1, ZAC och CT ändras inte.

## Beslutsgates

Behåll V1:s screeningkrav för denna studies bedömning: minst 300 events per sida/familj och 100 per delperiod, konsekvent asymmetritecken 2019–22/2023–24/2025–26, dagbootstrap-CI exkluderar noll, överensstämmelse mellan konstruktioner; baseline PF>1 och avgR>0 per period samt positiv 2p-stress. Dessa är protokollspecifika, inte nya projektövergripande A001-regler. Därefter krävs Pine/parity och genuin framåtevidens. Ingen numerisk paritytolerans uppfinns.

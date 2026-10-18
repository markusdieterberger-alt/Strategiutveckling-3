# BUCKO REVERSE 01 - protokoll före spegelvända resultat

Datum: 2026-10-18. Detta experiment beställs efter granskning av RECON04-originalets ekonomiska utfall. Hela historiken är därför exponerad DEV-forskning. Ett positivt utfall är explorativt, inte oberoende OOS, SIM-FWD eller verifierad edge. Inga resultat för spegelmodellen har granskats när detta protokoll låses.

## Frysta källor

Utgångspunkt är det levererade RECON04-paketet, SHA256 `6f70a71381c4d562e324e8ba9bf001f41bcf2e139fae0031c2cc19356a0e4d9e`. Alla156 manifestposter ska verifieras. Käll-Python, Pine, footprintpilot och CT Scalper ändras inte. RECON04:s source-of-truth-execution är `execution.py`, SHA256 `802b406a465fabd64d9f4101dad03286f12dc6a647bdd19f3a0ac2ef2fe89d34`. Den importeras byteoförändrad även för spegelkörningen. Signalmodellens RSI-seed, HTF-fullständighetskrav, pivot/zonregler, score6 och gates är originalets, inte PINE_SEMANTICS-approximationen.

## Enda modellförändringen

1. Kör den frysta signalreferensen på oförändrad OHLCV, bekräftade barer, originalets warmup/gapreset och kalender.
2. Behåll alla råevent, originalets faktorvärden, poäng, blockeringar och godkända tidsstämplar. Inga signalfilter tillämpas på nytt efter inversionen.
3. För varje godkänd original-LONG blir avsedd handel SHORT; godkänd original-SHORT blir LONG. Även ursprungligen ej exekverade godkända signaler inverteras. Det är inte en negation av tidigare affärsnetton.
4. Beräkna SL från den NYA handelssidans senaste vid signalclose bekräftade pivot: ny LONG använder swinglow minus0,25; ny SHORT använder swinghigh plus0,25. Pivoterna själva byts inte plats. SL fryses vid signalclose. Om den senaste pivoten saknas eller ger ett stop på fel sida av signalclose avvisas kandidaten, som i RECON04. Ingen sökning efter en äldre gynnsammare pivot, ATR-fallback eller ny riskgräns införs.
5. Vid nästa tillgängliga open gäller samma kontroll: open på/förbi stop avvisas. Entryfill inkluderar adverse slippage i NY riktning. TP räknas om från denna fill, nya SL och valt RR och avrundas utåt till tick. Gamla original-SL/TP får aldrig återanvändas.
6. Original och spegelmodell har var sin oberoende positionshistorik med högst en position åt gången. Annan hålltid eller SL-giltighet kan ändra vilka efterföljande kandidater som kan exekveras. Detta redovisas som mekanisk effekt, inte som optimerat signalurval.

Teknisk transport till den oförändrade executionfunktionen får byta godkännandemask och sidkolumner för source-score, source-factor-mask och source-trigger, så att den nya handelssidans etiketter fortfarande redovisar den godkända ORIGINAL-signalens poäng/typ. Swingnivåer, priser och regimkolumner ändras aldrig. Originalriktning och faktisk handelsriktning sparas separat i ledger/kandidatlogg. Kanoniska signalfiler är orörda.

## Exekvering, data och kostnader

Exakt samma RECON04-regler: nästa tillgängliga1m-open efter bekräftad signal; en position; motsatt signal under position ignoreras; samma OHLC stop-first, stopgap till sämre open, TP-penetration, targetgap utan förbättring, kostnad på limit-TP som separat haircut, gapexit på nästa observerade open, slutlikvidation, sessions- och helgdagsregler. 1 MNQ, tick0,25, USD2/punkt, USD1 round-turn-kommission, BASE1 minst1 tick adverse per sida. Ingen nyhets-/DLL-/riskkapningsregel läggs till.

Master: 2025-10-01T00:00Z till2026-10-01T19:21Z,355342 barer. Äldre:2019-05-05T22:03Z till2025-09-30T23:59Z,2252694 barer,27 outright-kontrakt med26 förutbestämda kalenderroller, inga prisjusteringar/fill-forward, separat indikatorwarmup per kontrakt. Alla tidigare gap-, kontraktsproveniens- och degraded-begränsningar följer med. Återanvänd redan rekonstruerad serie; rullningen optimeras inte.

## Låst matris

TP =1,5R/2R/3R i varje fall.

- Master original + spegel: BASE1, SLIP2, TP_THROUGH2, NO_ENTRY_BAR_TP. 24 körningar.
- Äldre original + spegel: BASE1, SLIP2. 12 körningar.
- Totalt36 körningar, varav18 spegelhypoteser och18 reproduktionskontroller av originalet.
- RECON04:s tre PINE_SEMANTICS-körningar är historisk dokumentation och ingår inte i inversionen; att byta signaldefinition skulle bryta detta uppdrag.

Alla originalresultat ska återges i både affärsidentitet och ekonomiska mått; annars utred blockerare före tolkning av spegelmodellen. Ingen ytterligare signal-, SL-, RR-, riktnings-, sessions- eller periodoptimering tillåts i detta uppdrag.

## QA innan utfallsgranskning

Verifiera originalets13 riktade tester. Lägg riktade tester för signalinversion efter godkännande, bevarad source-score/trigger, separata source/trade-directions, ny korrekt SL och ny TP, invalidation av omvänd SL, frame/source-immutabilitet och prefixkausalitet. Fullkörningen ska kontrollera identiska godkända tidsstämplar, exakt omvänd avsedd riktning och oförändrad originalscore. Ledger ska verifiera SL/TP på rätt sida, PnL-identitet, nästa-open-timing och ingen positionsöverlappning. Varje eventuellt kodfel dokumenteras; pre-result-hash bevaras.

## Jämförelse och robusthet

Antal affärer, wins/losses/breakeven, winrate, PF, brutto före kostnader på samma bok, netto, expectancy USD/R, max stängd-affärs-DD USD/R, bar-close MTM-DD, medelvinst/förlust, förlustsvit, frekvens och risk redovisas för alla36 körningar. Alla månads-, vecko- och long/short-resultat sparas; huvudrapporten visar basfallen. Gruppering efter originalscore, source-trigger och regim är beskrivande, aldrig nya valda filter. Source-riktning och faktiskt handlad riktning ska kunna skiljas åt.

Samma robusthetsplan som RECON04: masterhalvor vid2026-04-01T00:00Z, äldre vid kalenderhalvan2022-07-18T23:01Z; topp1/5/10 och högsta5% av vinnarna borttagna enbart som koncentrationsdiagnostik;5000 cirkulära femhandelsdags block-bootstrapdragningar, seed20261017, inkluderar observerade noll-affärsdagar;95% intervall och98,333% intervall för de tre primära RR. Samma dagvikter för original och spegel ger även en parad DIFFERENS i dagsnetto mellan modellerna. Detta jämför mekanismer, inte parvis identiska affärer. Perioder/kontrakt/dagar med dåliga utfall får inte filtreras bort.

Multipel testning och efterhandsinitierad inversion ska framgå på rapportens första sida. Bootstrap/Bonferroni för tre RR kan inte neutralisera att riktningen valdes efter originalutfallet eller all tidigare projektforskning.

## Beslutsram

Bedömningen gäller denna implementation och om begränsad fortsatt validering är motiverad, inte funded/live. GO kräver trovärdigt ekonomiskt stöd efter kostnad/stress, rimlig tidsstabilitet och inga avgörande QA-fel; ett sådant GO är fortfarande explorativt och kräver ny oexponerad validering. HOLD vid svaga/motsägelsefulla positiva punktestimat, materialitetsdrivande data-/fillfrågor eller otillräcklig robusthet. NO-GO om den testade inversionen saknar rimligt stöd för positiv expectancy och QA inte visar en ogiltig testimplementation. Ingen numerisk universell projektgate uppfinns, ingen snygg subgrupp väljs som ny strategi.

Ingen marknadsdata eller privat affärslogg publiceras i GitHub. Kod/protokoll på separat branch; rapporter, loggar och reproduktionspaket till projektledarens Drive-inkorg. A003 får en spårbar leveransanteckning. Ingen extern feed, Pine/livekörning eller CT Scalper-ändring inom detta experiment.

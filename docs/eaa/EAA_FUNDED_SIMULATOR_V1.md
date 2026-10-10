# EAA - funded-simulator v1

Python 3.10+; standardbibliotek for CSV och simulering. Valfri `openpyxl` behovs for XLSX-lasning. Inga marknadsdata eller brokernycklar skickas av programmet. Ingen orderlaggning finns.

## Regler, inte sammanblandade profiler

Kontroll mot officiella Lucid-sidor 2026-10-09:

| Regel | Kontrollerad information | Modell v1 |
|---|---|---|
| LucidFlex 25K evaluation | +$1 250 mal, $1 000 MLL, 20 micros | Samma belopp |
| Drawdown | EOD-trailing, lasning av MLL vid startkapital +$100 | Golv start -$1 000; max tidigare EOD; tak +$100 |
| DLL | ON/OFF valjs vid kop; ON ar soft breach/dagslas | Projektprofil ON=$600, inte verifierat Flex-belopp; separat OFF-profil |
| Consistency | 50% med beskriven cushion | Strikt 50%; cushion anvands inte eftersom exakt allman formel inte ar entydigt specificerad |
| Dagsvinst | $550 ar projektets arbetsantagande, inte pavisat Lucid-tak | Trigger for likvidering; overskjutande vinst klipps aldrig bort |
| Tillatna tider | Stangt senast 16:45 EST; ater 18:00; helgdagar kan avvika | Konfigurerbar zon; NY ar explicit modellantagande, inte bevis pa EST/DST eller helgdagar |
| 10/15 dagar, FAIL cirka <=30% | Projektmal | Urvalskriterium, ingen officiell diskvalifikation vid dag 15 |

`project_550_v1.json` foljer EAA-arbetsorderns $550 och intradagsrisk. `a003_500_v1.json` behaller aldre A003:s $500 realiserade profit-stop som separat jamforelse, inte tyst overskrivning av styrning. `lucidflex_dll_off_v1.json` ar en separat offentlig regelbaserad modell utan projektets vinsttak. Ingen profil ar marknadsford som kontocertifierad. $600 for Flex maste matchas mot det kopta kontots faktiska villkor; belopp fran LucidDaily/Pro far inte automatiskt arvas.

## Korning

Fran repots rot, utan installation for CSV:

```bash
python3 -m unittest discover -s tests/eaa -v
python3 -m eaa.synthetic
python3 -m eaa eaa/fixtures/synthetic_trades.csv --calendar eaa/fixtures/synthetic_calendar.csv --paths eaa/fixtures/synthetic_paths.csv --rules eaa/config/project_550_v1.json --contracts 1,2,3,4,6,10,20 --extra-slippage 0,1,2 --commissions 1,2,3 --bootstrap 1000 --output eaa-result.json
```

Detta exempel ar ENDAST SYNTETISKT. For faktisk export, ersatt input och kalender; anvand explicit `--export-timezone America/New_York` om exporten saknar UTC-offset. Kallans verkliga exportzon maste anvandas, inte anvandarens svenska lokaltid per automatik.

Programmet laser TradingViews engelska `Trade #`, `Type`, `Date and time`/`Date/Time`, `Price USD`/`Price`, `Position size (qty)`/`Contracts`/`Quantity`. En entry- och en exitrad paras per trade-ID. Nya XLSX-exporter med `Trades` eller `List of trades` valjs automatiskt; annars `--sheet` med exakt fliknamn. Andra sprak/rubriker kraver `--column-map map.json` fran exportens namn till accepterade namn. Fel, oppna trades, del-exits, overlagrade positioner, saknade par och oklar decimalformatering stoppas, inte gissas.

Alternativ normaliserad CSV, en rad per avslutad position:

```csv
trade_id,entry_time,exit_time,side,entry_price,exit_price,contracts,stop_points,mae_points
EXAMPLE,2026-01-05T10:00:00-05:00,2026-01-05T10:05:00-05:00,long,20000,20010,1,25,5
```

`stop_points` ar kausalt kant vid entry och kravs endast for `--risk-budget`. MAE ar frivillig och anges som positiv adverse-rorelse i punkter per kontrakt, inte dollar eller stopavstand. Riktning `long`/`short`, MNQ $2/punkt, tick 0.25. Ingen NQ-till-MNQ-identitet antas tyst.

## Kalender och intradagsunderlag

`--calendar` kravs: CSV med `session_date` i stigande ISO-datum, en rad for VARJE oppen marknadssession i testintervallet, aven dagar utan trades. Ingen artificiell kalender skapas fran endast handelsdagar med signal. Ange fullstandiga, avslutade sessioner. Session start 18:00 foregaende kvall raknas till foljande session. Helgdagar/early-close granskas separat fore beslutskritisk korning.

Tre datanivaer:

1. Endast trade-lista: `CLOSED_TRADES_ONLY`, approximativ. Kontot kan ha brutit MLL/DLL trots positiv avslutning. Varken PASS eller ingen FAIL bevisar intradagsregler.
2. `--paths`: CSV `trade_id,time,unrealized_points`, ett ordnat spar per position, samtliga IDs kravs. Punkter avser signerad mark-to-entry-P&L per MNQ FORE avgifter, inte total konto-equity. Samplad risk observeras, men mellanliggande extrema kan saknas.
3. `--bars`: 1m CSV `time,open,high,low,close,volume`, timezone-aware minutoppningar. OHLC-envelope testar open/adverse/favorable/close. Hela entry-/exitminuten inkluderas som konservativt extremspann och kan innehalla priser fore fill/efter exit. Resultatet ar inte en rekonstruerad tickvag eller exakt stop-first Pine-fill. Saknade minuter stoppas.

Saknad ticksekvens och orderko kan inte aterskapas fran OHLC. Stangda affarers total-MAE kan anvandas som adverse-first-proxy, men dess exakta tid ar okand. Inga resultat blir automatiskt officiella genom att mer data bifogas.

## Modellens bokforing

- `cash`: realiserat saldo; entry tar halva RT-kostnaden. Intradagsequity inkluderar oppen positions markering. Likvidering tar andra halvan. Priserna i TV-exporten innehaller redan eventuellt modellerad slippage.
- `--extra-slippage` ar ytterligare ticks per sida ovanpa exporterade priser. Provision raknas om fran pris-P&L; exporterad net P&L subtraheras inte igen. A001-bas $1 RT + totalt 2 ticks ger $2 RT per MNQ nar priset annars ar friktionsfritt.
- MLL-golvet anvander enbart hogsta EOD-resultat och sjunker aldrig. Oppen intradagsvinst hojer inte golvet. Vid golvkontakt blir det FAIL; samtliga kostnader och gapforluster behalls.
- DLL mot dagens startsaldo ger likvidering vid observerat markpris och block av resterande nya trades den dagen. MLL kontrolleras forst; gap genom bada ar MLL-failure. Hard DLL-failure finns enbart som explicit projektvariant.
- Profit-stop likviderar vid observerad trigger, inte exakt garanterat $550. Gap och sampling kan ge overshoot. `block_new`-profilen stoppar bara efter realiserad vinst; inga latenta toppvinster kapas.
- PASS provas vid EOD efter mal och consistency. Detta ar en konservativ pass-timing, inte Lucids exakta realtidsdashboard.
- Riskstorlek ar golv(riskbudget/(tickavrundad stoprisk+kostnader)), max valt heltal och max20. Om 1 kontrakt overskrider budget hoppas affaren over; ingen avrundning uppat. Riskbudget skyddar inte mot gap.
- Endast en position, intraday-flat. Pyramiding, partials och overnight input avvisas. Inga frysta portfoljer porteras till denna enklare replay.

## Rapport och statistik

JSON ger PASS/FAIL/ALIVE, median dagar bland PASS, PASS inom 5/10/15 fran samtliga startfonster, MLL/hard-DLL-orsaker, antal mjuka DLL-las, kontrakts-/kostnadsscenarier och varje fonsters handelser. Bara kompletta rullande fonster inkluderas; inga avkortade slutfonster.

Seedad moving-block-bootstrap drar sammanhangande block om normalt 5 hela sessioner, bevarar respektive dags handelsordning och tar med nolldagar. Minimum 30 sessioner och 10 sessionsdagar med trades. Bootstrap antar viss representativitet/stationaritet och ar inte nytt OOS. Overlappande fonster ar inte oberoende binomialobservationer.

`best_examined_contracts` valjs enbart vid deklarerad baskostnad, bland undersokta storlekar med FAIL<=30%, hogst PASS inom10 och darefter total PASS. Det ar ett explorativt in-sample-urval, INTE verkligt optimum eller godkand storlek. Inga strategifilter optimeras.

En viktig begransning: nar en exporterad affar stoppas i fortid eller hoppas over saknas eventuella nya signaler som da skulle ha kunnat uppsta. Simulatorn ar villkorad trade-replay, inte omkorning av Pine. Detta och saknad exakt intradagsequity hindrar strategipromotion fran simulatorn ensam.

## Officiella kallor

- [LucidFlex evaluation](https://support.lucidtrading.com/en/articles/12945790-lucidflex-evaluation-account)
- [LucidFlex drawdown](https://support.lucidtrading.com/en/articles/12945815-lucidflex-drawdown)
- [LucidFlex DLL ON/OFF och soft breach](https://support.lucidtrading.com/en/articles/16226050-lucidflex-customization)
- [Consistency och cushion](https://support.lucidtrading.com/en/articles/12945805-lucidflex-consistency-percentage)
- [Tillatna handelstider](https://support.lucidtrading.com/en/articles/11404729-allowed-trading-times)

Kallornas ordval om EST och de individuella kontovillkoren ar en oavgjord avtals-/tidszonsfraga, inte tyst ersatt med en gissning.

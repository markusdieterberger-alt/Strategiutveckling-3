# AMT Node Proxy V2 DEV — separat valideringsrapport

2026-10-12. **VALIDATION FAILURE / NOT EXECUTED. Ingen oberoende lönsamhetsvalidering.**

| Grind | Faktisk status | Bevis/återstående arbete |
|---|---|---|
| Canonical identitet | Verifierad | Gzip- och CSV-SHA256 enligt A002, 2 614 900 minuter |
| Python execution | Utförd | Generator, fullständiga event-/trade-loggar, tester och run-manifest |
| Pine source | Skriven | Riktig v6 `strategy()`, OHLCV-profil, A/B, bracketorders, closedtrades-diagnostik |
| Pine kompilering | **INTE UTFÖRD** | Två navigeringsförsök till TradingView timeout; ingen kompilatorrespons erhållen |
| Pine resursgränser | **INTE TESTADE** | Begränsade arrays och O(150+bin) per profil; faktisk fullhistorikkörning återstår |
| Signaler Python–Pine | **INTE VERIFIERADE** | Kräver chart-export med exakt data, session, symbol, roll och startuppvärmning |
| Native orderfills | **KÄND SKILLNAD** | TV:s OHLC-väg kan ge TP före SL; Python stop-first. Python extra konservativ limit-slippage och capped favorable gap skiljer också |
| Gap-exit | **KÄND SKILLNAD** | Python antar konservativ återkomst-open; Pine kan upptäcka datalucka först vid återkomstbarens close. Sådana trades flaggas, inte paritetsgodkända |
| SIM-FWD | **SAKNAS** | Hela 2019–2026 är redan exponerad i projektet. Årsdelar är DEV-diagnostik |
| TRUE FWD | **INTE STARTAD** | Ingen kandidat har passerat gates och frysts för framtida validering |
| Funded/challenge/payout | **INTE UTFÖRT** | Förutsätter robusthet, Pine/parity och verifierade aktuella firmregler |

En lyckad kompilering kommer enbart att stänga kompileringsgrinden. Native Strategy Tester-resultat måste därefter jämföras mot konservativa fills och datakällornas skillnader. En numerisk tolerans för avvikelser har inte fastställts av projektet; denna leverans uppfinner ingen.

Datum efter canonical-slutet 2026-10-02 är inte automatiskt oexponerade. En framtida valideringsperiod måste vara orörd vid exakt kandidatfrysning. Tidigare inkörd eller använd data får inte ometiketteras. Börja därför TRUE FWD först efter ny versionsfrysning och dokumenterad exponeringskontroll.

Pine-prototypen använder ingen IB-gate. De IB-mått som finns i Python är fenomenklassificering, inte regler som i hemlighet saknas i Pine. Inte heller lokal balans eller pseudo-korridorer är aktiverade ordermodeller i Pine; de är separata forskningskontroller.

Körorder: D02013. Metod/resultat och beslut: D02001. Alla negativa eller positiva historiska siffror i denna leverans har status DEV.

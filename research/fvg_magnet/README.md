# FVG Magnet Study v1

## Forskningsfråga
Finns en exploaterbar sannolikhetsedge i att ett närliggande, orört 30m/1h/4h FVG fungerar som magnet när priset redan har riktning mot gapet?

## Medvetet enkel hypotes
- Instrument: MNQ.
- Magnet: närmaste orörda 30m, 1h eller 4h FVG.
- Riktning: completed 30m EMA20 lutar åt gapet och priset ligger på rätt sida om EMA20.
- Maxavstånd: 2.0 x 1m ATR14 i första kartläggningen.
- Ingen CRT, POC, oscillator, trendkanal eller extra konfluens i basmodellen.
- FVG definieras som standard 3-candle imbalance.
- FVG aktiveras först när HTF-candlen är avslutad.
- Ett research-event per FVG för att undvika minutvis dubblering.

## Primära mått
För varje kvalificerat FVG-event mäts:
1. Touch inom 240 minuter.
2. Touch innan priset först går 0.25 ATR åt fel håll.
3. Touch innan 0.50 ATR adverse.
4. Touch innan 0.75 ATR adverse.
5. Touch innan 1.00 ATR adverse.
6. Tid till touch.
7. Distance-to-FVG i ATR.

## Segmentering
Rapportera minst:
- 30m / 1h / 4h separat.
- Avstånd: <=0.5, 0.5-1.0, 1.0-1.5, 1.5-2.0 ATR.
- Long / short.
- År/regim för stabilitet.
- HTF-konfluens som separat sekundär analys, inte som krav i basmodellen.

## Beslutsregel för nästa steg
Vi går vidare till en trade-entry-modell bara om magnetstudien visar:
- tydlig monotonic distance decay,
- stabil edge över flera år/regimer,
- tillräcklig sample size,
- och en praktiskt användbar kombination av touch-rate och låg adverse excursion.

## Kandidatstrategi först efter magnet-PASS
Om magneten håller:
- Entry: första enkla 5m continuation efter pullback.
- SL: bakom pullbackens extrem.
- TP: strax före närmaste FVG-edge.
- Minimera antal filter.

## Data
Använd projektets canonical MNQ 1m-serie som förstahandskälla. Rå Databento-data är verifierad som GLBX.MDP3 / ohlcv-1m / MNQ.FUT, med historik från 2019-04-14 i batchunderlaget. Canonical stitched dataset ska användas för faktisk studie för att undvika kontrakts-/rollartefakter.

## Status
Research harness implementerad i:
`research/fvg_magnet/fvg_magnet_study_v1.py`

Branch:
`research/fvg-magnet-v1`

Empirisk fullkörning återstår mot canonical CSV.

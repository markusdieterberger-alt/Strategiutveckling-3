# Kort körorder — AMT Pine-grind

**Forskningsprototyp. Ingen live/funded-handel.** Kompilering och parity är fortfarande oprövade.

1. Öppna ett separat standard-candlestick-diagram för **MNQ, 1 minut**, Extended session. Dokumentera ticker, datakälla, kontrakt/continuous-roll och om backadjust är avstängt. Använd inte Heikin Ashi/Renko.
2. Pine Editor → ny strategi. Klistra in hela **D02003_AMT_NODE_PROXY_V2_DEV.pine**. Spara och välj Add to chart. Vid fel: exportera exakt feltext och radnummer; ändra inte signalregler eller parametrar för att få bättre resultat.
3. Börja med standard **HL / A / NY**. Properties: 1 kontrakt, pyramiding 0, $0.50 kommission per sida, 1 tick slippage, inga beräkningar varje tick/efter fills, inga fills på signal-close. Testa först kort historik, därefter största tillgängliga period. Spara eventuell runtime-timeout.
4. Exportera Strategy Testers **List of trades** och **Performance summary** samt diagramdata med samtliga `QA ...` plots. Spara exakta start/slutdatum och alla Properties/Inputs. Notera om Deep Backtesting-data skiljer sig från diagrammets exportbara historik.
5. Om första körningen fungerar: upprepa **HL / B / NY**, **HL / A / EU**, **HL / B / EU**. CLOSE/TPO följer först när grundporten fungerar. Ingen optimeringsgrid ännu.

Projektledaren lämnar exporterna till Work för automatisk jämförelse mot D02005/D02006 och datakällan. Samma tider/prisnivåer ska jämföras först; därefter fills. Varning: Python tar SL först vid okänd dubbelträff, har capped target-gap och en extra konservativ exitslippage även för limits. Native P&L kan därför bli högre utan att strategin blivit bättre. `QA ambiguous SL TP minute` och `strategy.closedtrades` används för att hitta dessa avvikelser; position_size ensam missar same-bar roundtrips.

**Godkänn inte parity enbart för att antal affärer eller totalnetto liknar Python.** Kontrollera varje avvikande signal, stop, target, tid och fill. Välj ingen vinnande ny parameter här. Framåttest/funded är separata senare steg.

Underlagen finns i samma Drive-inkorg som denna körorder och på den nya AMT-research-branchen. Starta med D02001 för resultat och filkarta.

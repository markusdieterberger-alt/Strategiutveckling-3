# AMT Node Proxy V2 DEV — optimeringsrapport

2026-10-12. **Omfattande strategioptimering: INTE KÖRD.** Arbetsorderns hårda Pine-feasibility-grind är öppen efter faktiska webbläsartimeouter. Denna rapport redovisar vad som faktiskt prövats; en planerad parametergrid är inte ett utfört test.

Före resultat specificerades tre profilkonstruktioner (HL, CLOSE, TPO), två modeller (A/B), två separata kohorter (EU/NY), två riktningar och tre kostnadsnivåer (1/2/3 punkter). Samtliga tolv handelsvarianter och kostnadsstresser redovisas, även negativa. Pseudo-korridor och vanlig balans är fenomenkontroller, inte handplockade ersättningsstrategier. Se D02007–D02009 och D02016.

Detta är baseline och konstruktions-/kostnadskänslighet. Ingen bästa binbredd, topptröskel, daltröskel, stop, RR, tidsstopp, IB-gate eller riskstorlek har valts efter resultat. En prototyputförandebugg som spärrade ny signal på redan avslutad trades exitbar rättades till samma kausala close-beteende som Pine; inga marknadsregler ändrades. Alla publicerade resultat kommer från omkörningen efter rättningen.

Numerisk QA standardiserade dessutom smooth-volym till sex decimaler i båda språken så att flyttalsrester inte skapar toppar på platåer. Denna kodrättning och bytet från preliminära lokala filnamn till lediga D02001–D02018 dokumenteras i git/QA. Ingen tröskel valdes för att höja PF.

Fortsatt utveckling får göras enligt A001 §§5.16–5.17 när faktisk Pine-körbarhet är bevisad. Ny version ska skilja mellan:

- Att acceptans först blir synlig när det gamla HVN-målet redan passerats: ett implementerings-/entryproblem, som ska mätas före ny regel.
- Avsaknad av riktningsasymmetri efter kostnadsfri signal: ett problem för själva operationaliserade fenomenhypotesen.
- Konstruktionsberoende nodnivåer: en datamätningsbegränsning. Byt inte till den mest lönsamma profilen och kalla det robusthet.

Nästa rimliga DEV-fråga efter Pine-grinden är om en i förväg känd target-distance kan hållas tillräckligt stor för att bekräftelsen inte ska förbruka hela rörelsen. Det är ett förslag, **inte en testad räddning**, och kräver ny versionsidentitet innan körning. Nya filter ska motiveras, hela söklandskapet redovisas och den framtida valideringsperioden reserveras först efter kandidatval.

Ingen fryst V1-, CT-, R1- eller ZAC-version har ändrats.

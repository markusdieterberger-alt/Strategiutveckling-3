# EAA CT – här hittar projektledaren allt underlag

Uppdaterad 2026-10-10. **Källportning och lokal QA klara. TradingView-kompilering, fills och prestanda återstår.**

Samlad leverans: [Google Drive → Strategiutveckling → 00 – Inkorg till Projektledare](https://drive.google.com/drive/folders/1W6dB7lc6t6st2oKr4zSEj9wfwdUVaaIG).

Börja med den korta CT-körordern. Den färdiga strategifilen innehåller all kod som ska klistras in i TradingView.

- [EAA_CT_SCALPER_STRATEGY_V1.pine](https://drive.google.com/file/d/1GMQBmBLVmFoBtQS8i7mp0ls7W71MiAt1/view?usp=drivesdk)
- [EAA_CT_SCALPER_QA_V1.md](https://drive.google.com/file/d/11aV1lbWfDBQo-OvRQ7EXtnVwIz09FiRM/view?usp=drivesdk)
- [EAA_CT_DATORPASS_KORORDER_V1.md](https://drive.google.com/file/d/1b_v6sOZ1Cblr-VhwRXDyCEvZrJhyKtDK/view?usp=drivesdk)
- [EAA_DATORPASS_KORORDER_V1.md](https://drive.google.com/file/d/1_7HOiUp3O6VKayMKltYorpbTXOTSaCQn/view?usp=drivesdk)
- [CT_VERIFICATION_V1.json](https://drive.google.com/file/d/1yuXXCCuwL_2qufXx1EZcDZk8ly9HCIpQ/view?usp=drivesdk)
- [CT_ORIGINAL_TO_STRATEGY_V1.diff](https://drive.google.com/file/d/1FlBKzXqPlK_pJKtTz3Rh5DV4l03NG6bc/view?usp=drivesdk)
- [SOURCE_MANIFEST.json](https://drive.google.com/file/d/1240RRgrupoh7w77ZvQRls_Jo54a98kFT/view?usp=drivesdk)

Original som faktiskt användes: [uppladdad CT-indikator](https://drive.google.com/file/d/1zsoCvNPmFF6KMVaC5ETRwWF0DnYT2oFO/view). Den publika BACKTEST-versionen är inte signalkällan.

GitHub: [EAA-branchen](https://github.com/markusdieterberger-alt/Strategiutveckling-3/tree/eaa/validation-factory-v1-2026-10-09).

| Underlag | Sökväg på EAA-branchen |
|---|---|
| Klistra-in-fil | `pine/eaa/EAA_CT_SCALPER_STRATEGY_V1.pine` |
| Bytebevarat original | `pine/eaa/reference/EAA_CT_SCALPER_INDICATOR_ORIGINAL_FROM_CHAT_2026-10-10.pine` |
| QA, körorder och manifest | `docs/eaa/` |
| Full ändringsdiff och faktisk testlogg | `docs/eaa/evidence/CT_ORIGINAL_TO_STRATEGY_V1.diff`, `CT_VERIFICATION_V1.json` |
| Reproducerbar konvertering | `eaa/build_ct.py`, `eaa/ct_templates/` |
| Statiska kontroller och syntetiska kontrakt | `eaa/ct_audit.py`, `eaa/ct_contract.py`, `tests/eaa/test_ct.py` |
| Körning av QA | `python -m eaa.verify_ct` från reporoten |
| Tidigare HMA- och fundedunderlag | `pine/eaa/`, `eaa/`, `docs/eaa/` |

Aktuell status och överlämning förs i [A003](https://docs.google.com/document/d/1CfUzcWIWUkP1hKEqb39pYQy5dWnRz4pBmTDKqcL-ZrA/edit). Den äldre EAA-zippen från före denna leverans innehåller inte den nya CT-porten; använd länkarna ovan. Den länkade allmänna körordern är uppdaterad och ersätter äldre exemplar som säger att CT ska hoppas över.

Verifierat: originalets hash/storlek, bevarade sex modeller och signaluttryck, 87 godkända automatiserade tester (37 nya CT-tester) och 25 CT-textkontrakt. Strategins Drive-kopia har lästs tillbaka och jämförts byte-för-byte med den lokalt testade filen.

Ej verifierat: Pine-kompilering/runtime, signalparitet på marknadsdata, native intrabarordning, footprinttäckning och historisk prestanda. Pythonkontrakten kör inte Pine. Originalets HTF/reload-risk kvarstår. Separat stop-first-stress ersätter inte TradingViews affärslista. Inga ändringar i R1, ZAC eller frysta strategier.


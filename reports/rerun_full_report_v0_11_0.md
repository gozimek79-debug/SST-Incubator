# Raport re-runu konfirmacyjnego v0.11.0 — dane do analizy

> Wygenerowany 2026-07-26 20:01 UTC przez `scripts/report_composer.py` z `reports/population/population_validation_v0_11_0.json` + `publications/competency_profile.json`. **ZERO oceny/interpretacji dodanej przez generator** — każda liczba i status to echo pola już obliczonego w źródłach. Liczby identyczne z panelem (sekcje „Lekcje i wyniki” oraz „Porównanie genomów”) — ten sam plik źródłowy, brak osobnego liczenia.

## 1. Metadane re-runu

| Pole | Wartość | Źródło |
|---|---|---|
| study_id | `v0.11.0_confirmatory_rerun` | population_validation_v0_11_0.json |
| git_commit | `cfc15e2fa3f9be7853057140b91abc8ab41191b7` | jw. |
| hard_halt_baseline (AUD-001) | `cca6f8f933a73c1ff9ca9a3e482b966fef4c430ee50f3ed6c35137d3ab8ec935` | jw. |
| manifest | `execution_package_v0_11/experiment_manifest.json` | jw. |
| n_raw_records | 12765 | jw. |
| fdr_correction.n_real_testable_cells | 9 | jw. |
| fdr_correction.alpha | 0.005556 | jw. |
| profil.generated_at | 2026-07-22T22:35:03.877637 | competency_profile.json |

**dataset_status (population):** CONFIRMATORY (NIE Exploratory) - re-run autoryzowany przez Final Audit Gate (audytor, klon 5098e1f, 2026-07-19). N=185/93/92 wg experiment_manifest.json. ZERO interpretacji Power/Confirmatory w tym pliku - to zadanie audytora, potem red team wobec wnioskow. Ten plik NIE zastepuje ani nie nadpisuje Exploratory Dataset v0.10 (reports/population/population_validation_v0_10_1.json).

**dataset_status (profil):** CONFIRMATORY (NIE Exploratory) - re-run konfirmacyjny 12765 przebiegow (23 genomy x n=185/93/92 wg experiment_manifest.json), Hard-Halt PASS caly bieg, zakonczony 2026-07-20. Zrodlo: reports\population\population_validation_v0_11_0.json. Statusy per pojecie (VALIDATED/EXPERIMENTAL) z docs/METRIC_STATUS_TABLE.md po korekcie Red Teamu (2026-07-20). Ten profil ZASTEPUJE Exploratory Dataset v0.10 (n=10, 2 genomy) jako zywy artefakt - archiwum zachowane, nietkniete, w competency_profile_v0_10_1_exploratory.json.

## 2. Wyniki per (lekcja × środowisko × metryka)

Liczby wprost z `population_validation_v0_11_0.json` — identyczne z sekcją „Lekcje i wyniki” panelu. `FDR pary` = pary genomów istotne po korekcie Benjamini-Hochberg (q=0.05) na teście Welcha; `raw p<0.05` = przed korektą; `ANOVA f` = surowy effect size (wejście do oceny mocy, NIE werdykt).

Środowiska kontrolne oznaczone `[kontrola-zdegenerowane]` — deterministyczne (n_effective=1, CI95 nie dotyczy z definicji, nie porażka pomiaru).

### L1.1 / noise_world

| Metryka | classification | valid_rate | n_valid/n_total | n (seedy) | FDR pary | raw p<0.05 | ANOVA f |
|---|---|---|---|---|---|---|---|
| Adaptation | GENOME-FRAGILE | 0.5652 | 13/23 | n=185 | 75/78 | 75 | f=4.4268 |
| Final Energy Level | GENOME-ROBUST | 1.0000 | 23/23 | n=185 | 243/253 | 244 | f=3.5717 |
| Pattern Recognition | GENOME-ROBUST | 1.0000 | 23/23 | n=185 | 77/253 | 99 | f=0.1638 |
| Pattern Retention | GENOME-ROBUST | 1.0000 | 23/23 | n=185 | 0/253 | 17 | f=0.0792 |
| Stability | GENOME-ROBUST | 1.0000 | 23/23 | n=185 | 244/253 | 244 | f=2.0615 |
| Working Memory (MAE@50) | GENOME-ROBUST | 1.0000 | 23/23 | n=185 | 69/253 | 95 | f=0.1537 |

### L1.1 / stable_world [kontrola-zdegenerowane]

| Metryka | classification | valid_rate | n_valid/n_total | n (seedy) | FDR pary | raw p<0.05 | ANOVA f |
|---|---|---|---|---|---|---|---|
| Adaptation | GENOME-FRAGILE | 0.0000 | 0/23 | n=93 | 0/0 | 0 | nieobliczalne |
| Final Energy Level | GENOME-FRAGILE | 0.0000 | 0/23 | n=93 | 0/0 | 0 | nieobliczalne |
| Pattern Recognition | GENOME-FRAGILE | 0.0000 | 0/23 | n=93 | 0/0 | 0 | nieobliczalne |
| Pattern Retention | GENOME-FRAGILE | 0.0000 | 0/23 | n=93 | 0/0 | 0 | nieobliczalne |
| Stability | GENOME-FRAGILE | 0.0000 | 0/23 | n=93 | 0/0 | 0 | nieobliczalne |
| Working Memory (MAE@50) | GENOME-FRAGILE | 0.0000 | 0/23 | n=93 | 0/0 | 0 | nieobliczalne |

### L1.2 / shock_world

| Metryka | classification | valid_rate | n_valid/n_total | n (seedy) | FDR pary | raw p<0.05 | ANOVA f |
|---|---|---|---|---|---|---|---|
| Adaptation | GENOME-FRAGILE | 0.0000 | 0/23 | n=185 | 0/0 | 0 | nieobliczalne |
| Final Energy Level | GENOME-ROBUST | 1.0000 | 23/23 | n=185 | 204/253 | 205 | f=2.2227 |
| Homeostatic Resilience (recovery_time) | GENOME-FRAGILE | 0.7857 | 11/14 | n=2–185 | 48/55 | 48 | f=5.6987 |
| Stability | GENOME-ROBUST | 1.0000 | 23/23 | n=185 | 87/253 | 102 | f=1.6493 |

### L1.2 / stable_world [kontrola-zdegenerowane]

| Metryka | classification | valid_rate | n_valid/n_total | n (seedy) | FDR pary | raw p<0.05 | ANOVA f |
|---|---|---|---|---|---|---|---|
| Adaptation | GENOME-FRAGILE | 0.0000 | 0/23 | n=92 | 0/0 | 0 | nieobliczalne |
| Final Energy Level | GENOME-FRAGILE | 0.0000 | 0/23 | n=92 | 0/0 | 0 | nieobliczalne |
| Homeostatic Resilience (recovery_time) | — | — | —/— | — | — | — | nieobliczalne |
| Stability | GENOME-FRAGILE | 0.0000 | 0/23 | n=92 | 0/0 | 0 | nieobliczalne |

## 3. Profil kompetencji (z competency_profile.json)

Zmierzone: 7/14 · VALIDATED: 3 · ci95_valid (ROBUST): 5

**Profil minimalny (VALIDATED)** — osie, dla których status konfirmacyjny to VALIDATED (źródło statusu: `docs/METRIC_STATUS_TABLE.md`, generator przepisuje pole `confirmatory_status`, nie wylicza go sam):

- Osie poznawcze: Pattern Recognition, Working Memory, Stability
- Zmienne stanu fizjologicznego: (brak)

**Profil pełny** (wszystkie 14 pojęć ontologii; `confirmatory_status` echo z METRIC_STATUS_TABLE.md):

| Pojęcie | Rodzaj | Status pomiaru | confirmatory_status | classification | valid_rate | Źródło (lekcja/środ.) |
|---|---|---|---|---|---|---|
| Pattern Recognition | cognitive | measured | VALIDATED | GENOME-ROBUST | 1.0000 | L1.1/noise_world |
| Pattern Retention | cognitive | measured | EXPERIMENTAL | GENOME-ROBUST | 1.0000 | L1.1/noise_world |
| Working Memory | cognitive | measured | VALIDATED | GENOME-ROBUST | 1.0000 | L1.1/noise_world |
| Stability | cognitive | measured | VALIDATED | GENOME-ROBUST | 1.0000 | L1.1/noise_world |
| Final Energy Level | physiological_state | measured | EXPERIMENTAL | GENOME-ROBUST | 1.0000 | L1.2/shock_world |
| Adaptation | cognitive | measured | EXPERIMENTAL | GENOME-FRAGILE | 0.5652 | L1.1/noise_world |
| Homeostatic Resilience | cognitive | measured | EXPERIMENTAL | GENOME-FRAGILE | 0.7857 | L1.2/shock_world |
| Perception | cognitive | insufficient_data | — | — | — | — |
| Attention | cognitive | insufficient_data | — | — | — | — |
| Long-term Memory | cognitive | insufficient_data | — | — | — | — |
| Prediction | cognitive | insufficient_data | — | — | — | — |
| Exploration | cognitive | insufficient_data | — | — | — | — |
| Generalization | cognitive | insufficient_data | — | — | — | — |
| Planning | cognitive | insufficient_data | — | — | — | — |

## 4. Dane per-genom (surowe, załącznik)

Średnia ± CI95 per genom, wprost z `per_genome` w `population_validation_v0_11_0.json`. Środowiska kontrolne pominięte (deterministyczne, patrz §2).

### L1.1 / noise_world / Adaptation

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | 43.081081 | 42.411070 | 43.751092 | 185 | 23 | True |
| highly_plastic | 10.454054 | 10.340698 | 10.567410 | 185 | 5 | True |
| minimal | 41.502703 | 40.899483 | 42.105922 | 185 | 20 | True |
| pop_000 | 10.010811 | 9.989622 | 10.032000 | 185 | 2 | True |
| pop_001 | 10.010811 | 9.989622 | 10.032000 | 185 | 2 | True |
| pop_002 | 17.275676 | 16.942953 | 17.608399 | 185 | 12 | True |
| pop_003 | 10.032432 | 10.002753 | 10.062112 | 185 | 3 | True |
| pop_004 | 10.140541 | 10.076495 | 10.204586 | 185 | 4 | True |
| pop_005 | 10.005405 | 9.994811 | 10.016000 | 185 | 2 | True |
| pop_006 | 10.470270 | 10.350040 | 10.590500 | 185 | 5 | True |
| pop_007 | 11.097297 | 10.918191 | 11.276403 | 185 | 7 | True |
| pop_008 | 10.010811 | 9.989622 | 10.032000 | 185 | 2 | True |
| pop_009 | 10.264865 | 10.174709 | 10.355020 | 185 | 4 | True |
| pop_010 | 19.848649 | 19.465654 | 20.231644 | 185 | 14 | True |
| pop_011 | 10.005405 | 9.994811 | 10.016000 | 185 | 2 | True |
| pop_012 | 16.145946 | 15.146275 | 17.145617 | 185 | 23 | True |
| pop_013 | 41.659459 | 41.054624 | 42.264295 | 185 | 22 | True |
| pop_014 | 10.091892 | 10.040461 | 10.143322 | 185 | 4 | True |
| pop_015 | 12.210811 | 11.979822 | 12.441799 | 185 | 8 | True |
| pop_016 | 10.016216 | 9.992578 | 10.039855 | 185 | 3 | True |
| pop_017 | 11.270270 | 11.073097 | 11.467443 | 185 | 8 | True |
| pop_018 | 14.567568 | 14.257227 | 14.877908 | 185 | 13 | True |
| pop_019 | 33.713514 | 33.159690 | 34.267337 | 185 | 19 | True |

### L1.1 / noise_world / Final Energy Level

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | 0.461892 | 0.460592 | 0.463192 | 185 | 21 | True |
| highly_plastic | 0.414249 | 0.413859 | 0.414638 | 185 | 8 | True |
| minimal | 0.459492 | 0.458580 | 0.460404 | 185 | 17 | True |
| pop_000 | 0.411070 | 0.410785 | 0.411355 | 185 | 7 | True |
| pop_001 | 0.410076 | 0.409730 | 0.410421 | 185 | 8 | True |
| pop_002 | 0.426562 | 0.425975 | 0.427149 | 185 | 11 | True |
| pop_003 | 0.411968 | 0.411674 | 0.412261 | 185 | 7 | True |
| pop_004 | 0.412995 | 0.412685 | 0.413304 | 185 | 7 | True |
| pop_005 | 0.409741 | 0.409381 | 0.410100 | 185 | 7 | True |
| pop_006 | 0.415200 | 0.414243 | 0.416157 | 185 | 12 | True |
| pop_007 | 0.416962 | 0.416461 | 0.417463 | 185 | 8 | True |
| pop_008 | 0.410497 | 0.410179 | 0.410816 | 185 | 7 | True |
| pop_009 | 0.413957 | 0.413174 | 0.414740 | 185 | 10 | True |
| pop_010 | 0.430573 | 0.429816 | 0.431330 | 185 | 12 | True |
| pop_011 | 0.409319 | 0.408959 | 0.409679 | 185 | 7 | True |
| pop_012 | 0.656281 | 0.646983 | 0.665579 | 185 | 58 | True |
| pop_013 | 0.461665 | 0.460655 | 0.462675 | 185 | 17 | True |
| pop_014 | 0.412584 | 0.412268 | 0.412899 | 185 | 8 | True |
| pop_015 | 0.419059 | 0.418360 | 0.419759 | 185 | 10 | True |
| pop_016 | 0.411395 | 0.411109 | 0.411680 | 185 | 7 | True |
| pop_017 | 0.417405 | 0.416884 | 0.417927 | 185 | 9 | True |
| pop_018 | 0.422141 | 0.421650 | 0.422631 | 185 | 11 | True |
| pop_019 | 0.449632 | 0.448733 | 0.450532 | 185 | 17 | True |

### L1.1 / noise_world / Pattern Recognition

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | 0.152065 | 0.148467 | 0.155664 | 185 | 185 | True |
| highly_plastic | 0.156635 | 0.153052 | 0.160218 | 185 | 185 | True |
| minimal | 0.152104 | 0.148533 | 0.155675 | 185 | 185 | True |
| pop_000 | 0.155087 | 0.151353 | 0.158821 | 185 | 185 | True |
| pop_001 | 0.158802 | 0.155152 | 0.162453 | 185 | 185 | True |
| pop_002 | 0.161058 | 0.157208 | 0.164909 | 185 | 185 | True |
| pop_003 | 0.160624 | 0.156856 | 0.164392 | 185 | 185 | True |
| pop_004 | 0.155018 | 0.151283 | 0.158752 | 185 | 185 | True |
| pop_005 | 0.165758 | 0.161915 | 0.169602 | 185 | 185 | True |
| pop_006 | 0.160270 | 0.156526 | 0.164013 | 185 | 185 | True |
| pop_007 | 0.159957 | 0.156350 | 0.163564 | 185 | 185 | True |
| pop_008 | 0.165581 | 0.161870 | 0.169291 | 185 | 184 | True |
| pop_009 | 0.157739 | 0.154237 | 0.161241 | 185 | 185 | True |
| pop_010 | 0.156814 | 0.153370 | 0.160258 | 185 | 185 | True |
| pop_011 | 0.165063 | 0.161309 | 0.168816 | 185 | 184 | True |
| pop_012 | 0.160546 | 0.156663 | 0.164429 | 185 | 185 | True |
| pop_013 | 0.160703 | 0.156897 | 0.164508 | 185 | 185 | True |
| pop_014 | 0.157166 | 0.153763 | 0.160569 | 185 | 185 | True |
| pop_015 | 0.156610 | 0.153176 | 0.160044 | 185 | 185 | True |
| pop_016 | 0.164271 | 0.160553 | 0.167989 | 185 | 185 | True |
| pop_017 | 0.155396 | 0.151685 | 0.159108 | 185 | 182 | True |
| pop_018 | 0.153391 | 0.149864 | 0.156918 | 185 | 184 | True |
| pop_019 | 0.152185 | 0.148627 | 0.155744 | 185 | 185 | True |

### L1.1 / noise_world / Pattern Retention

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | -0.000147 | -0.000233 | -0.000061 | 185 | 174 | True |
| highly_plastic | -0.000074 | -0.000167 | 0.000019 | 185 | 176 | True |
| minimal | -0.000126 | -0.000215 | -0.000036 | 185 | 180 | True |
| pop_000 | 0.000026 | -0.000064 | 0.000115 | 185 | 180 | True |
| pop_001 | 0.000033 | -0.000053 | 0.000119 | 185 | 175 | True |
| pop_002 | -0.000048 | -0.000151 | 0.000054 | 185 | 177 | True |
| pop_003 | -0.000045 | -0.000140 | 0.000050 | 185 | 177 | True |
| pop_004 | 0.000003 | -0.000096 | 0.000102 | 185 | 179 | True |
| pop_005 | -0.000023 | -0.000095 | 0.000050 | 185 | 175 | True |
| pop_006 | -0.000030 | -0.000131 | 0.000070 | 185 | 172 | True |
| pop_007 | 0.000010 | -0.000098 | 0.000119 | 185 | 174 | True |
| pop_008 | -0.000091 | -0.000166 | -0.000016 | 185 | 177 | True |
| pop_009 | -0.000010 | -0.000103 | 0.000083 | 185 | 180 | True |
| pop_010 | -0.000092 | -0.000193 | 0.000009 | 185 | 177 | True |
| pop_011 | 0.000020 | -0.000052 | 0.000093 | 185 | 171 | True |
| pop_012 | -0.000055 | -0.000159 | 0.000048 | 185 | 183 | True |
| pop_013 | -0.000027 | -0.000129 | 0.000074 | 185 | 177 | True |
| pop_014 | -0.000003 | -0.000094 | 0.000088 | 185 | 175 | True |
| pop_015 | -0.000095 | -0.000187 | -0.000003 | 185 | 183 | True |
| pop_016 | -0.000093 | -0.000187 | 0.000000 | 185 | 174 | True |
| pop_017 | -0.000079 | -0.000174 | 0.000015 | 185 | 180 | True |
| pop_018 | -0.000087 | -0.000182 | 0.000007 | 185 | 180 | True |
| pop_019 | -0.000122 | -0.000213 | -0.000032 | 185 | 178 | True |

### L1.1 / noise_world / Stability

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | 2.418917 | 2.409477 | 2.428358 | 185 | 181 | True |
| highly_plastic | 3.207701 | 3.186781 | 3.228620 | 185 | 183 | True |
| minimal | 2.417758 | 2.408732 | 2.426784 | 185 | 178 | True |
| pop_000 | 3.416131 | 3.391184 | 3.441078 | 185 | 179 | True |
| pop_001 | 3.491572 | 3.464906 | 3.518238 | 185 | 184 | True |
| pop_002 | 2.845305 | 2.830119 | 2.860491 | 185 | 177 | True |
| pop_003 | 3.342203 | 3.319067 | 3.365338 | 185 | 179 | True |
| pop_004 | 3.284944 | 3.262994 | 3.306894 | 185 | 182 | True |
| pop_005 | 3.510577 | 3.483357 | 3.537797 | 185 | 180 | True |
| pop_006 | 3.193905 | 3.172915 | 3.214895 | 185 | 181 | True |
| pop_007 | 3.108797 | 3.089458 | 3.128136 | 185 | 181 | True |
| pop_008 | 3.460173 | 3.434251 | 3.486095 | 185 | 182 | True |
| pop_009 | 3.245168 | 3.223481 | 3.266855 | 185 | 181 | True |
| pop_010 | 2.768597 | 2.754499 | 2.782695 | 185 | 181 | True |
| pop_011 | 3.539637 | 3.511866 | 3.567409 | 185 | 180 | True |
| pop_012 | 2.692212 | 2.613161 | 2.771264 | 185 | 183 | True |
| pop_013 | 2.388486 | 2.378811 | 2.398162 | 185 | 178 | True |
| pop_014 | 3.306273 | 3.283876 | 3.328670 | 185 | 180 | True |
| pop_015 | 3.041534 | 3.023045 | 3.060023 | 185 | 182 | True |
| pop_016 | 3.393291 | 3.368891 | 3.417691 | 185 | 180 | True |
| pop_017 | 3.089106 | 3.069504 | 3.108709 | 185 | 181 | True |
| pop_018 | 2.941318 | 2.924533 | 2.958104 | 185 | 183 | True |
| pop_019 | 2.497005 | 2.486352 | 2.507659 | 185 | 179 | True |

### L1.1 / noise_world / Working Memory (MAE@50)

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | 0.140634 | 0.132370 | 0.148897 | 185 | 185 | True |
| highly_plastic | 0.155801 | 0.147198 | 0.164404 | 185 | 185 | True |
| minimal | 0.142536 | 0.133525 | 0.151548 | 185 | 185 | True |
| pop_000 | 0.161607 | 0.152656 | 0.170558 | 185 | 185 | True |
| pop_001 | 0.174275 | 0.165035 | 0.183515 | 185 | 185 | True |
| pop_002 | 0.160188 | 0.150274 | 0.170102 | 185 | 185 | True |
| pop_003 | 0.161194 | 0.152139 | 0.170249 | 185 | 185 | True |
| pop_004 | 0.161177 | 0.151765 | 0.170589 | 185 | 184 | True |
| pop_005 | 0.173943 | 0.166273 | 0.181612 | 185 | 185 | True |
| pop_006 | 0.163593 | 0.153969 | 0.173216 | 185 | 185 | True |
| pop_007 | 0.165446 | 0.154841 | 0.176051 | 185 | 185 | True |
| pop_008 | 0.155080 | 0.147275 | 0.162885 | 185 | 185 | True |
| pop_009 | 0.160796 | 0.151978 | 0.169614 | 185 | 185 | True |
| pop_010 | 0.152339 | 0.142378 | 0.162301 | 185 | 185 | True |
| pop_011 | 0.180719 | 0.172738 | 0.188699 | 185 | 185 | True |
| pop_012 | 0.158616 | 0.148790 | 0.168443 | 185 | 185 | True |
| pop_013 | 0.162452 | 0.152320 | 0.172583 | 185 | 183 | True |
| pop_014 | 0.159446 | 0.150772 | 0.168120 | 185 | 185 | True |
| pop_015 | 0.151559 | 0.142454 | 0.160663 | 185 | 185 | True |
| pop_016 | 0.155437 | 0.146670 | 0.164204 | 185 | 185 | True |
| pop_017 | 0.152305 | 0.142970 | 0.161640 | 185 | 185 | True |
| pop_018 | 0.147697 | 0.137924 | 0.157470 | 185 | 185 | True |
| pop_019 | 0.143054 | 0.134095 | 0.152013 | 185 | 185 | True |

### L1.2 / shock_world / Adaptation

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| highly_plastic | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| minimal | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_000 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_001 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_002 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_003 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_004 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_005 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_006 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_007 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_008 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_009 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_010 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_011 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_012 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_013 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_014 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_015 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_016 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_017 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_018 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |
| pop_019 | 10.000000 | 10.000000 | 10.000000 | 185 | 1 | False |

### L1.2 / shock_world / Final Energy Level

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | 0.336054 | 0.330072 | 0.342036 | 185 | 74 | True |
| highly_plastic | 0.218259 | 0.213154 | 0.223365 | 185 | 63 | True |
| minimal | 0.326627 | 0.320834 | 0.332420 | 185 | 72 | True |
| pop_000 | 0.208097 | 0.203005 | 0.213189 | 185 | 63 | True |
| pop_001 | 0.205784 | 0.200691 | 0.210876 | 185 | 62 | True |
| pop_002 | 0.249881 | 0.244661 | 0.255102 | 185 | 67 | True |
| pop_003 | 0.210659 | 0.205564 | 0.215755 | 185 | 60 | True |
| pop_004 | 0.213427 | 0.208339 | 0.218515 | 185 | 66 | True |
| pop_005 | 0.205276 | 0.200187 | 0.210365 | 185 | 64 | True |
| pop_006 | 0.219168 | 0.214057 | 0.224278 | 185 | 65 | True |
| pop_007 | 0.224476 | 0.219383 | 0.229568 | 185 | 61 | True |
| pop_008 | 0.206605 | 0.201495 | 0.211716 | 185 | 59 | True |
| pop_009 | 0.215751 | 0.210662 | 0.220840 | 185 | 63 | True |
| pop_010 | 0.257654 | 0.252410 | 0.262898 | 185 | 68 | True |
| pop_011 | 0.204486 | 0.199398 | 0.209575 | 185 | 63 | True |
| pop_012 | 0.574324 | 0.568876 | 0.579772 | 185 | 71 | True |
| pop_013 | 0.354714 | 0.348367 | 0.361060 | 185 | 73 | True |
| pop_014 | 0.212443 | 0.207352 | 0.217535 | 185 | 64 | True |
| pop_015 | 0.229481 | 0.224369 | 0.234593 | 185 | 67 | True |
| pop_016 | 0.208876 | 0.203776 | 0.213976 | 185 | 66 | True |
| pop_017 | 0.228789 | 0.223528 | 0.234051 | 185 | 65 | True |
| pop_018 | 0.237059 | 0.231915 | 0.242204 | 185 | 63 | True |
| pop_019 | 0.316497 | 0.310614 | 0.322381 | 185 | 79 | True |

### L1.2 / shock_world / Homeostatic Resilience (recovery_time)

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | 16.032432 | 15.346605 | 16.718260 | 185 | 23 | True |
| highly_plastic | 2.333333 | 1.680000 | 2.986667 | 3 | 2 | True |
| minimal | 16.032432 | 15.346605 | 16.718260 | 185 | 23 | True |
| pop_002 | 2.959184 | 2.327994 | 3.590373 | 49 | 10 | True |
| pop_003 | 3.400000 | 2.576178 | 4.223822 | 25 | 8 | True |
| pop_004 | 4.545455 | 3.877775 | 5.213134 | 77 | 12 | True |
| pop_008 | 2.000000 | 0.040000 | 3.960000 | 2 | 2 | True |
| pop_009 | 2.666667 | 1.573431 | 3.759902 | 6 | 3 | True |
| pop_010 | 7.143750 | 6.514550 | 7.772950 | 160 | 19 | True |
| pop_012 | 107.702703 | 106.410813 | 108.994593 | 185 | 42 | True |
| pop_014 | 4.000000 | 3.233188 | 4.766812 | 49 | 10 | True |
| pop_015 | 4.428571 | 3.811718 | 5.045424 | 84 | 11 | True |
| pop_018 | 8.464286 | 7.828537 | 9.100035 | 168 | 18 | True |
| pop_019 | 1.363636 | 0.662673 | 2.064600 | 22 | 5 | True |

### L1.2 / shock_world / Stability

| Genom | mean | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|
| default | 1.717644 | 1.710128 | 1.725160 | 185 | 178 | True |
| highly_plastic | 1.671791 | 1.655910 | 1.687673 | 185 | 183 | True |
| minimal | 1.697822 | 1.691029 | 1.704614 | 185 | 175 | True |
| pop_000 | 1.675829 | 1.658641 | 1.693018 | 185 | 182 | True |
| pop_001 | 1.677068 | 1.659579 | 1.694557 | 185 | 179 | True |
| pop_002 | 1.662491 | 1.650377 | 1.674605 | 185 | 173 | True |
| pop_003 | 1.674634 | 1.657790 | 1.691477 | 185 | 179 | True |
| pop_004 | 1.673219 | 1.656726 | 1.689712 | 185 | 182 | True |
| pop_005 | 1.677151 | 1.659596 | 1.694706 | 185 | 182 | True |
| pop_006 | 1.671145 | 1.655351 | 1.686940 | 185 | 183 | True |
| pop_007 | 1.667857 | 1.652755 | 1.682959 | 185 | 179 | True |
| pop_008 | 1.676563 | 1.659198 | 1.693929 | 185 | 179 | True |
| pop_009 | 1.672857 | 1.656633 | 1.689082 | 185 | 182 | True |
| pop_010 | 1.662444 | 1.651168 | 1.673721 | 185 | 176 | True |
| pop_011 | 1.677654 | 1.659997 | 1.695311 | 185 | 183 | True |
| pop_012 | 2.552739 | 2.522732 | 2.582747 | 185 | 181 | True |
| pop_013 | 1.699780 | 1.692855 | 1.706705 | 185 | 176 | True |
| pop_014 | 1.673677 | 1.657054 | 1.690301 | 185 | 182 | True |
| pop_015 | 1.666989 | 1.652512 | 1.681467 | 185 | 178 | True |
| pop_016 | 1.675364 | 1.658284 | 1.692444 | 185 | 179 | True |
| pop_017 | 1.641322 | 1.625365 | 1.657278 | 185 | 180 | True |
| pop_018 | 1.663009 | 1.649567 | 1.676451 | 185 | 177 | True |
| pop_019 | 1.680305 | 1.673335 | 1.687276 | 185 | 174 | True |


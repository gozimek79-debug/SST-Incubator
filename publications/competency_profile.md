# CLOS Competency Profile

CONFIRMATORY (NIE Exploratory) - re-run konfirmacyjny 12765 przebiegow (23 genomy x n=185/93/92 wg experiment_manifest.json), Hard-Halt PASS caly bieg, zakonczony 2026-07-20. Zrodlo: reports\population\population_validation_v0_11_0.json. Statusy per pojecie (VALIDATED/EXPERIMENTAL) z docs/METRIC_STATUS_TABLE.md po korekcie Red Teamu (2026-07-20). Ten profil ZASTEPUJE Exploratory Dataset v0.10 (n=10, 2 genomy) jako zywy artefakt - archiwum zachowane, nietkniete, w competency_profile_v0_10_1_exploratory.json.

Profil minimalny (VALIDATED): 3 osi / 14 pojec
Measured: 7/14
Insufficient data: 7/14
ci95_valid (ROBUST, wszystkie obecne genomy): 5/14
Generated at: 2026-07-22T22:35:03.877637

Definicje pojec: [cognitive_ontology.md](../clos_academy/cognitive_ontology.md). Statusy konfirmacyjne: [METRIC_STATUS_TABLE.md](../docs/METRIC_STATUS_TABLE.md).

## Profil minimalny (oficjalny, VALIDATED)

Oficjalny profil kompetencji - WYLACZNIE pojecia ze statusem konfirmacyjnym VALIDATED (docs/METRIC_STATUS_TABLE.md: przetrwaly Welch-pary+FDR ORAZ/LUB Kruskal-Wallis, leave-one-out, Red Team). UWAGA: ci95_valid=True ('ROBUST', pomiar wiarygodny) NIE oznacza VALIDATED ('dyskryminuje genomy', potwierdzone konfirmacyjnie) - to dwa rozne pytania, patrz docs/VALIDITY_REPORT.md 'Kluczowe odkrycie'. Przyklad: Pattern Retention jest 100% ci95-valid, ale tylko EXPERIMENTAL - nie wchodzi tutaj.

3 osi poznawczych VALIDATED + 0 zmienna(ych) stanu fizjologicznego VALIDATED. Zmienna stanu fizjologicznego mierzy STAN systemu (np. poziom energii), NIE jego zdolnosc do czegokolwiek - nie sumowac z osiami poznawczymi jako rownowazne wpisy 'kompetencji'.

Osie poznawcze: Pattern Recognition, Working Memory, Stability

Zmienne stanu fizjologicznego: (brak)

| Concept | Status | Confirmatory | Source (lekcja/środowisko) | Classification | valid_rate | n_valid/n_total | FDR pary | ANOVA f (surowe) |
|---|---|---|---|---|---|---|---|---|
| Pattern Recognition | measured | VALIDATED | L1.1/noise_world | GENOME-ROBUST | 1.000000 | 23/23 | 77/253 | 0.163816 |
| Working Memory | measured | VALIDATED | L1.1/noise_world | GENOME-ROBUST | 1.000000 | 23/23 | 69/253 | 0.153698 |
| Stability | measured | VALIDATED | L1.1/noise_world | GENOME-ROBUST | 1.000000 | 23/23 | 244/253 | 2.061514 |

## Profil pelny (wszystkie pojecia, luki jawne)

Wszystkie pojecia z ontologii, w tym zdegenerowane i insufficient_data - jawnie oznaczone, nie ukryte. 'valid'/'degenerate' ponizej to WYLACZNIE ci95_valid (wiarygodnosc pomiaru per genom) - NIEZALEZNE od confirmatory_status (VALIDATED/EXPERIMENTAL), ktory jest polem na kazdym koncepcie.

### ci95_valid = True dla wszystkich obecnych genomow, tzw. ROBUST (5)

| Concept | Status | Confirmatory | Source (lekcja/środowisko) | Classification | valid_rate | n_valid/n_total | FDR pary | ANOVA f (surowe) |
|---|---|---|---|---|---|---|---|---|
| Pattern Recognition | measured | VALIDATED | L1.1/noise_world | GENOME-ROBUST | 1.000000 | 23/23 | 77/253 | 0.163816 |
| Pattern Retention | measured | EXPERIMENTAL | L1.1/noise_world | GENOME-ROBUST | 1.000000 | 23/23 | 0/253 | 0.079230 |
| Working Memory | measured | VALIDATED | L1.1/noise_world | GENOME-ROBUST | 1.000000 | 23/23 | 69/253 | 0.153698 |
| Stability | measured | VALIDATED | L1.1/noise_world | GENOME-ROBUST | 1.000000 | 23/23 | 244/253 | 2.061514 |
| Final Energy Level | measured | EXPERIMENTAL | L1.2/shock_world | GENOME-ROBUST | 1.000000 | 23/23 | 204/253 | 2.222654 |

### Zdegenerowane, tzw. FRAGILE (2) - zmierzone, ale co najmniej jeden genom bez wiarygodnej wariancji

| Concept | Status | Confirmatory | Source (lekcja/środowisko) | Classification | valid_rate | n_valid/n_total | FDR pary | ANOVA f (surowe) |
|---|---|---|---|---|---|---|---|---|
| Adaptation | measured | EXPERIMENTAL | L1.1/noise_world | GENOME-FRAGILE | 0.565200 | 13/23 | 75/78 | 4.426836 |
| Homeostatic Resilience | measured | EXPERIMENTAL | L1.2/shock_world | GENOME-FRAGILE | 0.785700 | 11/14 | 48/55 | 5.698668 |

### Insufficient data (7) - brak lekcji/mechanizmu

| Concept | Status | Confirmatory | Source (lekcja/środowisko) | Classification | valid_rate | n_valid/n_total | FDR pary | ANOVA f (surowe) |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | -/- | - | - |
| Attention | insufficient_data | - | - | - | - | -/- | - | - |
| Long-term Memory | insufficient_data | - | - | - | - | -/- | - | - |
| Prediction | insufficient_data | - | - | - | - | -/- | - | - |
| Exploration | insufficient_data | - | - | - | - | -/- | - | - |
| Generalization | insufficient_data | - | - | - | - | -/- | - | - |
| Planning | insufficient_data | - | - | - | - | -/- | - | - |

## Karty genomow (23 genomy: default/highly_plastic/minimal + pop_000..pop_019)

### default

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.152065 | 0.148467 | 0.155664 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000147 | -0.000233 | -0.000061 | 185 | 174 | True |
| Working Memory | measured | L1.1/noise_world | 0.140634 | 0.132370 | 0.148897 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 43.081081 | 42.411070 | 43.751092 | 185 | 23 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 2.418917 | 2.409477 | 2.428358 | 185 | 181 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.336054 | 0.330072 | 0.342036 | 185 | 74 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 16.032432 | 15.346605 | 16.718260 | 185 | 23 | True |

### highly_plastic

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.156635 | 0.153052 | 0.160218 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000074 | -0.000167 | 0.000019 | 185 | 176 | True |
| Working Memory | measured | L1.1/noise_world | 0.155801 | 0.147198 | 0.164404 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.454054 | 10.340698 | 10.567410 | 185 | 5 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.207701 | 3.186781 | 3.228620 | 185 | 183 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.218259 | 0.213154 | 0.223365 | 185 | 63 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 2.333333 | 1.680000 | 2.986667 | 3 | 2 | True |

### minimal

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.152104 | 0.148533 | 0.155675 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000126 | -0.000215 | -0.000036 | 185 | 180 | True |
| Working Memory | measured | L1.1/noise_world | 0.142536 | 0.133525 | 0.151548 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 41.502703 | 40.899483 | 42.105922 | 185 | 20 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 2.417758 | 2.408732 | 2.426784 | 185 | 178 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.326627 | 0.320834 | 0.332420 | 185 | 72 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 16.032432 | 15.346605 | 16.718260 | 185 | 23 | True |

### pop_000

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.155087 | 0.151353 | 0.158821 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | 0.000026 | -0.000064 | 0.000115 | 185 | 180 | True |
| Working Memory | measured | L1.1/noise_world | 0.161607 | 0.152656 | 0.170558 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.010811 | 9.989622 | 10.032000 | 185 | 2 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.416131 | 3.391184 | 3.441078 | 185 | 179 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.208097 | 0.203005 | 0.213189 | 185 | 63 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | - | - | - | - | - | - |

### pop_001

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.158802 | 0.155152 | 0.162453 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | 0.000033 | -0.000053 | 0.000119 | 185 | 175 | True |
| Working Memory | measured | L1.1/noise_world | 0.174275 | 0.165035 | 0.183515 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.010811 | 9.989622 | 10.032000 | 185 | 2 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.491572 | 3.464906 | 3.518238 | 185 | 184 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.205784 | 0.200691 | 0.210876 | 185 | 62 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | - | - | - | - | - | - |

### pop_002

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.161058 | 0.157208 | 0.164909 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000048 | -0.000151 | 0.000054 | 185 | 177 | True |
| Working Memory | measured | L1.1/noise_world | 0.160188 | 0.150274 | 0.170102 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 17.275676 | 16.942953 | 17.608399 | 185 | 12 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 2.845305 | 2.830119 | 2.860491 | 185 | 177 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.249881 | 0.244661 | 0.255102 | 185 | 67 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 2.959184 | 2.327994 | 3.590373 | 49 | 10 | True |

### pop_003

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.160624 | 0.156856 | 0.164392 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000045 | -0.000140 | 0.000050 | 185 | 177 | True |
| Working Memory | measured | L1.1/noise_world | 0.161194 | 0.152139 | 0.170249 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.032432 | 10.002753 | 10.062112 | 185 | 3 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.342203 | 3.319067 | 3.365338 | 185 | 179 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.210659 | 0.205564 | 0.215755 | 185 | 60 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 3.400000 | 2.576178 | 4.223822 | 25 | 8 | True |

### pop_004

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.155018 | 0.151283 | 0.158752 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | 0.000003 | -0.000096 | 0.000102 | 185 | 179 | True |
| Working Memory | measured | L1.1/noise_world | 0.161177 | 0.151765 | 0.170589 | 185 | 184 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.140541 | 10.076495 | 10.204586 | 185 | 4 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.284944 | 3.262994 | 3.306894 | 185 | 182 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.213427 | 0.208339 | 0.218515 | 185 | 66 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 4.545455 | 3.877775 | 5.213134 | 77 | 12 | True |

### pop_005

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.165758 | 0.161915 | 0.169602 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000023 | -0.000095 | 0.000050 | 185 | 175 | True |
| Working Memory | measured | L1.1/noise_world | 0.173943 | 0.166273 | 0.181612 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.005405 | 9.994811 | 10.016000 | 185 | 2 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.510577 | 3.483357 | 3.537797 | 185 | 180 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.205276 | 0.200187 | 0.210365 | 185 | 64 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | - | - | - | - | - | - |

### pop_006

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.160270 | 0.156526 | 0.164013 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000030 | -0.000131 | 0.000070 | 185 | 172 | True |
| Working Memory | measured | L1.1/noise_world | 0.163593 | 0.153969 | 0.173216 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.470270 | 10.350040 | 10.590500 | 185 | 5 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.193905 | 3.172915 | 3.214895 | 185 | 181 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.219168 | 0.214057 | 0.224278 | 185 | 65 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | - | - | - | - | - | - |

### pop_007

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.159957 | 0.156350 | 0.163564 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | 0.000010 | -0.000098 | 0.000119 | 185 | 174 | True |
| Working Memory | measured | L1.1/noise_world | 0.165446 | 0.154841 | 0.176051 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 11.097297 | 10.918191 | 11.276403 | 185 | 7 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.108797 | 3.089458 | 3.128136 | 185 | 181 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.224476 | 0.219383 | 0.229568 | 185 | 61 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | - | - | - | - | - | - |

### pop_008

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.165581 | 0.161870 | 0.169291 | 185 | 184 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000091 | -0.000166 | -0.000016 | 185 | 177 | True |
| Working Memory | measured | L1.1/noise_world | 0.155080 | 0.147275 | 0.162885 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.010811 | 9.989622 | 10.032000 | 185 | 2 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.460173 | 3.434251 | 3.486095 | 185 | 182 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.206605 | 0.201495 | 0.211716 | 185 | 59 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 2.000000 | 0.040000 | 3.960000 | 2 | 2 | True |

### pop_009

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.157739 | 0.154237 | 0.161241 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000010 | -0.000103 | 0.000083 | 185 | 180 | True |
| Working Memory | measured | L1.1/noise_world | 0.160796 | 0.151978 | 0.169614 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.264865 | 10.174709 | 10.355020 | 185 | 4 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.245168 | 3.223481 | 3.266855 | 185 | 181 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.215751 | 0.210662 | 0.220840 | 185 | 63 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 2.666667 | 1.573431 | 3.759902 | 6 | 3 | True |

### pop_010

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.156814 | 0.153370 | 0.160258 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000092 | -0.000193 | 0.000009 | 185 | 177 | True |
| Working Memory | measured | L1.1/noise_world | 0.152339 | 0.142378 | 0.162301 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 19.848649 | 19.465654 | 20.231644 | 185 | 14 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 2.768597 | 2.754499 | 2.782695 | 185 | 181 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.257654 | 0.252410 | 0.262898 | 185 | 68 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 7.143750 | 6.514550 | 7.772950 | 160 | 19 | True |

### pop_011

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.165063 | 0.161309 | 0.168816 | 185 | 184 | True |
| Pattern Retention | measured | L1.1/noise_world | 0.000020 | -0.000052 | 0.000093 | 185 | 171 | True |
| Working Memory | measured | L1.1/noise_world | 0.180719 | 0.172738 | 0.188699 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.005405 | 9.994811 | 10.016000 | 185 | 2 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.539637 | 3.511866 | 3.567409 | 185 | 180 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.204486 | 0.199398 | 0.209575 | 185 | 63 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | - | - | - | - | - | - |

### pop_012

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.160546 | 0.156663 | 0.164429 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000055 | -0.000159 | 0.000048 | 185 | 183 | True |
| Working Memory | measured | L1.1/noise_world | 0.158616 | 0.148790 | 0.168443 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 16.145946 | 15.146275 | 17.145617 | 185 | 23 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 2.692212 | 2.613161 | 2.771264 | 185 | 183 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.574324 | 0.568876 | 0.579772 | 185 | 71 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 107.702703 | 106.410813 | 108.994593 | 185 | 42 | True |

### pop_013

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.160703 | 0.156897 | 0.164508 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000027 | -0.000129 | 0.000074 | 185 | 177 | True |
| Working Memory | measured | L1.1/noise_world | 0.162452 | 0.152320 | 0.172583 | 185 | 183 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 41.659459 | 41.054624 | 42.264295 | 185 | 22 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 2.388486 | 2.378811 | 2.398162 | 185 | 178 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.354714 | 0.348367 | 0.361060 | 185 | 73 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | - | - | - | - | - | - |

### pop_014

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.157166 | 0.153763 | 0.160569 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000003 | -0.000094 | 0.000088 | 185 | 175 | True |
| Working Memory | measured | L1.1/noise_world | 0.159446 | 0.150772 | 0.168120 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.091892 | 10.040461 | 10.143322 | 185 | 4 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.306273 | 3.283876 | 3.328670 | 185 | 180 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.212443 | 0.207352 | 0.217535 | 185 | 64 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 4.000000 | 3.233188 | 4.766812 | 49 | 10 | True |

### pop_015

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.156610 | 0.153176 | 0.160044 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000095 | -0.000187 | -0.000003 | 185 | 183 | True |
| Working Memory | measured | L1.1/noise_world | 0.151559 | 0.142454 | 0.160663 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 12.210811 | 11.979822 | 12.441799 | 185 | 8 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.041534 | 3.023045 | 3.060023 | 185 | 182 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.229481 | 0.224369 | 0.234593 | 185 | 67 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 4.428571 | 3.811718 | 5.045424 | 84 | 11 | True |

### pop_016

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.164271 | 0.160553 | 0.167989 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000093 | -0.000187 | 0.000000 | 185 | 174 | True |
| Working Memory | measured | L1.1/noise_world | 0.155437 | 0.146670 | 0.164204 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 10.016216 | 9.992578 | 10.039855 | 185 | 3 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.393291 | 3.368891 | 3.417691 | 185 | 180 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.208876 | 0.203776 | 0.213976 | 185 | 66 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | - | - | - | - | - | - |

### pop_017

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.155396 | 0.151685 | 0.159108 | 185 | 182 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000079 | -0.000174 | 0.000015 | 185 | 180 | True |
| Working Memory | measured | L1.1/noise_world | 0.152305 | 0.142970 | 0.161640 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 11.270270 | 11.073097 | 11.467443 | 185 | 8 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 3.089106 | 3.069504 | 3.108709 | 185 | 181 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.228789 | 0.223528 | 0.234051 | 185 | 65 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | - | - | - | - | - | - |

### pop_018

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.153391 | 0.149864 | 0.156918 | 185 | 184 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000087 | -0.000182 | 0.000007 | 185 | 180 | True |
| Working Memory | measured | L1.1/noise_world | 0.147697 | 0.137924 | 0.157470 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 14.567568 | 14.257227 | 14.877908 | 185 | 13 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 2.941318 | 2.924533 | 2.958104 | 185 | 183 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.237059 | 0.231915 | 0.242204 | 185 | 63 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 8.464286 | 7.828537 | 9.100035 | 168 | 18 | True |

### pop_019

| Concept | Status | Source | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1/noise_world | 0.152185 | 0.148627 | 0.155744 | 185 | 185 | True |
| Pattern Retention | measured | L1.1/noise_world | -0.000122 | -0.000213 | -0.000032 | 185 | 178 | True |
| Working Memory | measured | L1.1/noise_world | 0.143054 | 0.134095 | 0.152013 | 185 | 185 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1/noise_world | 33.713514 | 33.159690 | 34.267337 | 185 | 19 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1/noise_world | 2.497005 | 2.486352 | 2.507659 | 185 | 179 | True |
| Final Energy Level | measured | L1.2/shock_world | 0.316497 | 0.310614 | 0.322381 | 185 | 79 | True |
| Homeostatic Resilience | measured | L1.2/shock_world | 1.363636 | 0.662673 | 2.064600 | 22 | 5 | True |

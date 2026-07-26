# CLOS Competency Profile

Profil minimalny: 7 osi z waznym CI95 / 14 pojec
Measured: 7/14
Insufficient data: 7/14
Generated at: 2026-07-17T05:16:23.109127

Definicje pojec: [cognitive_ontology.md](../clos_academy/cognitive_ontology.md).

## Profil minimalny (oficjalny)

Oficjalny profil kompetencji - WYLACZNIE pojecia, dla ktorych wszystkie obecne genomy maja ci95_valid=True. UWAGA: to NIE jest jednorodna lista zdolnosci poznawczych - patrz cognitive_axes vs physiological_state_variables ponizej.

6 osi poznawczych (zmierzonych zdolnosci lub kandydatow na nie) + 1 zmienna(ych) stanu fizjologicznego. Zmienna stanu fizjologicznego mierzy STAN systemu (np. poziom energii), NIE jego zdolnosc do czegokolwiek - nie sumowac z osiami poznawczymi jako rownowazne wpisy 'kompetencji'.

Osie poznawcze: Pattern Recognition, Pattern Retention, Working Memory, Adaptation, Stability, Homeostatic Resilience

Zmienne stanu fizjologicznego: Final Energy Level

| Concept | Status | Source lesson | default value | default n_eff | highly_plastic value | highly_plastic n_eff | mean_diff | cohens_d |
|---|---|---|---|---|---|---|---|---|
| Pattern Recognition | measured | L1.1 | 0.151568 | 10 | 0.150072 | 10 | -0.001496 | -0.050008 |
| Pattern Retention | measured | L1.1 | -0.000097 | 10 | 0.000098 | 10 | 0.000195 | 0.276125 |
| Working Memory | measured | L1.1 | 0.156712 | 10 | 0.173229 | 10 | 0.016517 | 0.327187 |
| Adaptation | measured | L1.1 | 42.200000 | 7 | 10.500000 | 3 | -31.700000 | -8.904978 |
| Stability | measured | L1.1 | 2.445580 | 10 | 3.245140 | 10 | 0.799560 | 9.460857 |
| Final Energy Level | measured | L1.1 | 0.460800 | 6 | 0.413800 | 3 | -0.047000 | -8.701052 |
| Homeostatic Resilience | measured | L1.2 | 15.400000 | 7 | - | - | - | - |

## Profil pelny (wszystkie pojecia, luki jawne)

Wszystkie pojecia z ontologii, w tym zdegenerowane i insufficient_data - jawnie oznaczone, nie ukryte.

### Wazne (CI95, 7)

| Concept | Status | Source lesson | default value | default n_eff | highly_plastic value | highly_plastic n_eff | mean_diff | cohens_d |
|---|---|---|---|---|---|---|---|---|
| Pattern Recognition | measured | L1.1 | 0.151568 | 10 | 0.150072 | 10 | -0.001496 | -0.050008 |
| Pattern Retention | measured | L1.1 | -0.000097 | 10 | 0.000098 | 10 | 0.000195 | 0.276125 |
| Working Memory | measured | L1.1 | 0.156712 | 10 | 0.173229 | 10 | 0.016517 | 0.327187 |
| Adaptation | measured | L1.1 | 42.200000 | 7 | 10.500000 | 3 | -31.700000 | -8.904978 |
| Stability | measured | L1.1 | 2.445580 | 10 | 3.245140 | 10 | 0.799560 | 9.460857 |
| Final Energy Level | measured | L1.1 | 0.460800 | 6 | 0.413800 | 3 | -0.047000 | -8.701052 |
| Homeostatic Resilience | measured | L1.2 | 15.400000 | 7 | - | - | - | - |

### Zdegenerowane (0) - zmierzone, ale bez wiarygodnej wariancji

| Concept | Status | Source lesson | default value | default n_eff | highly_plastic value | highly_plastic n_eff | mean_diff | cohens_d |
|---|---|---|---|---|---|---|---|---|

### Insufficient data (7) - brak lekcji/mechanizmu

| Concept | Status | Source lesson | default value | default n_eff | highly_plastic value | highly_plastic n_eff | mean_diff | cohens_d |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |

## Obserwacje dodatkowe (nie wliczone do puli CI95)

Wartosci z lekcji jawnie oznaczonych `"pool": False` w `CONCEPT_METRIC_MAP` (clos_scientist/capability_analyzer.py) - policzone osobno, NIGDY nie mieszane ze wartoscia oficjalna pojecia powyzej. Powod zawsze podany w `note`.

| Concept | Lekcja | Genom | value | ci95_valid | deterministic | n | note |
|---|---|---|---|---|---|---|---|
| Adaptation | L1.2 | default | 10.000000 | False | True | 10 | L1.2 adaptation_tick jest stala (=10, wszystkie seedy/genomy): mierzy stabilizacje entropii w oknie PRZED szokiem (t_shock zawsze >=20), nie adaptacje DO szoku. Nie laczona z pula L1.1 |
| Adaptation | L1.2 | highly_plastic | 10.000000 | False | True | 10 | L1.2 adaptation_tick jest stala (=10, wszystkie seedy/genomy): mierzy stabilizacje entropii w oknie PRZED szokiem (t_shock zawsze >=20), nie adaptacje DO szoku. Nie laczona z pula L1.1 |

## Karty genomow

### default

| Concept | Status | Source lesson | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1 | 0.151568 | 0.133546 | 0.169591 | 10 | 10 | True |
| Pattern Retention | measured | L1.1 | -0.000097 | -0.000515 | 0.000322 | 10 | 10 | True |
| Working Memory | measured | L1.1 | 0.156712 | 0.124980 | 0.188444 | 10 | 10 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1 | 42.200000 | 39.110624 | 45.289376 | 10 | 7 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1 | 2.445580 | 2.410612 | 2.480548 | 10 | 10 | True |
| Final Energy Level | measured | L1.1 | 0.460800 | 0.456304 | 0.465296 | 10 | 6 | True |
| Homeostatic Resilience | measured | L1.2 | 15.400000 | 12.767140 | 18.032860 | 10 | 7 | True |

### highly_plastic

| Concept | Status | Source lesson | value | ci95_low | ci95_high | n | n_effective | ci95_valid |
|---|---|---|---|---|---|---|---|---|
| Perception | insufficient_data | - | - | - | - | - | - | - |
| Attention | insufficient_data | - | - | - | - | - | - | - |
| Pattern Recognition | measured | L1.1 | 0.150072 | 0.131021 | 0.169123 | 10 | 10 | True |
| Pattern Retention | measured | L1.1 | 0.000098 | -0.000357 | 0.000554 | 10 | 10 | True |
| Working Memory | measured | L1.1 | 0.173229 | 0.142390 | 0.204068 | 10 | 10 | True |
| Long-term Memory | insufficient_data | - | - | - | - | - | - | - |
| Prediction | insufficient_data | - | - | - | - | - | - | - |
| Adaptation | measured | L1.1 | 10.500000 | 10.061731 | 10.938269 | 10 | 3 | True |
| Exploration | insufficient_data | - | - | - | - | - | - | - |
| Generalization | insufficient_data | - | - | - | - | - | - | - |
| Planning | insufficient_data | - | - | - | - | - | - | - |
| Stability | measured | L1.1 | 3.245140 | 3.179834 | 3.310446 | 10 | 10 | True |
| Final Energy Level | measured | L1.1 | 0.413800 | 0.412316 | 0.415284 | 10 | 3 | True |
| Homeostatic Resilience | measured | L1.2 | - | - | - | - | - | - |

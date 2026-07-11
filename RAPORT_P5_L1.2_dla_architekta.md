# Raport dla architekta — SPRINT v0.9, Priorytet 5 (L1.2 Shock Recovery)

Status: **implementacja zakończona, wyniki zebrane, NIE zacommitowane.** Dwa
znaleziska architektoniczne poniżej wymagają decyzji przed commitem (sprint
wymaga 3 zielonych walidatorów przed każdym commitem — jeden jest obecnie
czerwony, patrz Odkrycie 2).

Branch: `v0.7.2-scientific-integrity`, ostatni commit: `cc84fa1` (P4,
prerejestracja L1.2 zatwierdzona). P5 dodaje wyłącznie nowe pliki
(`git diff --stat` na plikach śledzonych jest pusty) — Core nietknięty.

---

## 1. Wyniki eksperymentu (dokładnie wg preregistration_L1_2.json v0.9.3)

### recovery_time (primary endpoint)

| Genom | mean | CI95 | n | n_eff | ci95_valid | recovery_rate |
|---|---|---|---|---|---|---|
| `default` | 15.4 | [12.77, 18.03] | 10 | 7 | **True** | 10/10 (0% cenzury) |
| `highly_plastic` | — | — | 0 | 0 | **False** | 0/10 (**100% cenzury**) |

`highly_plastic` nigdy nie odzyskuje homeostazy w oknie W=150 ticków.
Mechanistycznie spójne z genomem: `decay_rate=0.05` (5× wyższy niż
`default=0.01`) daje 5× silniejszy przyrost entropii na jednostkę błędu
predykcji w `regulate()`, podczas gdy tempo ściągania w dół rośnie tylko o
~19% (`plasticity` 0.95 vs 0.8). To wygląda na realny, wytłumaczalny wynik,
nie artefakt implementacji.

### pre_shock_band_check — decyzja z danych zadziałała

**Oba genomy: `pre_shock_in_band_fraction = 0.0`** (próg 0.8 nieosiągnięty).
System nigdy nie zdążył osiągnąć pasma homeostazy B=[0.25, 0.5] przed
szokiem (t_shock ∈ [20,80] — za wcześnie po "narodzinach" Brain). Zgodnie z
regułą progową z prerejestracji: **endpoint automatycznie przeklasyfikowany
na `time_to_sustained_band` (arrival), nie `recovery_time` (return)** —
hipoteza "Brain odzyskuje homeostazę" wymaga korekty językowej na "Brain
**osiąga/ustanawia** homeostazę po szoku". `mixed_case=False` — oba genomy
po tej samej stronie progu, brak konfliktu międzygenomowego.

### adaptation_tick / stability_score — zdegenerowane, ale NIE z powodu przewidzianego w prerejestracji

Oba `n_effective=1, ci95_valid=False`, dla obu genomów, dla obu scenariuszy.

**Zdiagnozowana przyczyna** (zweryfikowana przed zaraportowaniem, żeby
odróżnić prawdziwy wynik od błędu w kodzie): `kernel.snapshot_engine.get_all_snapshots()`
zwraca **0 snapshotów**. Pętla lekcji (identycznie jak w L1.1) woła
`world.step()` + `brain_rt.step()` bezpośrednio, nigdy `kernel.run_tick()`
— jedyną metodę Kernela, która faktycznie tworzy snapshot
(`clos_kernel/kernel.py:64`). `detect_phases()`/`stability_index()` przy
`len(snapshots)==0` degenerują trywialnie do zera z definicji.

To **nie jest nowy błąd** — to ten sam mechanizm degeneracji, który już
wystąpił w L1.1 i został udokumentowany w `RAPORT_KONCOWY_v0.8.4.md`. Ale
moje uzasadnienie w prerejestracji P4 ("shock_tick/shock_magnitude powinny
dać wariancję między seedami") było **błędne u podstaw** — problem leży
wcześniej niż wrażliwość metryki na wariancję scenariusza: snapshoty są
zawsze puste, niezależnie od scenariusza. Zgodnie z `degenerate_result_clause`
z prerejestracji raportuję to wprost, bez modyfikowania Kernela (poza
zakresem P5 — Core nietknięty).

### Glass's delta (kontrola, wariant B)

Nieobliczalne dla obu genomów: `"grupa eksperymentalna bez wariancji"` —
bezpośrednia konsekwencja degeneracji `stability_score` powyżej.

---

## 2. Odkrycie architektoniczne #1: Capability Analyzer nie skaluje się na L1.2

```
load_academy_reports() -> klucze: ['L1.1', 'L1.2']     # loader OK
build_capability_profile() -> WSZYSTKIE source_lesson nadal = 'L1.1'
```

**Przyczyna:** `CONCEPT_METRIC_MAP` w `clos_scientist/capability_analyzer.py`
hardkoduje **dokładnie jeden `lesson_id` na pojęcie**
(`{"lesson": "L1.1", "extract": ...}`). L1.2 dotyka tych samych pojęć co
L1.1 (Adaptation, Stability), ale mapa nie ma mechanizmu "wielu lekcji na
jedno pojęcie". Dodatkowo `recovery_time`/`time_to_sustained_band` nie
odpowiada żadnemu z 13 istniejących pojęć `cognitive_ontology.md` — to
potencjalnie nowa oś poznawcza (odporność homeostatyczna), nie mieszcząca
się w obecnym schemacie bez zmiany ontologii.

**Nie modyfikowałem `capability_analyzer.py` w P5** (poza zakresem —
naturalnie należy do P6 "profil minimalny").

**Opcje dla architekta (do decyzji w P6, nie teraz):**
- (a) Rozszerzyć `CONCEPT_METRIC_MAP` o listę lekcji na pojęcie zamiast
  pojedynczej wartości (agregacja/wybór "najlepszej" lekcji per pojęcie).
- (b) Dodać 14. pojęcie do ontologii ("Homeostatic Resilience" czy podobne)
  dla `recovery_time`/`time_to_sustained_band` — realna zmiana treści
  `cognitive_ontology.md`, nie tylko kodu.
- (c) Zostawić L1.2 poza Capability Analyzer na razie, jawnie udokumentować
  ograniczenie, odłożyć do przyszłego sprintu.

---

## 3. Odkrycie architektoniczne #2: validate_artifacts.py fałszywie alarmuje na cenzurowanie

```
$ python scripts/validate_artifacts.py
VALIDATE_ARTIFACTS: 1 problem(ow) w 2 raportach
  FAIL: L1_2_shock_recovery.json: genom 'highly_plastic', scenariusz stochastyczny
  'shock_world' ma ci95_valid=False (n_effective=0) - blad, oczekiwana wariancja miedzyseedowa
```

Walidator (P3, `SPRINT_v0.8.4.md`) traktuje **każde** `ci95_valid=False` na
scenariuszu stochastycznym jako błąd pseudoreplikacji — słuszne założenie
dla L1.1, gdzie taki wynik faktycznie sygnalizowałby bug. Dla L1.2 to
**fałszywy alarm**: `ci95_valid=False` dla `highly_plastic` to zamierzony,
prerejestrowany wynik reguły `min_non_censored=5` (100% cenzurowania to
prawdziwe zjawisko naukowe, nie usterka).

**To blokuje czysty commit** — reguła sprintu wymaga 3 zielonych
walidatorów przed każdym commitem. Obecnie: `validate_publication.py` OK
(6 bundli), `validate_panel.py` OK (nieużyty w tym priorytecie, ale
niezależnie zielony), **`validate_artifacts.py` CZERWONY**.

**Opcje dla architekta:**
- (a) Rozpoznać cenzurowanie jako sankcjonowany wyjątek: jeśli raport ma
  pole typu `recovery_time_detail.n_censored`/`min_non_censored`, walidator
  sprawdza zgodność z TĄ regułą zamiast generycznego "ci95_valid nigdy nie
  może być False".
- (b) Zawęzić istniejący check do L1.1 (lesson-specific), nowy,
  lekcjo-świadomy check dla L1.2 — więcej kodu, ale zero ryzyka osłabienia
  istniejącej ochrony przed pseudoreplikacją.
- (c) Zaakceptować czerwony wynik jako świadomie udokumentowany wyjątek
  (np. allowlist per run_id w konfiguracji CI) bez zmiany logiki walidatora.

Nie wybrałem żadnej opcji sam — czekam na decyzję, dokładnie jak przy
`pre_shock_band_check` w P4.

---

## 4. Stan testów i walidatorów

| Sprawdzenie | Wynik |
|---|---|
| `pytest -q` | **273 passed** (`test_step_regression` zielony) |
| `validate_publication.py` | **OK** (6 bundli, L1.2 z pełną prowenancją 5/5 pól) |
| `validate_panel.py` | OK (niezmieniony w tym priorytecie) |
| `validate_artifacts.py` | **FAIL** (Odkrycie #2 powyżej) |
| Capability Analyzer | Działa bez crasha, ale nie absorbuje L1.2 (Odkrycie #1) |

## 5. Dostarczone artefakty (nieskomitowane)

- `clos_academy/lesson_L1_2.py` — implementacja 1:1 wg prerejestracji
  (pasmo B, N=10, W=150, total_ticks=300, min_non_censored=5, próg
  pre_shock_band_check=0.8, kontrola wariant B).
- `clos_academy/publish_L1_2.py` — generator bundla (mirror `publish_L1_1.py`).
- `publications/L1_2_shock_recovery/` — pełny bundle, prowenancja 5/5 pól,
  git_commit `cc84fa1536c0c50aa197aa20af8793cb59109610`.
- `reports/academy/L1_2_shock_recovery.json` — raport lekcji.

## 6. Rekomendacja

Nie rekomenduję wyboru za architekta w żadnym z dwóch odkryć — oba mają
realne kompromisy (patrz opcje wyżej). Sugeruję jednak rozdzielić decyzje
w czasie: Odkrycie #2 (walidator) blokuje commit P5 **teraz** i wymaga
decyzji przed przejściem dalej; Odkrycie #1 (Capability Analyzer) jest
jawnie w zakresie P6 i może poczekać do tego priorytetu bez blokowania P5.

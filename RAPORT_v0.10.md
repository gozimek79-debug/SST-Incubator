# Raport końcowy — Sprint v0.10 (Observation Layer)

Branch: `v0.7.2-scientific-integrity`. Zakres: `beec073..HEAD` (8 commitów,
w tym 3 auto-commity CI). Status projektu: **Research Grade Infrastructure
for Artificial Ontogenesis** — bez zmian względem v0.9. Cel sprintu:
naprawić warstwę obserwacji ZANIM dodamy nowe zdolności poznawcze —
sprint **infrastrukturalny**, zero Predictive Coding / Latent Space /
IDIO-MORPH jako kod.

---

## 1. Lista commitów sprintu

| Commit | Priorytet | Opis (jedno zdanie) |
|---|---|---|
| `3b4cfff` | P1 | Spec Snapshot Observer (Read-Only, addytywny) + dowód usuwalności — pola Execution 40/40 bajtowo identyczne z/bez obserwatora na L1.1, tylko `stability_score`/`adaptation_tick` się zmieniają. |
| `2a4d531` | (auto, CI) | `ci: aktualizacja reports/status.json [skip ci]`. |
| `c3317e0` | P2 | Read-Only Observer na L1.2 (lustrzane do L1.1), dowód usuwalności sformalizowany jako `tests/test_observer_removability.py` (5 testów, L1.1+L1.2). |
| `e8167f0` | (auto, CI) | `ci: aktualizacja reports/status.json [skip ci]`. |
| `c6121cb` | P3+P4 | Re-run L1.1/L1.2 na realnych snapshotach (Adaptation/Stability real CI95) + Competency Profile i panel odzwierciedlają nowy stan (5→7 osi, reguła N:M `pool=False` dla Adaptation). |
| `87e3432` | (auto, CI) | `ci: aktualizacja reports/status.json [skip ci]`. |
| `73784b6` | P5 | `scripts/validate_observability.py` — walidator telemetrii (count≥20, monotoniczność, kompletność sekwencji, timestampy), `snapshot_diagnostics` addytywnie w L1.1/L1.2, test negatywny w CI. |
| (ten commit) | P6 | Ten raport + zasada Execution/Observation w `docs/architecture.md` + nota IDIO-MORPH + ROADMAP. |

---

## 2. Co było naprawione: dług był DWUWARSTWOWY

`RAPORT_v0.9.md` zdiagnozował dług jako "żadna lekcja nie woła
`kernel.run_tick()`". To była tylko połowa problemu — P1 tego sprintu
ujawnił drugą warstwę:

1. **Warstwa 1 (już znana):** `lesson_L1_1.py`/`lesson_L1_2.py` wołają
   `world.step()` + `brain_rt.step()` bezpośrednio w pętli, nigdy
   `kernel.run_tick()` — jedyne miejsce w Kernelu tworzące snapshot
   ([clos_kernel/kernel.py:92](clos_kernel/kernel.py)). Stąd
   `kernel.snapshot_engine.get_all_snapshots()` zawsze zwracał `[]`.
2. **Warstwa 2 (odkryta w P1, nieudokumentowana wcześniej):** nawet gdyby
   ktoś naiwnie przepiął lekcje na wołanie `kernel.run_tick()` zamiast
   naprawiać to poprawnie, snapshot i tak byłby bezwartościowy —
   `entropy=0.0, energy=100.0` są zaszyte na sztywno w
   [`kernel.py:98-99`](clos_kernel/kernel.py:98), niezależnie od
   faktycznego stanu `tissue`. `run_tick()` architektonicznie nie ma
   dostępu do obiektu `BrainTissue` używanego przez lekcję.

Te dwie warstwy razem są dodatkowym uzasadnieniem Warunku 1 CTO
("`kernel.run_tick()` NIE staje się jedyną ścieżką") — przepięcie na
`run_tick()` nie tylko ryzykowałoby zmianą ścieżki RNG/schedulera, ale
**i tak dałoby śmieciowe dane** bez osobnej przebudowy kontraktu Kernela.
Naprawa poszła inną drogą: Read-Only Observer woła bezpośrednio już-czystą
`SnapshotEngine.create_snapshot()` z **realnych** wartości `tissue.entropy`/
`tissue.energy`, jedną dodatkową linią w pętli lekcji, obok istniejących
wywołań — patrz [docs/spec_snapshot_observer.md](docs/spec_snapshot_observer.md).

---

## 3. Dowód usuwalności obserwatora (test CTO)

Test: `Snapshot Engine` jest poprawnym Read-Only Observerem, jeśli jego
usunięcie (`observe=False`) nie zmienia ANI JEDNEJ wartości z Execution
Pipeline — tylko wartości, które są z definicji funkcją snapshotów
(Observation Pipeline).

Zweryfikowane na pełnej macierzy L1.1 (2 genomy × 2 scenariusze × 10
seedów = 40 runów, identyczna z `publish_L1_1.py`), sformalizowane jako
`tests/test_observer_removability.py` (5 testów, L1.1+L1.2, część CI od
P2):

- **Pola EXECUTION** (`primary_endpoint`, `mse_stimulus_phase`,
  `mse_silence_phase`, `memory_decay_rate`, `final_energy`,
  `final_entropy`, `memory_size`, `telemetry`) — **40/40 bajtowo
  identyczne** z obserwatorem włączonym i wyłączonym.
- **Pola OBSERVATION** (`stability_score`, `adaptation_tick`) — 40/40 się
  zmieniają (np. run 0: `stability_score` 0.0→2.4127,
  `adaptation_tick` 0→47) — to jest naprawa długu, nie regresja.

---

## 4. Pełna regresja harnessu (Warunek 3 CTO)

| Sprawdzenie | Wynik |
|---|---|
| `test_step_regression` | zielony (Core nietknięty od P2 wzwyż) |
| L1.1: 40/40 `run_*.json` bundla + primary endpoint | `mean=0.156712` (default) / `0.173229` (highly_plastic) — **niezmienione** |
| L1.2: primary endpoint (`recovery_time`) | `default: 15.4`, `highly_plastic: 0 (100% censored)` — **niezmienione** |
| Hash wyników (pola Execution) | identyczny z/bez obserwatora (§3) |
| Raport Capability Analyzer | `Adaptation`/`Stability` oficjalne CI95 liczone WYŁĄCZNIE z L1.1 — dodanie L1.2 jako `pool: False` nie zmienia ani jednej cyfry (`test_adaptation_pooled_stats_match_l1_1_only_ci95`) |
| Raport publikacyjny (bundle) | zregenerowany z nową proweniencją (`git_commit`), struktura niezmieniona |
| Testy | 263 (v0.9) → **309 passed** (v0.10, koniec sprintu) |
| Walidatory CI | `validate_publication`, `validate_artifacts`, `validate_panel`, `validate_observability` — wszystkie OK |

Core (`clos_brain/`, `clos_kernel/`, `genome/`, `birth/`) — **zero plików
dotkniętych w całym sprincie** (zweryfikowane `git show --stat` na każdym
commicie z filtrem tych katalogów).

---

## 5. Realne Adaptation/Stability — trójstan A/B/C

| Lekcja | Genom | Metryka | mean | CI95 | n_eff | ci95_valid | Stan |
|---|---|---|---|---|---|---|---|
| L1.1 | default | adaptation_tick | 42.20 | [39.11, 45.29] | 7 | True | **A** |
| L1.1 | default | stability_score | 2.4456 | [2.4106, 2.4805] | 10 | True | **A** |
| L1.1 | highly_plastic | adaptation_tick | 10.50 | [10.06, 10.94] | 3 | True | **A** |
| L1.1 | highly_plastic | stability_score | 3.2451 | [3.1798, 3.3104] | 10 | True | **A** |
| L1.2 | default | adaptation_tick | 10.0 | — (std=0) | 1 | False | **B** |
| L1.2 | default | stability_score | 1.7241 | [1.7062, 1.7420] | 10 | True | **A** |
| L1.2 | highly_plastic | adaptation_tick | 10.0 | — (std=0) | 1 | False | **B** |
| L1.2 | highly_plastic | stability_score | 1.6685 | [1.6104, 1.7267] | 10 | True | **A** |

**Stan C (błąd infrastruktury): brak, nigdzie.** `snapshot_count` = 200/200
(L1.1) i 300/300 (L1.2) dla wszystkich sprawdzonych runów — zawsze ≥20,
monotoniczne, kompletne (zweryfikowane przez `validate_observability.py`
od P5).

### (b) L1.2 `adaptation_tick=10` — stan B, ale NIE degeneracja adaptacji do szoku

Zweryfikowane bezpośrednio na surowych wartościach: **dokładnie 10, dla
wszystkich 10 seedów, obu genomów, bez wyjątku**. Mechanizm: `_shock_tick()`
zawsze losuje `t_shock ∈ [20,80]`
([clos_academy/lesson_L1_2.py](clos_academy/lesson_L1_2.py)), a
`detect_phases()._find_chaos_end()` sprawdza pierwsze okno od `tick=10` —
**zawsze przed szokiem**, gdzie entropia narasta identycznym, gładkim
rampem niezależnie od seeda/genomu (żaden sygnał specyficzny dla genomu
czy szoku jeszcze tam nie dotarł). L1.2's `adaptation_tick` mierzy więc
"kiedy stabilizuje się baseline PRZED szokiem", nie "adaptację DO szoku" —
inne zjawisko niż L1.1's `adaptation_tick`, mimo tej samej nazwy metryki i
tej samej funkcji ją liczącej. Z tego powodu `CONCEPT_METRIC_MAP["Adaptation"]`
([clos_scientist/capability_analyzer.py](clos_scientist/capability_analyzer.py))
NIE łączy tej wartości do wspólnej puli CI95 (`"pool": False`, jawna
reguła — patrz §6) — widoczna osobno jako `secondary_observations`
(`ci95_valid=False`, `deterministic=True`), z notą wyjaśniającą wprost w
kodzie, `cognitive_ontology.md` i `competency_profile.md`. To jest
świadomie NIE naprawione (bo nie ma czego naprawiać — to poprawny,
zmechanizowany wynik o konstrukcji L1.2), tylko poprawnie zaklasyfikowane
i odizolowane od reszty danych.

---

## 6. Competency Profile: 5→7 osi, reguła N:M jawna

Profil minimalny (oficjalny) urósł z **5/14 do 7/14** — wyłącznie jako
konsekwencja danych (`_concept_validity_state` liczy z surowych
`ci95_valid`, nie z wpisanej liczby — `test_minimal_profile_axes_match_...`
przelicza to niezależnie w teście). Nowe osie: **Adaptation**, **Stability**
(obie zasilane wyłącznie z L1.1).

**Reguła agregacji N:M, gdy jedno źródło daje ważny CI95 a drugie stałą**
(`CONCEPT_METRIC_MAP`, `clos_scientist/capability_analyzer.py):

- Każdy mapping ma flagę `"pool": bool` (domyślnie `True`).
- `pool=True` → wartości wchodzą do wspólnej puli `genome_values`,
  zasilają oficjalne CI95 pojęcia (traktowane jak niezależne repliki tego
  samego zjawiska).
- `pool=False` → wartość NIGDY nie wchodzi do puli. Trafia do osobnego
  pola `secondary_observations` (CI95 per genom liczone **osobno**,
  `deterministic`/`ci95_valid` widoczne wprost), z obowiązkową `note`
  tłumaczącą powód.
- Decyzja `pool` jest **jawna flaga w kodzie**, nie automatyczna heurystyka
  ("czy wygląda na stałą") — bo pooling zakłada, że źródła mierzą to samo
  zjawisko; to jest osąd naukowy, nie coś do zgadnięcia z danych w locie.

Zastosowanie: `Adaptation ← L1.2` ma `pool=False` (§5b). Oficjalna wartość
Adaptation (z L1.1) jest bajtowo niezmieniona przez dodanie L1.2 jako
źródła — zweryfikowane regresyjnie.

**Stability ← L1.2** (też teraz `ci95_valid=True` od P3) świadomie NIE
połączona z L1.1 w tym sprincie — L1.1 (pattern echo) i L1.2 (shock
recovery) to różne konteksty zadaniowe; czy są współmierne jako repliki
ogólnej stabilności genomu, to osobna decyzja naukowa, odłożona poza
zakres P4 (pytanie CTO dotyczyło wprost tylko Adaptation).

### (c) Duże Cohen's d — pewność statystyczna, NIE duży efekt praktyczny

`competency_profile.md` pokazuje Cohen's d = **9.46** dla Stability i
**-8.70** dla Energy Efficiency między genomami. To NIE oznacza
"kolosalnej różnicy" w sensie potocznym — oznacza **bardzo małą wariancję
wewnątrz genomu** w mianowniku:

| Pojęcie | Genom | mean | std wewnątrz genomu | mean_diff | Cohen's d |
|---|---|---|---|---|---|
| Stability | default | 2.4456 | 0.0564 | 0.7996 | 9.46 |
| Stability | highly_plastic | 3.2451 | 0.1054 | | |
| Energy Efficiency | default | 0.4608 | 0.0073 | -0.0470 | -8.70 |
| Energy Efficiency | highly_plastic | 0.4138 | 0.0024 | | |

Energy Efficiency: różnica średnich to **-0.047** (~10% wartości) — skromna
w kategoriach bezwzględnych — ale odchylenie standardowe wewnątrz genomu
to **0.002-0.007**, więc Cohen's d (różnica / pooled std) wychodzi
ogromne. Interpretacja poprawna: "genomy różnią się w sposób bardzo
powtarzalny między seedami" (wysoka pewność statystyczna), NIE "genomy
różnią się drastycznie w praktyce" (duży efekt). Mylenie tych dwóch jest
częstym błędem interpretacyjnym Cohen's d przy małej wariancji resztowej —
odnotowane tutaj wprost, żeby czytelnik `competency_profile.md` nie
wyciągnął błędnego wniosku z samej wielkości liczby.

---

## 7. Ocena gotowości

**Zrobione i zweryfikowane:**
- Nowy formalny podział Execution/Observation Pipeline (Warunek 6 CTO),
  zapisany trwale w `docs/architecture.md` (patrz commit tego raportu).
- Read-Only Observer zaimplementowany, dowód usuwalności zweryfikowany
  empirycznie (nie tylko zadeklarowany) i sformalizowany jako test
  regresyjny w CI.
- Adaptation/Stability przestały być zdegenerowane u źródła — zamknięty
  dług udokumentowany w `RAPORT_KONCOWY_v0.8.4.md` i `RAPORT_v0.9.md`.
- Walidator telemetrii (`validate_observability.py`) blokuje scalenie przy
  braku/niekompletności snapshotów — zanim metryki zdążą je cicho
  zdegenerować do zera.

**NIE zrobione / świadome ograniczenia:**
- **Stability z L1.2 nie jest połączona z L1.1** — decyzja naukowa o
  współmierności między kontekstami zadaniowymi odłożona (§6).
- **L1.2 adaptation_tick pozostaje strukturalnie stałe** — to nie jest coś
  do "naprawienia" (§5b), ale oznacza, że L1.2 nigdy nie dostarczy
  realnego pomiaru "adaptacji do szoku" bez zmiany definicji endpointu
  (poza zakresem tego sprintu, wymagałoby rewizji prerejestracji L1.2).
- **Cała warstwa Academy nadal zweryfikowana tylko na L1.1+L1.2** — reguła
  `pool` nie była testowana na trzeciej, strukturalnie innej lekcji.
- **IDIO-MORPH pozostaje wyłącznie hipotezą** — zero kodu, zero planu
  implementacji (§8).

## 8. Nota IDIO-MORPH (rationale, zero kodu)

Warstwa obserwacji zbudowana w tym sprincie (Read-Only Observer,
`snapshot_diagnostics`, walidator telemetrii) jest **warunkiem wstępnym**,
nie ozdobnikiem, dla jakiejkolwiek przyszłej próby zmierzenia czterech
kierunków z `docs/idio_morph_hypothesis.md`. Bez wiarygodnej, zweryfikowanej
telemetrii nie da się odróżnić:

- realnej idiosynkratycznej reprezentacji (§1.3 tam) od artefaktu
  metryki liczonej na niepełnych/pustych danych (dokładnie to, co
  degenerowało Adaptation/Stability do v0.9 włącznie);
- realnej zmiany granularności kodowania w czasie (§1.1) od szumu
  pomiarowego wynikającego z brakujących snapshotów w części trajektorii;
- prawdziwego efektu metabolicznego pamięci (§1.4) od zdegenerowanego
  `stability_index()`/`detect_phases()` liczonego poniżej progu 20
  snapshotów.

Innymi słowy: v0.10 nie przybliża IDIO-MORPH treściowo (zero kodu w
`clos_brain/`, zero nowych pojęć w `cognitive_ontology.md` dla tych
kierunków), ale usuwa jedną z przeszkód, które uniemożliwiłyby
odróżnienie "to działa" od "to tylko tak wygląda w danych, bo dane są
zepsute" — patrz `docs/idio_morph_hypothesis.md` §4 (dodane w tym
sprincie).

## 9. Status projektu

**Research Grade Infrastructure for Artificial Ontogenesis** — bez zmian.
Infrastruktura integralności rozszerzona w tym sprincie o formalny podział
Execution/Observation Pipeline jako trwałą zasadę architektoniczną (nie
tylko dyscyplinę tego sprintu). Zawartość naukowa: profil minimalny 7/14
(było 5/14), z jawną klasyfikacją trójstanu wszędzie, gdzie to zastosowanie.
Zero fałszywych twierdzeń o "dużych efektach" tam, gdzie liczba odzwierciedla
tylko pewność statystyczną (§6c) — to jest zamierzone i jawne, nie
przeoczenie.

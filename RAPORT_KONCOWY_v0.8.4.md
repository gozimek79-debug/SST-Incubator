# Raport końcowy — Sprint v0.8.4 (Integralność infrastruktury)

Branch: `v0.7.2-scientific-integrity`. Zakres: `1edbc72..HEAD` (7 commitów).
Status projektu: **Research Grade Infrastructure**. **NIE** Publication Ready,
**NIE** Production Ready.

---

## 1. Lista commitów sprintu

`git log --oneline 1edbc72..HEAD`:

| Commit | Priorytet | Opis (jedno zdanie) |
|---|---|---|
| `91e4766` | P2 | Przełączenie L1.1 z ręcznego szumu na `stable_world` na scenariusz `noise_world`, `stable_world` jako osobna kontrola; nowa prerejestracja zsynchronizowana z kodem. |
| `b2a8383` | P1 | Publication Bundle L1.1 z pełną prowenancją (`git_commit`, `config_hash`, `manifest_hash`, `timestamp`, `experiment_id`); legacy `EXP-*` otagowane `legacy-pre-0.7.2` bez fabrykowania danych. |
| `8699ffb` | P3 | CI na GitHub Actions (Python 3.12, pytest, dwa walidatory) + `scripts/validate_publication.py` i `scripts/validate_artifacts.py`, oba z testem negatywnym potwierdzającym, że faktycznie coś wykrywają. |
| `2f7af6b` | P4.1 | `clos_academy/cognitive_ontology.md` — 13 pojęć, każde z mierzalnym korelatem zakotwiczonym w konkretnym pliku/funkcji kodu, jawne `not yet measured` tam, gdzie nie ma lekcji. |
| `954b1f8` | P4.2 | `clos_scientist/capability_analyzer.py` — mapuje endpointy L1.1 na pojęcia ontologii, `insufficient_data` bez wartości liczbowej, Cohen's d między genomami (nie Glass's delta). |
| `ddedf70` | P4.3 | `clos_scientist/competency_profile.py` + `publications/competency_profile.json`/`.md` — formatowanie wyjścia analizatora (zero nowych obliczeń), karty genomów. |
| `b56d982` | P5+P6 | `README.md`, `ROADMAP.md`, `docs/spec_partial_step.md`; usunięcie sprzecznego, osieroconego `cognitive_ontology.md` z katalogu głównego. |

**Uwaga o pushu:** commity do `ddedf70` są wypchnięte na `origin` i mają
potwierdzone zielone przebiegi CI (patrz sekcja 3). Commit `b56d982` (P5+P6)
jest **lokalny, jeszcze niewypchnięty w momencie pisania tego raportu** — nie
ma dla niego przebiegu CI. Dotyczy wyłącznie plików `.md`, więc ryzyko jest
niskie, ale to nie jest to samo co "zweryfikowane".

---

## 2. Status priorytetów

### P1 — Integralność naukowa i prowenancja
**Dostarczono:**
- `publications/L1_1_pattern_echo/` — pełny Publication Bundle (manifest, provenance, metadata, 40 runów: 2 genomy × 2 scenariusze × 10 seedów).
- `clos_academy/publish_L1_1.py` — regeneruje bundle z bieżącego kodu (nie z zapisanych liczb).
- `clos_studio/publication/bundle.py` rozszerzony o `manifest_hash` (sha256 pliku `manifest.json` na dysku) i `timestamp`.
- 4 legacy bundle (`EXP-1C290805`, `EXP-3A59D747`, `EXP-89D9BA69`, `EXP-8C696B3C`) otagowane `"provenance": "legacy-pre-0.7.2"`; `git_commit` pozostawiony pusty, nic nie zgadywane.

**Świadomie NIE zrobiono:** pełnego "zregeneruj wszystkie raporty Academy" w sensie dosłownym poza L1.1, bo L1.1 to jedyna istniejąca lekcja — nie ma nic więcej do regeneracji.

### P2 — Prerejestracja L1.1 (noise_world)
**Dostarczono:**
- `clos_academy/lesson_L1_1.py` — usunięty ręczny `gaussian_noise` na `stable_world`; eksperyment na `scenario="noise_world"`, `stable_world` jako osobny przebieg kontrolny do Glass's delta.
- `publications/preregistration_L1_1.json` (nowa) + `publications/preregistration_L1_1_v0.8.json` (zachowana historia).

### P3 — Automatyzacja jakości (CI)
**Dostarczono:**
- `.github/workflows/ci.yml` — Python 3.12, `pytest -q`, potem oba walidatory, na `push` i `pull_request`.
- `scripts/validate_publication.py`, `scripts/validate_artifacts.py` — oba przetestowane negatywnie (wymuszony błąd → exit 1) przed uznaniem za działające.

### P4 — Cognitive Academy
**Dostarczono (wszystkie 3 części):**
- P4.1: `clos_academy/cognitive_ontology.md` — 13 pojęć.
- P4.2: `clos_scientist/capability_analyzer.py` + `tests/test_capability_analyzer.py` (7 testów).
- P4.3: `clos_scientist/competency_profile.py` + `publications/competency_profile.json`/`.md` + `tests/test_competency_profile.py` (8 testów).

**Ograniczenie uczciwości zachowane:** 7 z 13 pojęć ma `status: "insufficient_data"` i **zero** wartości liczbowych (`genomes: {}`, `genome_comparison: null`) — nie zgadywane, nie interpolowane.

### P5 — Dokumentacja
**Dostarczono:**
- `README.md`, `ROADMAP.md`.
- Usunięcie osieroconego, sprzecznego `cognitive_ontology.md` z katalogu głównego (odkryte przy okazji tej pracy, niezwiązane z pierwotnym zakresem P5, ale bezpośrednio naruszało zasadę "jedna obowiązująca definicja" z P4.1).

### P6 — Specyfikacja `partial_step()`
**Dostarczono:** `docs/spec_partial_step.md` — dokument, **zero implementacji, zero zmian w `clos_brain/`**. Certyfikuje jako bezpieczne do pominięcia wyłącznie krok `PERCEIVE` (bo `predict()`/`compute_error()` już to tolerują bez zmian w Core); pozostałe 6 kroków jawnie oznaczone jako wymagające osobnej analizy przed dodaniem.

---

## 3. Wyniki

- **Testy:** `263 passed` (`pytest -q`), lokalnie zweryfikowane po każdym priorytecie.
- **CI:** dwa przebiegi CI na GitHub Actions (commit `8699ffb` i `ddedf70`) zakończone zielono, zweryfikowane wizualnie w zakładce Actions. Push P5+P6 jeszcze nie wysłany w momencie pisania raportu — brak dla niego przebiegu CI.
- **L1.1 (noise_world, n=10 seedów/genom):**
  - `default`: mean MSE@50 = 0.156712, n=10, **n_effective=10**, **ci95_valid=True**.
  - `highly_plastic`: mean MSE@50 = 0.173229, n=10, **n_effective=10**, **ci95_valid=True**.
  - Kontrola (`stable_world`): deterministyczna, `ci95_valid=False` — poprawnie, to oczekiwane dla kontroli, nie błąd.
- **Prowenancja:** `publications/L1_1_pattern_echo/metadata.json` ma niepuste `experiment_id`, `git_commit`, `config_hash`, `manifest_hash`, `timestamp` — zweryfikowane programowo (`scripts/validate_publication.py` → `OK`).

---

## 4. Uczciwa ocena gotowości — co jest zrobione, a co NIE

**Zrobione i zweryfikowane:**
- Statystyka L1.1 (primary endpoint) jest realna — 10 różnych wartości na genom, nie pseudoreplikacja.
- Prowenancja bundli jest kompletna i zautomatyzowana (nie ręczna).
- CI faktycznie działa na GitHubie (zweryfikowane zdalnie, nie tylko "plik yml istnieje").
- Walidatory faktycznie wykrywają błędy (przetestowane negatywnie), a nie tylko zwracają 0 bezwarunkowo.

**NIE zrobione / ograniczenia, których nie ukrywam:**

1. **Competency Profile: 6/13 pojęć `measured`, 7/13 `insufficient_data`.** To nie jest "prawie kompletne" — to dosłownie mniej niż połowa. Perception, Attention, Long-term Memory, Prediction (w wąskim sensie), Exploration, Generalization, Planning nie mają żadnej lekcji ani mechanizmu (Exploration/Planning: `act()` to nadal czysty "echo input" v0.1, brak jakiegokolwiek mechanizmu wyboru działania).

2. **Adaptation i Stability są zmierzone, ale zdegenerowane.** Mimo że L1.1 działa na stochastycznym `noise_world`, `adaptation_tick` i `stability_score` wychodzą **identyczne dla wszystkich 10 seedów** w obu genomach (`n_effective=1`, `ci95_valid=False`). To nie błąd w Capability Analyzerze — to realna właściwość obecnych metryk (`detect_phases()` i `stability_index()`), które są w tym eksperymencie nieczułe na seed. Praktyczny skutek: z 6 "measured" pojęć tylko 4 (Working Memory, Pattern Recognition, Pattern Retention, Energy Efficiency) mają sensowny, niezdegenerowany CI95. Adaptation i Stability są zmierzone tylko w sensie "kod policzył liczbę", nie w sensie "liczba niesie informację o wariancji między seedami".

3. **Martwe/osierocone katalogi w drzewie repo:**
   - `core/` — **śledzony w git** (`__init__.py`, `base.py`, `config.py`, `engine.py`, `storage.py`), ale nigdzie nieimportowany przez żaden aktywny moduł. Realny dług do usunięcia (zweryfikowane: `git ls-files core/` → 5 plików, `grep -r "from core\.|import core"` poza `core/` → 0 wyników).
   - `brain/`, `dashboard/`, `scientist/`, `world/`, `api/` — puste katalogi na dysku roboczym, **nieśledzone w git** (nie pojawią się przy świeżym `git clone`). To nie jest dług repozytorium, tylko lokalny bałagan na tej konkretnej maszynie — ale wart odnotowania, bo myli przy przeglądaniu struktury.

4. **`partial_step()` to wyłącznie specyfikacja.** `docs/spec_partial_step.md` nie jest zaimplementowany, nie jest zmergowany do `clos_brain/`, nie ma testów poza planem testów opisanym w dokumencie. Obecny mechanizm ciszy w L1.1 nadal używa `clos_academy/echo_runtime.py` (duplikacja pipeline'u opisana w spec jako problem, nie rozwiązana). v0.9 (Predictive Coding, Latent Space) nie może się zacząć, dopóki ktoś nie zaakceptuje/odrzuci/zmodyfikuje tej specyfikacji i jej nie zaimplementuje.

5. **Jedna lekcja.** Cała warstwa Academy (ontologia, Capability Analyzer, Competency Profile) jest zweryfikowana wyłącznie na L1.1. Nie wiadomo, czy architektura Capability Analyzera (mapowanie pojęcie→lekcja→pole w JSON) wytrzyma drugą, strukturalnie inną lekcję bez przeróbek — to niesprawdzone.

---

## 5. Status projektu

**Research Grade Infrastructure.**

Nie "Publication Ready". Nie "Production Ready". Infrastruktura (CI,
prowenancja, statystyka, ontologia, walidatory) jest solidna i zweryfikowana
tam, gdzie twierdzę, że jest zweryfikowana. Zawartość naukowa (co system
faktycznie *wie* o sobie poznawczo) jest wąska: jedna lekcja, 4 z 13 pojęć z
niezdegenerowanym CI95, reszta jawnie oznaczona jako brakująca. To jest
zamierzone i uczciwe, nie przeoczenie — ale nie należy tego mylić z gotowym
systemem poznawczym.

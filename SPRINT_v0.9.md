# SPRINT v0.9 — partial_step(), dług, L1.2, profil minimalny (ZATWIERDZONY)

Gałąź: `v0.7.2-scientific-integrity`. Priorytet → testy → commit → push → audyt.
Status projektu: **Research Grade Infrastructure for Artificial Ontogenesis**.
Zakaz sformułowań sugerujących „Artificial Mind".

---

## NOWY INWARIANT (konstytucja projektu od v0.9)

Nie obowiązuje już `clos_brain/` diff = 0. Obowiązuje:

> **Chronimy niezmienność ZACHOWANIA systemu, nie niezmienność plików.
> Poznanie Brain pozostaje niezmienione, nawet jeśli Runtime API jest rozszerzane.**

Warunki obowiązkowe (bez nich każdy commit po P2 jest nieważny):
- `step()` daje identyczny wynik jak przed sprintem (test regresji, złote wartości).
- `partial_step(skip=[])` == `step()`.
- Wszystkie dotychczasowe eksperymenty (L1.1) przechodzą bez różnic liczbowych.
- Dozwolone wyłącznie zmiany ADDYTYWNE. Zero zmian w istniejących funkcjach poznawczych.

Zakazane: Predictive Coding, Latent Space, IDIO-MORPH jako kod produkcyjny,
nowe neurony/geny, zmiana istniejącej logiki poznawczej.

---

## P1 — Usunięcie długu `core/`
- `git rm -r core/` (zweryfikowane: 5 śledzonych plików, 0 importów spoza `core/`).
- `pytest -q` (263) potwierdza brak zależności. Osobny, mały commit.

## P2 — `partial_step()` jako Runtime API (addytywne)
- Dodaj `partial_step(brain, sensory_input, seed, tick, skip=())` do BrainRuntime.
- **Tylko `PERCEIVE` certyfikowany.** Próba pominięcia dowolnego innego kroku →
  **`NotImplementedError`** (świadomie niecertyfikowane, nie „zła wartość").
- Determinizm: seed liczony identycznie niezależnie od `skip`.
- Testy regresji (WYMAGANE — bez kompletu STOP):
  - `test_step_regression`: `step()` na ustalonych wejściach = złote wartości baseline.
  - `test_partial_equals_step`: `partial_step(skip=())` == `step()`.
  - `test_partial_skip_perceive`: bufor niezmieniony przy pominięciu percepcji.
  - `test_partial_rejects_other_steps`: `skip={PREDICT}` → `NotImplementedError`.
- Interfejs ogólny (nota IDIO-MORPH) — nie zawężaj tak, by blokował rozszerzenia.

## P3 — Refaktor `echo_runtime.py` na nowe API
- Zamień ręczne komponowanie prymitywów na `partial_step(skip={PERCEIVE})`.
- **Regresja krytyczna:** L1.1 po refaktorze = IDENTYCZNE liczby
  (mean MSE@50 default 0.156712 / plastic 0.173229, n_eff=10). Różnica → STOP.
- Regeneruj bundle L1.1 tylko jeśli liczby identyczne (nowy git_commit).

## P4 — Prerejestracja L1.2 (BRAMKA — przed implementacją)
- `publications/preregistration_L1_2.json`, scenariusz `shock_world`,
  kontrola `stable_world`. Standard: (a) hipoteza, (b) mechanizm, (c) kryterium
  matematyczne, (d) replikacja.
- **`recovery_time` MUSI mieć formalną definicję matematyczną** (bez niej
  eksperyment nie jest falsyfikowalny — twardy wymóg):
  - moment perturbacji (tick szoku),
  - pasmo homeostazy (konkretny przedział liczbowy),
  - warunek utrzymania stabilizacji (pozostanie w paśmie przez N ticków),
  - okno obserwacji.
- **Plan seedów:** określ MINIMALNĄ liczbę replik uzasadnioną potrzebą CI95 —
  nie wpisuj liczby na sztywno w architekturę. Kontroli deterministycznej nie
  mnóż sztucznie.
- Ta prerejestracja jest do przeglądu (CTO/audytor) PRZED P5. Nie implementuj L1.2,
  dopóki definicja `recovery_time` nie jest zatwierdzona.

## P5 — Implementacja L1.2 (odporność + skalowalność Academy)
- Lekcja mierząca `recovery_time` (primary endpoint STRUKTURALNIE INNY niż MSE@50 L1.1).
- **Cel: niezdegenerowane Adaptation i Stability** (n_eff>1, ci95_valid=True) —
  ALE jeśli zostaną zdegenerowane mimo poprawnego projektu, raportuj to jako
  WYNIK NAUKOWY, bez wyjątków. Nie dodawaj sztucznego szumu, by „zaliczyć".
- Pełny bundle z prowenancją; `reports/academy/L1_2_*.json`.
- **Test skalowalności:** Capability Analyzer wchłania L1.2 BEZ przeróbek
  architektury. Jeśli wymaga zmian — to odkrycie o architekturze, opisz je.

## P6 — Competency Profile: profil minimalny
- **Minimalny profil poznawczy** = WYŁĄCZNIE pojęcia z `ci95_valid=True`. Zero
  pojęć bez eksperymentu.
- Zdegenerowane i `insufficient_data` pozostają w PEŁNYM profilu jako osobna
  kategoria; profil MINIMALNY (oficjalny) ich nie zawiera. Rozróżnienie jawne.
- Panel Badacza czyta to automatycznie — sekcja „Profil kompetencji" pokazuje
  minimalny + pełny osobno.

## P7 — IDIO-MORPH (hipoteza) + status + dokumentacja
- `docs/idio_morph_hypothesis.md`: IDIO-MORPH jako OFICJALNA HIPOTEZA badawcza,
  cztery kierunki (dynamiczne kodowanie reprezentacji, morficzna kompresja,
  idiosynkratyczne reprezentacje semantyczne, metaboliczna optymalizacja pamięci)
  jako pytania badawcze. Zero kodu produkcyjnego.
- **Wymóg architektoniczny (negatywny):** architektura v0.9 (zwł. `partial_step()`)
  nie może zamknąć drogi do powyższych. Nie projektuj pod IDIO-MORPH spekulacyjnie —
  tylko nie zamykaj drzwi.
- README/ROADMAP: status „Research Grade Infrastructure for Artificial Ontogenesis";
  usuń ewentualne sformułowania sugerujące „umysł".

---

## KRYTERIUM ZAKOŃCZENIA
Działający `partial_step()` (regresja zielona) · `core/` usunięty · `echo_runtime`
na nowym API · prerejestracja L1.2 z formalnym `recovery_time` · L1.2 przeszła
lub uczciwie zaraportowana · skalowalność Academy potwierdzona · profil minimalny ·
pełna reprodukowalność · panel odzwierciedla stan · CI zielony · `RAPORT_v0.9.md`.

## DYSCYPLINA GITA
Jeden logiczny commit na priorytet; `pytest -q` + 3 walidatory zielone przed
commitem; `test_step_regression` zielony w KAŻDYM commicie po P2; komunikat =
realny stan. Na końcu push + potwierdzenie stanu zdalnego. Nie commituj `.claude/`
ani śmieci ze `storage/`.

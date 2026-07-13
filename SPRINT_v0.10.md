# SPRINT v0.10 — Observation Layer (snapshot pipeline) [ZATWIERDZONY przez CTO]

Gałąź: `v0.7.2-scientific-integrity`. Priorytet → testy → commit → push → audyt.
Status: **Research Grade Infrastructure for Artificial Ontogenesis.**

Cel: naprawić warstwę obserwacji ZANIM dodamy nowe zdolności — jako sprint
INFRASTRUKTURALNY. Bez wiarygodnych snapshotów Adaptation/Stability są
strukturalnie niemierzalne.

---

## NOWA ZASADA KONSTYTUCYJNA (CTO, od v0.10)

Projekt dzieli się formalnie na dwie warstwy:

- **Execution Pipeline:** World · Brain · Kernel · Lesson
- **Observation Pipeline:** Snapshot Engine · Capability Analyzer · Statistics · CI · Dashboard

> **Observation Pipeline NIGDY nie wpływa na Execution Pipeline.**

Test poprawności (falsyfikowalny, nie wybór API): **jeśli można całkowicie
usunąć Snapshot Engine i WSZYSTKIE wyniki eksperymentów pozostają bajtowo
identyczne — architektura jest poprawna.** Snapshot Engine jest **Read-Only
Observer**: nie wpływa na Brain, World, Kernel, RNG ani harmonogram.

To rozszerza inwariant „Behavior Frozen" z `step()` na cały harness eksperymentalny.

---

## SZEŚĆ WARUNKÓW CTO (obowiązkowe, bez kompletu sprint nieważny)

1. **Wyłącznie implementacja ADDYTYWNA** — żadnego zastępowania istniejącej
   ścieżki wykonania. `kernel.run_tick()` NIE staje się jedyną ścieżką (może
   zmienić moment poboru RNG / kolejność aktualizacji / propagację błędów →
   w systemie deterministycznym to zmienia wynik).
2. **Snapshot Engine = pasywny Read-Only Observer** — dołączony jako obserwator,
   nie jako nowy sterownik wykonania.
3. **Rozszerzony pakiet regresji** — nie tylko `step()`, ale cały harness: L1.1
   primary + wszystkie golden values, L1.2 primary, hash wyników, raport
   Capability Analyzer, raport publikacyjny — wszystkie identyczne.
4. **Jawne rozróżnienie trójstanu** (obowiązkowa część dokumentacji):
   A = snapshoty są + wariancja → sukces eksperymentu;
   B = snapshoty są + wariancja=0 → poprawny wynik naukowy (degeneracja realna);
   C = brak snapshotów → błąd infrastruktury. Nie wolno ich mieszać.
5. **Nowy walidator CI** — brak/niekompletność snapshotów blokuje scalenie.
6. **Formalne rozdzielenie Execution / Observation Pipeline** — trwała zasada.

Zakazane: Predictive Coding, Latent Space, IDIO-MORPH jako kod, zmiana logiki
poznawczej, zastąpienie ścieżki wykonania, jakikolwiek wpływ obserwacji na wykonanie.

---

## P1 — Test usuwalności obserwatora (BRAMKA, przed implementacją)

- Udokumentuj, dlaczego snapshoty są puste: lekcje wołają `world.step()`+
  `brain_rt.step()` bezpośrednio, nigdy `kernel.run_tick()` (jedyne miejsce
  tworzące snapshot).
- Zaprojektuj Snapshot Engine jako Read-Only Observer dołączany do pętli lekcji
  ADDYTYWNIE (obok istniejących wywołań, nie zamiast). Opisz mechanizm.
- **Dowód usuwalności (test CTO):** pokaż, że z obserwatorem i bez niego
  L1.1 daje BAJTOWO identyczny wynik (hash 40 run_*.json). To jest właściwy
  test — obecność obserwatora nie może zmienić ani jednej liczby.
- Pokaż mi: projekt obserwatora + dowód usuwalności (hash z/bez). Nie implementuj pełnej naprawy.

## P2 — Implementacja Read-Only Observer (addytywnie)

- Snapshot Engine produkuje realne snapshoty z tego samego stanu tissue, który
  daje istniejąca ścieżka — BEZ zmiany wywołań poznawczych.
- **Rozszerzony pakiet regresji (warunek 3 CTO), bez kompletu STOP:**
  - `test_step_regression` zielony,
  - L1.1: 40/40 run_*.json + wszystkie golden values bajtowo identyczne,
  - L1.2: primary endpoint identyczny,
  - hash wyników identyczny,
  - raport Capability Analyzer identyczny,
  - raport publikacyjny (bundle) identyczny.
- JAKAKOLWIEK różnica → STOP i eskaluj. Najpierw dowód, że zmieniono wyłącznie
  obserwację.
- Snapshot zawiera realną trajektorię (energia, entropia, stan) — sprawdź, że
  `detect_phases()`/`stability_index()` dostają sensowne wejście.

## P3 — Re-run L1.1 i L1.2 na realnych snapshotach

- **Warunek wejścia:** dopiero PO potwierdzeniu pełnej regresji z P2.
- Pokaż REALNE Adaptation/Stability per genom (mean, CI95, n_eff, ci95_valid).
- **Trójstan (warunek 4 CTO) jawnie:** dla każdej metryki zaklasyfikuj wynik jako
  A (wariancja), B (wariancja=0, realna degeneracja) lub — gdyby to wystąpiło —
  C (błąd infrastruktury). Nie mieszaj. Raportuj, co wyjdzie, bez wymuszania.

## P4 — Aktualizacja Competency Profile + panel

- Przelicz profil z realnych Adaptation/Stability.
- Stan A/B → oś dostaje realny status: jeśli ważny CI95 → może wejść do profilu
  MINIMALNEGO (5 → do 7 osi); jeśli wariancja=0 → profil pełny, `degenerate`,
  ale teraz z REALNEGO powodu (stan B), nie artefaktu (stan C).
- Panel odzwierciedla automatycznie; `validate_panel` OK.

## P5 — Walidator telemetrii (warunek 5 CTO)

- Nowy `validate_observability.py` (lub rozszerzenie): FAIL gdy metryki liczone
  przy braku LUB niekompletności snapshotów. Sprawdza nie tylko `count>0`, ale:
  `snapshot_count >= expected_minimum`, monotoniczność timeline, spójność
  timestampów, kompletność sekwencji.
- TEST NEGATYWNY: (1) 0 snapshotów pod metryką → exit≠0; (2) niemonotoniczny/
  niekompletny timeline → exit≠0; (3) realny kompletny raport → exit 0. Dodaj do CI.

## P6 — Raport + status + konstytucja

- `RAPORT_v0.10.md`: commity, co naprawiono, dowód usuwalności obserwatora,
  pełna regresja harnessu, REALNE Adaptation/Stability z klasyfikacją A/B/C,
  dług zamknięty.
- Zapisz zasadę Execution/Observation (warunek 6) do trwałej dokumentacji
  architektury (np. README/ROADMAP lub docs/architecture.md).
- Nota IDIO-MORPH (rationale, zero kodu): warstwa obserwacji to fundament, by
  KIEDYKOLWIEK odróżnić realne reprezentacje od artefaktów metryk.
- ROADMAP: v0.10 = Observation Layer (zrobione); Predictive Coding → v0.11.

---

## KRYTERIUM ZAKOŃCZENIA
Snapshoty produkowane (Read-Only Observer, dowód usuwalności) · pełna regresja
harnessu (L1.1/L1.2/analyzer/bundle bajtowo zachowane) · realne Adaptation/
Stability z jawną klasyfikacją A/B/C · profil zaktualizowany · walidator
telemetrii z testem negatywnym · zasada Execution/Observation w dokumentacji ·
`test_step_regression` zielony · CI zielony · RAPORT_v0.10.md.

## DYSCYPLINA GITA
Jeden logiczny commit na priorytet; jawna lista plików (nie `git add -A`);
pełna regresja + walidatory zielone przed commitem; komunikat = realny stan.
Push domykający + audyt. Nie commituj `.claude/` ani śmieci.

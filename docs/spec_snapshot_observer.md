# Spec: Snapshot Engine jako Read-Only Observer

**Status: P1 (bramka) SPRINT_v0.10.md — zaprojektowane i empirycznie
zweryfikowane (dowód usuwalności poniżej). P2 wykona pełne wdrożenie
(L1.1 + L1.2 + regresja harnessu). Ten dokument sam w sobie nie zmienia
żadnej ścieżki wykonania poza jednym prototypowym haczykiem w
`clos_academy/lesson_L1_1.py` opisanym w §4, potrzebnym wyłącznie do
przeprowadzenia dowodu.**

## 1. Dlaczego snapshoty są puste (root cause)

`Kernel.snapshot_engine` ([clos_kernel/kernel.py](../clos_kernel/kernel.py))
tworzy snapshot **wyłącznie** wewnątrz `Kernel.run_tick()`
(`clos_kernel/kernel.py:92`). Żadna lekcja Academy nigdy nie woła
`run_tick()`. `lesson_L1_1.py`/`lesson_L1_2.py` wołają `kernel.initialize()`
i `kernel.stop()` (dla `brain_id`/`max_ticks`/porządku), ale pętla
eksperymentu woła bezpośrednio:

```python
for tick in range(total_ticks):
    signal = world.step(tick=tick, seed=seed, scenario=scenario)
    tissue = brain_rt.step(brain=tissue, sensory_input=signal, seed=seed, tick=tick)
```

`kernel.snapshot_engine.get_all_snapshots()` wołane po pętli
(`lesson_L1_1.py:78`, `lesson_L1_2.py:107`) zwraca więc zawsze `[]`.
`detect_phases()`/`stability_index()` na pustej liście degenerują
trywialnie do zera z definicji (`clos_scientist/analyzer.py:23`,
`clos_scientist/metrics.py:17-18`) — niezależnie od scenariusza czy genomu.
To jest dokładnie odkrycie (c) z `RAPORT_v0.9.md`.

**Drugi, dotąd nieudokumentowany problem:** nawet gdyby `run_tick()` był
wołany, snapshot i tak byłby bezwartościowy — `entropy=0.0, energy=100.0`
są tam zaszyte na sztywno (`clos_kernel/kernel.py:98-99`), niezależne od
faktycznego stanu `tissue`. `run_tick()` nie ma dostępu do obiektu
`BrainTissue` używanego przez lekcję — architektonicznie nie mógłby
zwrócić realnych wartości bez przebudowy sygnatury. To wzmacnia decyzję
CTO, żeby NIE robić z `run_tick()` jedynej ścieżki (Warunek 1) — wymagałoby
to zmiany kontraktu Kernela, nie tylko podłączenia wywołania.

## 2. Projekt: Read-Only Observer

Zamiast przepinać lekcje na `kernel.run_tick()` (co zmieniłoby moment
poboru RNG / kolejność aktualizacji przez `TickEngine.next_tick()` →
`Scheduler.execute()` → `EventBus.publish()` — osobną ścieżkę wykonania
równoległą do istniejącej), obserwator woła **bezpośrednio** istniejącą,
już-czystą metodę `SnapshotEngine.create_snapshot()`
([clos_kernel/snapshot_engine.py:39](../clos_kernel/snapshot_engine.py)) —
ta metoda sama w sobie nie ma efektów ubocznych: nie konsumuje RNG, nie
dotyka `tissue`/`world`/`kernel`, tylko tworzy dataclass i dopisuje go do
lokalnej listy `self._snapshots`.

Dołączenie do pętli lekcji jest **addytywne** — jedna linia wywołania
wstawiona zaraz po już-istniejącym `tissue = brain_rt.step(...)` /
`tissue = silent_step(...)`, czytająca wartości, które i tak już zostały
obliczone:

```python
tissue = brain_rt.step(brain=tissue, sensory_input=pattern_signal, seed=seed, tick=tick)
# --- Read-Only Observer (dodane, nie zastępuje niczego powyżej) ---
kernel.snapshot_engine.create_snapshot(
    brain_id=tissue.brain_id, tick=tick, seed=seed,
    lifecycle_state="OBSERVED", brain_status="RUNNING",
    entropy=tissue.entropy, energy=tissue.energy,
    age=tick, step_counter=tick,
)
```

`kernel.run_tick()` pozostaje nietknięty i nadal nieużywany przez lekcje —
poza zakresem tego sprintu, bo nie jest na krytycznej ścieżce.

## 3. Dowód usuwalności (test CTO)

Test: jeśli obserwator jest poprawnie Read-Only, to usunięcie go (flaga
`observe=False`) NIE MOŻE zmienić żadnej wartości pochodzącej z Execution
Pipeline (World/Brain/Kernel/RNG) — tylko wartości, które są *z definicji*
funkcją snapshotów (Observation Pipeline), a te zmienić się MUSZĄ (bo
wcześniej były zdegenerowane do zera właśnie z braku danych — to jest
cel naprawy, nie regresja).

Metodologia: prototyp `observe: bool` w `run_pattern_echo()`
(`clos_academy/lesson_L1_1.py`), uruchomiony na **dokładnie** tej samej
macierzy co `clos_academy/publish_L1_1.py` (2 genomy × 2 scenariusze ×
10 seedów = 40 runów, `TICKS=200`), z `observe=True` i `observe=False`.
Pola wyniku podzielone rozłącznie na:

- **EXECUTION** (`run_id, lesson, genome, seed, scenario, primary_endpoint,
  mse_stimulus_phase, mse_silence_phase, memory_decay_rate, final_energy,
  final_entropy, memory_size, passed`) — pochodzą wyłącznie z
  `world.step()`/`brain_rt.step()`/`silent_step()`, liczone przed
  jakimkolwiek dostępem do snapshotów.
- **OBSERVATION** (`stability_score, adaptation_tick`) — jawnie
  zdefiniowane jako `f(snapshots)` przez `run_experiment()`/
  `detect_phases()`.

### Wynik (40/40 runów, SHA256 per pole-podzbiór)

```
=== EXECUTION FIELDS === 40/40 identycznych, 0 niezgodności
PASS - Read-Only Observer NIE wpływa na Execution Pipeline.

=== OBSERVATION FIELDS === 40/40 runów ma inne wartości on/off
(oczekiwane: stability_score/adaptation_tick były 0 z braku snapshotów)

Przykład (run 0, L1.1_default_s1_noise_world):
  observe=True:  stability_score=2.4127  adaptation_tick=47
  observe=False: stability_score=0.0     adaptation_tick=0
```

**Wniosek: architektura poprawna wg testu CTO.** Snapshot Engine można
całkowicie usunąć (ustawić `observe=False`) i wszystkie wyniki
Execution Pipeline pozostają bajtowo identyczne. Jedyne pola, które się
zmieniają, są tymi, które CTO explicite oczekuje że się zmienią (Warunek
4, trójstan A/B/C — realizowane w P3).

Skrypt dowodowy: uruchomiony ad-hoc w tej sesji (nie w repo — zostanie
sformalizowany jako `tests/test_observer_removability.py` w P2, razem z
resztą rozszerzonego pakietu regresji, Warunek 3 CTO).

## 4. Zakres tego commitu (P1)

Jedyna zmiana w kodzie: `clos_academy/lesson_L1_1.py` —
`run_pattern_echo()` dostaje parametr `observe: bool = True` i jedno
dodatkowe wywołanie `create_snapshot()` w pętli (patrz §2). Domyślne
zachowanie (`observe=True`) różni się od stanu sprzed P1 tylko w polach
OBSERVATION (co jest zamierzone — to naprawia dokładnie ten sam bug,
który P2/P3 mają domknąć). `lesson_L1_2.py`, Capability Analyzer,
Competency Profile, panel, walidator telemetrii — **nie dotknięte**,
zaplanowane na P2–P5.

## 5. Co NIE jest w zakresie P1

- Rozszerzony pakiet regresji (Warunek 3 CTO) — pełny zestaw testów
  (L1.1 40/40 + golden, L1.2 primary, hash, Capability Analyzer, bundle)
  — P2.
- Wdrożenie w `lesson_L1_2.py` — P2.
- Realne Adaptation/Stability per genom z klasyfikacją A/B/C — P3.
- Walidator telemetrii — P5.

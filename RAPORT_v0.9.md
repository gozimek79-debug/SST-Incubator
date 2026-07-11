# Raport końcowy — Sprint v0.9

Branch: `v0.7.2-scientific-integrity`. Zakres: `55f3e75..HEAD` (11 commitów,
w tym 3 auto-commity CI). Status projektu: **Research Grade Infrastructure
for Artificial Ontogenesis**. Nie "Publication Ready", nie "Production
Ready", i wprost: nie "Artificial Mind" — CLOS bada mierzalną ontogenezę
(rozwój stanu wewnętrznego Brain pod wpływem genomu i środowiska), nie
ogólną inteligencję.

---

## 1. Lista commitów sprintu

| Commit | Priorytet | Opis (jedno zdanie) |
|---|---|---|
| `0a722cf` | P1 | Usunięcie martwego `core/` (5 plików, 0 importów spoza), 263 passed. |
| `31ec282` | P2 | `BrainRuntime.partial_step()` jako addytywne API — tylko `PERCEIVE` certyfikowany, `test_step_regression` na złotych wartościach z commita sprzed tej zmiany. |
| `68e0b07` | P3 | `echo_runtime.py` zrefaktoryzowany na `partial_step()` — L1.1 bajtowo identyczne (40/40 `run_*.json`). |
| `cc84fa1` | P4 | Prerejestracja L1.2 (BRAMKA zatwierdzona) — formalna definicja `recovery_time`, kontrola=wariant B, `pre_shock_band_check` z progiem 0.8, `min_non_censored=5`. |
| `cccd3fd` | P5 | Implementacja L1.2 wg prerejestracji — realne wyniki, dwa odkrycia architektoniczne (Capability Analyzer, walidator cenzurowania). |
| `824416a` | P6 (krok 1) | Raport dla architekta + osobny surowy log (nie duplikat, hashe różne). |
| `a02ac02` | P6 (kroki 2–3) | 14. pojęcie Homeostatic Resilience + Capability Analyzer na relację N:M, 4 pojęcia L1.1 zweryfikowane jako identyczne. |
| `fe91d62` | P6 (kroki 4–5) | Profil minimalny (5/14) oddzielony od pełnego, Panel Badacza — dwie karty. |
| `a41ed18`, `3f8a572`, `a553b6c`, `2c5f70a` | (auto, CI) | `ci: aktualizacja reports/status.json [skip ci]` — automatyczne commity po każdym zielonym przebiegu CI. |

Commit dla P7 (ten priorytet — hipoteza IDIO-MORPH, status, ten raport)
jeszcze nie istnieje w momencie pisania tego pliku.

---

## 2. Status priorytetów

### P1 — Usunięcie długu `core/`
**Zrobione.** 5 plików usuniętych, 0 importów spoza, 263 passed potwierdza brak zależności.

### P2 — `partial_step()` jako Runtime API
**Zrobione.** Addytywne — `step()` ma dokładnie 1 usuniętą linię (import), zero zmian w ciałach istniejących funkcji poznawczych. Tylko `PERCEIVE` certyfikowany; każdy inny krok → `NotImplementedError`. Nowy inwariant projektu (chronimy zachowanie, nie pliki) wprowadzony i przestrzegany od tego commita wzwyż.

### P3 — Refaktor `echo_runtime.py`
**Zrobione.** Regresja krytyczna zweryfikowana na dwóch poziomach: zagregowane statystyki L1.1 identyczne ORAZ wszystkie 40 pojedynczych plików `run_*.json` bajtowo identyczne przed/po.

### P4 — Prerejestracja L1.2 (bramka)
**Zrobione, z trzema rundami rewizji przed zatwierdzeniem** (nie jednorazowo): dodanie `min_non_censored`, jawne uzasadnienie hipotezy o niezdegenerowanych secondary endpoints, dwa warianty kontroli do wyboru (wybrano wariant B), korekta progu `pre_shock_band_check` z 0.5 na 0.8. Proces bramkowy zadziałał zgodnie z zamierzeniem — dokument nie został zaimplementowany, dopóki nie był gotowy.

### P5 — Implementacja L1.2
**Zrobione.** Zobacz sekcję 4 (odkrycia) — wyniki są realne i częściowo nieoczekiwane, zaraportowane bez upiększania.

### P6 — Competency Profile: skalowalność + profil minimalny
**Zrobione, w tym Odkrycie #1 z P5** (Capability Analyzer wymagał refaktoru N:M — nie "wchłonął" L1.2 za darmo, patrz sekcja 4). Profil minimalny (5/14) i pełny (14/14, z jawnymi kategoriami zdegenerowane/insufficient_data) rozdzielone w `.json`/`.md`/Panelu Badacza.

### P7 — IDIO-MORPH + status
**Zrobione.** `docs/idio_morph_hypothesis.md` — cztery kierunki jako pytania badawcze, zero kodu. Nota o zgodności architektonicznej (negatywna — potwierdzenie braku blokady, nie projekt). Status README/ROADMAP zaktualizowany; grep na "Artificial Mind"/"umysł" czysty (tylko negacje).

---

## 3. Wyniki

- **Testy:** `263 → 273 → 277 → 282 passed` w toku sprintu (przyrost widoczny per priorytet w tabeli commitów). `test_step_regression` zielony w każdym commicie po P2 — sprawdzane jawnie, nie tylko przez pełny `pytest -q`.
- **Walidatory:** `validate_publication.py` OK (6 bundli), `validate_artifacts.py` OK (2 raporty, świadomy cenzurowania od P5), `validate_panel.py` OK (zero wklejonych metryk, przetrwał zmiany w `panel.js` z P6).
- **Core:** `clos_brain/brain_runtime.py` jedyny plik Core dotknięty w całym sprincie — czysto addytywnie (86 wstawień, 1 usunięcie — linia importu). Reszta Core (`clos_kernel/`, `genome/`, `birth/`, pozostałe pliki `clos_brain/`) nietknięta.

---

## 4. Trzy odkrycia — jawnie, bez upiększania

### (a) `recovery_time`: `default` ważny, `highly_plastic` w 100% ucenzurowany

| Genom | mean | CI95 | n_eff | ci95_valid | recovery_rate |
|---|---|---|---|---|---|
| `default` | 15.4 | [12.77, 18.03] | 7 | **True** | 10/10 |
| `highly_plastic` | — | — | 0 | **False** | **0/10** |

`highly_plastic` nigdy nie odzyskuje homeostazy w oknie W=150 ticków — nie
raz, nie czasem, **za każdym razem, dla wszystkich 10 seedów**.
Mechanistycznie wytłumaczalne: `decay_rate=0.05` (5× wyższy niż
`default=0.01`) daje 5× silniejszy przyrost entropii na jednostkę błędu
predykcji w `regulate()`, podczas gdy tempo ściągania w dół rośnie tylko o
~19% (`plasticity` 0.95 vs 0.8 → `0.005×plasticity`). To realny wynik
naukowy o konkretnym genomie, nie usterka implementacji — zweryfikowany
przed zaraportowaniem właśnie po to, by odróżnić jedno od drugiego.

### (b) `pre_shock_band_check = 0.0` → endpoint przemianowany na `arrival`, nie `recovery`

Dla **obu** genomów `pre_shock_in_band_fraction = 0.0` (próg
rozstrzygający: 0.8, poniżej niego = ustanowienie, nie powrót). Brain
nigdy nie zdążył osiągnąć pasma homeostazy przed szokiem — perturbacja
następuje zbyt wcześnie po "narodzinach". Reguła z prerejestracji
zadziałała dokładnie tak, jak zaprojektowano: **decyzja podjęta z danych**,
nie z góry. Hipoteza w raporcie L1.2 skorygowana z "Brain odzyskuje
homeostazę" na "Brain **osiąga/ustanawia** homeostazę po szoku" — jawnie,
nie po cichu. `mixed_case=False` (oba genomy po tej samej stronie progu).

### (c) Adaptation/Stability zdegenerowane **u źródła** — znany dług, NIE naprawiony w v0.9

W P4 prerejestracja L1.2 zakładała (błędnie), że seed-zależny
`shock_tick`/`shock_magnitude` da realną wariancję międzyseedową dla
`adaptation_tick`/`stability_score`. **Nie dało** — i przyczyna okazała
się głębsza niż wrażliwość metryki na scenariusz:
`kernel.snapshot_engine.get_all_snapshots()` zwraca **0 snapshotów** w
obu lekcjach (L1.1 i L1.2), bo pętla lekcji woła `world.step()` +
`brain_rt.step()` bezpośrednio, nigdy `kernel.run_tick()` — jedyną
metodę Kernela faktycznie tworzącą snapshot. `detect_phases()`/
`stability_index()` przy pustej liście snapshotów degenerują trywialnie
do zera z definicji, niezależnie od scenariusza świata.

**To NIE jest nowe odkrycie tego sprintu** — ten sam mechanizm degeneracji
już wystąpił w L1.1 i był udokumentowany w `RAPORT_KONCOWY_v0.8.4.md` jako
"Capability Analyzer nie skaluje się" (niewłaściwie zdiagnozowane wtedy
jako problem skalowania metryki, nie pustych snapshotów). L1.2 tylko
ujawnił prawdziwą przyczynę, dzięki próbie zweryfikowania hipotezy o
wariancji, która nie potwierdziła się.

**Świadomie NIE naprawione w tym sprincie** — poprawka wymagałaby albo
zmiany pętli lekcji (by wołać `kernel.run_tick()`), albo `detect_phases()`/
`stability_index()`, żeby działały bez Kernela — żadne z nich nie było w
zakresie P1–P7. Zostaje jako udokumentowany dług dla przyszłego sprintu.

### Dodatkowo: Capability Analyzer wymagał refaktoru, nie "wchłonął" L1.2 za darmo

Skalowalność architektury **nie była potwierdzona automatycznie** —
`CONCEPT_METRIC_MAP` (jeden lesson_id na pojęcie) faktycznie zignorował
L1.2 przy pierwszym uruchomieniu (P5, Odkrycie #1). Wymagało to
świadomego refaktoru na relację N:M (P6, Krok 3) z decyzją CTO. Bez tego
refaktoru "Homeostatic Resilience" nigdy nie pojawiłoby się w profilu
kompetencji, mimo że lekcja L1.2 i jej dane istniały.

---

## 5. Uczciwa ocena gotowości

**Zrobione i zweryfikowane:**
- Nowy inwariant (zachowanie, nie pliki) przestrzegany w każdym commicie po P2 — nie tylko zadeklarowany, ale mierzony (`test_step_regression`).
- Proces bramkowy prerejestracji L1.2 faktycznie wpłynął na wynik (trzy rundy rewizji, próg pre_shock_band_check zmieniony z 0.5 na 0.8 na żądanie, przed jakąkolwiek implementacją).
- Oba architektoniczne odkrycia (Capability Analyzer N:M, walidator świadomy cenzurowania) rozwiązane, nie zamiecione.

**NIE zrobione / ograniczenia:**
- **Profil minimalny to 5/14, nie 14/14.** Adaptation i Stability pozostają zdegenerowane u źródła (puste snapshoty) — nie jest to kwestia braku lekcji, tylko infrastrukturalna usterka we WSZYSTKICH dotychczasowych lekcjach.
- **`highly_plastic` nie ma zmierzonego `recovery_time`** — 100% cenzury. Homeostatic Resilience w profilu minimalnym istnieje tylko dla jednego genomu.
- **Cohen's d między genomami dla recovery_time jest nieobliczalny** (jedna grupa pusta) — porównanie genomowe dla nowego pojęcia nie istnieje.
- **IDIO-MORPH to wyłącznie hipoteza.** Zero kodu, zero planu implementacji, zero priorytetyzacji czterech kierunków.
- **Dwie lekcje.** Cała warstwa Academy nadal zweryfikowana tylko na L1.1+L1.2 — Capability Analyzer N:M nie był testowany na trzeciej, strukturalnie innej lekcji.

## 6. Status projektu

**Research Grade Infrastructure for Artificial Ontogenesis.**

Infrastruktura integralności (regresja zachowania, prerejestracja jako
bramka, walidatory świadome niuansów typu cenzurowania, panel czytający
dane na żywo) jest solidna i rozszerzona w tym sprincie o nowy typ
niezmienności (zachowanie, nie pliki). Zawartość naukowa pozostaje wąska
i jest tym razem jeszcze bardziej precyzyjnie zmapowana: 5 z 14 pojęć z
wiarygodnym CI95, jeden dobrze wytłumaczony przypadek 100%-owej cenzury,
jeden znany, nienaprawiony dług źródłowy (puste snapshoty). To jest
zamierzone i jawne, nie przeoczenie.

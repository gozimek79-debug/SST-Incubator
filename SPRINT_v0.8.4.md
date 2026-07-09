# SPRINT v0.8.4 — Integralność infrastruktury (brief dla Claude Code)

To jest wykonywalna specyfikacja sprintu. Zrealizuj ją w tym repo, na gałęzi
`v0.7.2-scientific-integrity`. Po każdym priorytecie uruchom testy; na końcu
zrób jeden push i potwierdź stan zdalny.

---

## ZASADY NADRZĘDNE (nie łam)

1. **CORE FROZEN.** Nie modyfikuj logiki poznawczej Brain Runtime
   (`clos_brain/runtime/*`, `clos_brain/tissue.py`, `clos_kernel/*`, `genome/*`,
   `birth/*`). Zmiany tylko w: `clos_academy/`, `clos_scientist/`,
   `clos_curriculum/`, `clos_studio/`, CI, dokumentacji, testach.
   Jedyny dozwolony dotyk Core to naprawy kompilacji (jak istniejący import
   `List` w `kernel.py`) — nie zmiany zachowania.
2. **Weryfikacja, nie deklaracja.** Po każdej zmianie uruchom `pytest -q`.
   Liczba w komunikacie commita musi odpowiadać realnemu wynikowi.
3. **Artefakt = kod.** Żaden opublikowany raport nie może pokazywać wyniku,
   którego bieżący kod już nie produkuje.
4. **Bez przeceniania.** Status projektu = „Research Grade Infrastructure".
   Nie używaj „Publication Ready" ani „Production Ready".
5. **Nowy standard lekcji** (obowiązuje od teraz): każda lekcja Academy definiuje
   (a) hipotezę poznawczą, (b) mierzalny mechanizm, (c) kryterium matematyczne,
   (d) możliwość niezależnej replikacji. Projektujemy dowód mechanizmu, nie
   zaliczenie testu.

Zakazane w tym sprincie: odblokowanie Core, Predictive Coding, Latent Space,
nowe neurony/geny, zmiany architektury Brain.

---

## DECYZJA PROJEKTOWA (już podjęta przez CTO)

**L1.1 → `noise_world`.** `stable_world` pozostaje jako **benchmark kontrolny**
(punkt odniesienia), ale prerejestracja i kod eksperymentu L1.1 opisują
`noise_world`. Powód: L1.1 ma dowodzić powstania wewnętrznej reprezentacji,
odpornej na zakłócenia — nie odtwarzania idealnego sygnału. Środowiskowa
wariancja daje poprawną podstawę CI95/effect size.

Skutek: usuń z lekcji szum prezentacji dodany w v0.8.3 (`gaussian_noise` na
sygnale stable) — wariancja ma pochodzić ze świata `noise_world`, nie z hacka
na kontroli. Zachowaj `stable_world` jako osobny przebieg kontrolny w raporcie
(baseline), do którego liczymy Glass's delta.

---

## PRIORYTET 1 — Integralność naukowa i prowenancja

- Zregeneruj **wszystkie raporty Academy** z bieżącego kodu (obecnie: L1.1).
- Zregeneruj Publication Bundle dla L1.1.
- Wymuś w każdym manifeście/metadanych zapis: `git_commit` (z `git rev-parse
  HEAD`), `config_hash`, `manifest_hash`, `timestamp`, `experiment_id`.
- **Legacy:** starych bundli sprzed prowenancji (EXP-* z v0.4–v0.7) NIE
  fabrykuj — oznacz je polem `provenance: "legacy-pre-0.7.2"`. Nie zgaduj commita.
- Kryterium akceptacji: uruchomienie walidatora artefaktów (P3) na `reports/`
  i `publications/` nie zgłasza rozjazdu kod↔artefakt.

## PRIORYTET 2 — Prerejestracja L1.1 (spójność z kodem)

- Napisz nową `publications/preregistration_L1_1.json` opisującą **dokładnie**
  eksperyment na `noise_world`:
  hipoteza, primary endpoint (`mse_after_stimulus_removal` @ tick 50),
  secondary endpoints, PASS/FAIL, `scenario: noise_world`,
  `control_baseline: stable_world`, min. liczba seedów ≥ 10, plan statystyczny
  (CI95 + Glass's delta vs kontrola).
- Kod lekcji i prerejestracja muszą opisywać ten sam eksperyment (zweryfikuj
  programowo, jeśli się da).
- Zachowaj poprzednią wersję jako `preregistration_L1_1_v0.8.json` (historia).

## PRIORYTET 3 — Automatyzacja jakości (CI)

- Dodaj `.github/workflows/ci.yml` uruchamiany na push i pull_request:
  instalacja zależności, `pytest -q`, testy ważności naukowej.
- Dodaj skrypty walidacyjne (uruchamiane też lokalnie i w CI):
  - `scripts/validate_publication.py` — każdy bundle ma komplet prowenancji.
  - `scripts/validate_artifacts.py` — raporty nie zawierają metryk nieważnych
    tam, gdzie powinna być wariancja (np. `ci95_valid=False` przy scenariuszu
    stochastycznym = błąd); artefakt zgadza się z definicją eksperymentu.
- Kryterium: repo samo potwierdza poprawność (zielony workflow).

## PRIORYTET 4 — Cognitive Academy (domknięcie v0.8)

- `clos_academy/cognitive_ontology.md` — jedna obowiązująca definicja pojęć
  (Perception, Attention, Pattern Recognition/Retention, Working/Long-term
  Memory, Prediction, Adaptation, Exploration, Generalization, Planning,
  Stability, Energy Efficiency). Każda przyszła metryka odnosi się do tych definicji.
- `clos_scientist/capability_analyzer.py` — Capability Analyzer: czyta `reports/`,
  `events.jsonl`, telemetrię; buduje profil; porównuje genomy.
- Competency Profile (`competency_profile.json` + `.md`) + auto-karty genomów.
  **Ograniczenie uczciwości:** każda oś wynika WYŁĄCZNIE z mierzalnej metryki
  konkretnej lekcji. Istnieje jedna lekcja (L1.1 → Working Memory). Osie bez
  lekcji MUSZĄ być oznaczone `status: "insufficient_data"` — bez zgadywania,
  bez „wykresu marketingowego". Profil ma pokazywać luki, nie je ukrywać.

## PRIORYTET 5 — Dokumentacja

- Zaktualizuj/utwórz `README.md`: czym jest CLOS, status
  **„Research Grade Infrastructure"** (usuń „Publication Ready"/„Production
  Ready" wszędzie), jak uruchomić testy, struktura.
- `ROADMAP.md`: v0.8.4 (ten sprint) → v0.9 (Predictive Coding, Latent Space).
- Zsynchronizuj prerejestracje i Publication Bundle z powyższym.

## PRIORYTET 6 — Specyfikacja pod v0.9 (TYLKO dokument)

- `docs/spec_partial_step.md` — pełna specyfikacja `BrainRuntime.partial_step()`:
  motywacja (lekcje wymagające pominięcia kroków pipeline bez łamania Core
  Frozen — patrz `clos_academy/echo_runtime.py` jako obecny obejście), proponowany
  interfejs (które kroki można pominąć/wykonać), kontrakt, wpływ na determinizm,
  plan testów. **Nie implementuj** — sama specyfikacja. Nie dotykaj Brain Runtime.

---

## PRODUKT KOŃCOWY (deliverables)

Zregenerowane raporty Academy; zaktualizowany Publication Bundle z pełną
prowenancją; działający CI (zielony); `cognitive_ontology.md`; Capability
Analyzer; Competency Profiles (z jawnymi lukami); nowa prerejestracja L1.1
(noise_world); specyfikacja `partial_step()`; oraz `RAPORT_KONCOWY_v0.8.4.md`
z listą wszystkich zmian i uczciwą oceną gotowości.

## DYSCYPLINA GITA

- Jeden logiczny commit na priorytet (czytelne komunikaty, liczba testów = realna).
- `pytest -q` musi być zielony przed każdym commitem.
- Na końcu: `git push origin v0.7.2-scientific-integrity`, potem `git status`
  ma pokazać „up to date with origin". Nie zostawiaj niewypchniętych commitów.
- Nie commituj śmieci ze `storage/` (jest `.gitignore`).

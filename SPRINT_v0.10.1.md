# SPRINT v0.10.1 — Infrastructure Validation [wg dyrektywy CTO]

Gałąź: `v0.7.2-scientific-integrity`. Priorytet → testy → commit → push → audyt.
Status: **Research Grade Infrastructure for Artificial Ontogenesis.**

Cel (CTO): nie zwiększamy inteligencji — zwiększamy WIARYGODNOŚĆ. Walidujemy
laboratorium przed v0.11. Zero nowych zdolności poznawczych.

---

## ZASADA NADRZEDNA SPRINTU WALIDACYJNEGO

> **Celem jest ZNALEŹĆ, gdzie infrastruktura pęka — nie potwierdzić, że działa.**

Macierz odporności z samymi ✔ jest bezwartościowa. ✘ jest WYNIKIEM, nie porażką.
Każdy raport ma prawo (i obowiązek) wskazać granicę, degenerację lub warunek,
w którym metryka zawodzi. Sprint „ładnych tabelek" = sprint nieudany.

Inwariant v0.10 obowiązuje: **Execution niezmienione, Observation usuwalna.**
Nowy kod (środowiska, populacja) NIE może zmienić L1.1/L1.2 (regresja bajtowa)
ani złamać usuwalności obserwatora.

Zakazane: Predictive Coding, Latent Space, IDIO-MORPH jako kod, nowe mechanizmy
poznawcze, zmiana istniejącej logiki poznawczej.

---

## P1 — Prerejestracja walidacji populacyjnej (BRAMKA, przed uruchomieniem)

To Zadanie 1 CTO, ale z bramką metrologiczną — bez niej 100 genomów to 100×
pseudonauki.
- `publications/preregistration_v0_10_1_population.json`: definicja populacji
  (ile genomów, jakie parametry: decay_rate, learning_rate, retention, noise,
  plasticity — zakresy i próbkowanie), środowiska, seedy.
- **Metrologia (wymóg — bez tego STOP):**
  - MINIMALNA liczba seedów/genom dla ważnego CI95 (uzasadniona, nie na sztywno),
  - korekta na WIELOKROTNE PORÓWNANIA (przy N genomach część „istotnych" różnic
    będzie przypadkowa — Bonferroni/FDR, zadeklaruj którą i dlaczego),
  - z góry: co znaczy „metryka odporna na zmianę genomu" (próg ilościowy).
- Cel jawnie NIE „ładne wyniki", lecz mapa przestrzeni zachowań (dyrektywa CTO).
- Pokaż mi prerejestrację. NIE uruchamiaj populacji, dopóki nie zatwierdzę bramki.

## P2 — Środowiska testowe (Zadanie 2) — pod inwariantem v0.10

- Dodaj zestaw prostych środowisk różniących się: poziom szumu, częstotliwość
  zakłóceń, siła perturbacji, długość stabilnych okresów, przewidywalność.
- **Każde nowe środowisko przechodzi:** (a) regresja — L1.1/L1.2 bajtowo
  niezmienione; (b) test usuwalności — Snapshot Engine usuwalny także na nowym
  środowisku; (c) walidator telemetrii zielony.
- Cel: znaleźć GRANICE działania infrastruktury — gdzie metryki się sypią.

## P3 — Uruchomienie walidacji populacyjnej (po bramce P1)

- Uruchom populację × środowiska × seedy wg prerejestracji.
- Raportuj przestrzeń zachowań: rozkłady metryk, gdzie CI95 ważne, gdzie
  degeneracja, gdzie cenzura. Bez upiększania — degeneracje to dane.
- Pełna prowenancja; artefakty w `reports/`/`publications/`.

## P4 — Validity Report per metryka (Zadanie 3)

- **Nie zaczynaj od zera** — skonsoliduj znane ograniczenia i rozszerz:
  * `recovery_time`→`time_to_sustained_band` (arrival vs return, v0.9),
  * `adaptation_tick` mierzy okno PRZED szokiem w L1.2 (v0.10),
  * duże Cohen's d z małej wariancji ≠ duży efekt praktyczny (v0.10),
  * empty-snapshot degeneracja (naprawiona v0.10) — jako historia.
- Dla KAŻDEJ z 14 osi sekcja: co mierzy / czego NIE mierzy / kiedy zdegenerowana
  / kiedy myląca / kiedy wymaga innej interpretacji. NIE poprawiaj metryk — poznaj granice.

## P5 — Macierz odporności (Zadanie 4)

- Tabela: każda metryka × {genom, środowisko, seed, obserwacja, refaktoryzacja}.
- ✔/✘ MUSI wynikać z danych P2/P3, nie z założenia. ✘ jest oczekiwane i cenne.
- Dokument dla przyszłych autorów eksperymentów: kiedy metryce można ufać, kiedy nie.

## P6 — Procedura replikacji + test empiryczny (Zadanie 5)

- `docs/REPLICATION.md`: krok-po-kroku odtworzenie GŁÓWNYCH wyników wyłącznie
  z repo (clone → env → run → oczekiwane liczby z tolerancją).
- **Test empiryczny (nie „na wiarę"):** procedura musi być na tyle samowystarczalna,
  by osoba z samym repo + instrukcją doszła do 0.156712 / 0.173229 / 15.4 bez
  dostępu do historii projektu. Wypisz brakujące elementy, jeśli są.
  (Audytor zweryfikuje to niezależnie: klon + sama instrukcja → czy dochodzę do liczb.)

## P7 — Current Scientific Limits + Research Readiness Report (Zadania 6-7)

- `docs/CURRENT_SCIENTIFIC_LIMITS.md`: czego NIE wolno twierdzić (nie AGI, nie
  uniwersalna inteligencja, nie ogólna teoria ontogenezy; wyniki są O MODELU,
  nie o poznaniu w ogóle — parametry genomów były USTAWIONE, nie odkryte).
- `RESEARCH_READINESS_REPORT.md`: mocne strony, ograniczenia, otwarte pytania,
  rekomendacje przed preprintem. Odpowiedź na jedno pytanie: czy można rozpocząć
  proces publikacyjny? Uczciwie — także jeśli odpowiedź brzmi „jeszcze nie, bo X".

---

## KRYTERIA ZAKOŃCZENIA (CTO)
Brak regresji wszystkich eksperymentów · walidacja na populacji genomów ·
walidacja na wielu środowiskach · udokumentowane ograniczenia każdej metryki ·
procedura pełnej replikacji (zweryfikowana empirycznie) · opisane granice
interpretacji · Research Readiness Report · `test_step_regression` zielony ·
4 walidatory zielone · CI zielony.

## DYSCYPLINA GITA
Jeden logiczny commit na priorytet; **jawna lista plików (nie `git add -A`) i
`git status --short` PRZED commitem** (nawyk do przywrócenia); regresja +
walidatory zielone przed commitem; komunikat = realny stan. Push + audyt.
Nie commituj `.claude/` ani śmieci.

# Energy Efficiency: decyzja ontologiczna (do CTO, osobno od MSE/MAE)

> **Status: ZDECYDOWANE I ZREALIZOWANE — Opcja 1, decyzja CTO 2026-07-17.**
> To pytanie było ONTOLOGICZNE (czy pojęcie w tej formie powinno istnieć w
> profilu kompetencji), nie nazewnicze — inne od
> `docs/MSE_MAE_NAMING_DECISION.md` mimo wspólnego pochodzenia (audyt
> formalnych definicji, SPRINT_v0.11.0.md P1). Dotyka **profilu minimalnego**
> (1 z 7 osi). CTO wybrał **Opcję 1 z zastrzeżeniem audytora**: rename na
> "Final Energy Level" (NIE "Metabolic Cost" — patrz uzasadnienie w opisie
> Opcji 1 poniżej, zapisane też w `clos_academy/cognitive_ontology.md` i
> `docs/VALIDITY_REPORT.md`). Profil minimalny jest teraz jawnie oznaczony
> jako **6 osi poznawczych + 1 zmienna stanu fizjologicznego**
> (`clos_scientist/capability_analyzer.py:CONCEPT_KIND`,
> `publications/competency_profile.json:minimal_profile.cognitive_axes` vs
> `.physiological_state_variables`). §1-4 poniżej to oryginalna analiza trzech
> opcji, zachowana jako zapis procesu decyzyjnego.

## Ustalenia (potwierdzone w kodzie, nie interpretacja)

- **Formuła:** `clos_academy/lesson_L1_1.py` linia 119 / `lesson_L1_2.py`
  linia 199: `"final_energy": round(tissue.energy, 6)` — surowa wartość
  stanu `tissue.energy` w OSTATNIM ticku przebiegu.
- **W kodzie NIE ISTNIEJE żadna formuła efektywności** — brak stosunku,
  brak dzielenia przez cokolwiek, brak porównania nakład/efekt. To nie jest
  przybliżenie efektywności ani jej proxy — to inna kategoria wielkości
  (poziom stanu, nie stosunek).
- **Nie ma czego dzielić przez energię, bo `act()` jest echem** — system w
  obecnej architekturze nie ma WYJŚCIA (output) w sensie wymaganym do
  policzenia efektywności (efekt/koszt). Bez mechanizmu produkującego
  mierzalny efekt, "efektywność" nie ma operacyjnej definicji do policzenia
  — to nie brak implementacji szczegółu, to brak przedmiotu pomiaru.
- **Konsekwencja wprost:** genom, który NIC NIE ROBI (minimalna aktywność,
  energia nie spada) miałby NAJWYŻSZĄ "efektywność" wg obecnej metryki — bo
  metryka nagradza wysoki POZIOM energii na końcu, nie stosunek
  efekt/nakład. To odwraca intuicyjny sens słowa "efektywność".
- **Różnica względem MSE/MAE:** MSE/MAE to był błąd NAZWY — zła operacja
  statystyczna (kwadrat vs abs) na WŁAŚCIWEJ kategorii wielkości (błąd
  predykcji). Tu formuła mierzy poprawnie coś realnego (poziom energii), ale
  to NIE JEST kategoria, którą nazwa obiecuje (stosunek/efektywność) — błąd
  KATEGORII, nie operacji. Nie da się tego naprawić samym rename (nie ma
  krótszej, poprawnej nazwy czekającej — "Final Energy Level" opisuje co
  innego niż "efektywność").
- **Miejsce w architekturze:** oś jest w **profilu minimalnym** (1 z 7 —
  `publications/competency_profile.json`, `minimal_profile.axes`) — jedyna z
  7 zmierzonych osi obecnie oznaczonych jako "oficjalne, wiarygodne CI95".

## Trzy opcje (przedstawione, NIE wybrane)

### Opcja 1 — Przemianuj na "Metabolic Cost" / "Final Energy Level"

**Co się zmienia:** nazwa pojęcia w `cognitive_ontology.md`,
`capability_analyzer.py` (`CONCEPT_METRIC_MAP` label), `population_validation.py`,
panel, dokumentacja. Formuła (`final_energy`) bez zmian.

**Koszt:** podobny zasięg do MSE/MAE Wariantu (c) — kilka plików kodu +
testy golden-field + dokumentacja. Nie dotyka zamrożonych prerejestracji w
sposób odmienny niż tam.

**Ryzyko:** uczciwe wobec formuły, ALE — jak zauważa audytor — **to
przestaje być pojęcie POZNAWCZE, staje się zmienną stanu**. "Metabolic Cost"/
"Final Energy Level" nie twierdzi nic o zdolności systemu do robienia
czegokolwiek efektywnie — to opis stanu fizjologicznego, nie kompetencji.
Pytanie do CTO: czy zmienna stanu ma w ogóle sens jako "oś kompetencji
poznawczej" obok Working Memory/Adaptation/etc., nawet pod uczciwą nazwą?

**Co widzi recenzent:** nazwa zgodna z pomiarem — ale profil kompetencji
zawiera 1 oś, która jawnie NIE jest kompetencją poznawczą, tylko telemetrią
stanu. Wymaga wytłumaczenia, dlaczego zmienna stanu jest w tej samej tabeli
co zdolności poznawcze.

### Opcja 2 — Usuń z ontologii do czasu, aż `act()` będzie coś produkować

**Co się zmienia:** "Energy Efficiency" znika z `CONCEPT_METRIC_MAP`
(`capability_analyzer.py`), z profilu minimalnego i pełnego, z
`population_validation.py` (`L1_1_METRICS`/`L1_2_METRICS`), z panelu. Dane
historyczne (`final_energy` w raportach) NIE są usuwane z surowych
artefaktów — tylko przestają być prezentowane jako "oś kompetencji".

**Koszt:** większy niż Opcja 1 — usunięcie z profilu minimalnego zmienia
**7 osi na 6** (widoczne w `RESEARCH_READINESS_REPORT.md`,
`docs/ROBUSTNESS_MATRIX.md`, wszędzie gdzie liczba "7 zmierzonych osi" jest
cytowana — wymaga przeglądu tych wszystkich miejsc, nie tylko
`capability_analyzer.py`).

**Ryzyko:** traci się dane, które SĄ realne i deterministycznie mierzalne
(`final_energy` GENOME-ROBUST w kilku kontekstach, patrz macierz P3) — nawet
jeśli nie mierzą "efektywności", mierzą coś (poziom energii końcowej), co
może być użyteczne pod inną, mniej ambitną etykietą (patrz Opcja 1) zamiast
całkowitego usunięcia. Usunięcie jest nieodwracalne bez ponownej
"dyskusji o dodaniu" w przyszłości — inny próg niż rename.

**Co widzi recenzent:** profil 6 osi zamiast 7 — najbardziej defensywna
opcja (nic nieprawdziwego w profilu), ale wymaga jasnego zapisu W CHANGELOG,
dlaczego liczba osi się zmieniła (żeby nie wyglądało na "chowanie"
niewygodnego wyniku, zwłaszcza że ta oś akurat była GENOME-ROBUST w kilku
kontekstach, nie fragile).

### Opcja 3 — Zdefiniuj prawdziwą efektywność (wymaga mechanizmu wyjścia)

**Co się zmienia:** NIC od razu w profilu/nazwach — to opcja "poczekaj i
zbuduj właściwy pomiar", nie zmiana obecnego stanu. Wymagałoby: (a)
mechanizmu, w którym `act()` faktycznie coś produkuje/wpływa na świat
(zmiana Execution, prawdopodobnie dotyka `clos_brain`/`clos_kernel` — a
więc **potencjalnie Core**, co ten sprint (v0.11.0 KPI: laboratorium, nie
system poznawczy) wprost zabrania jako "nowa zdolność poznawcza"), (b) nowej
formuły efekt/koszt.

**Koszt:** największy, nieznany dopóki mechanizm wyjścia nie istnieje — to
nie jest zadanie na ten sprint, to osobny projekt.

**Ryzyko:** wprost koliduje z zasadą nadrzędną tego sprintu ("zero nowych
zdolności poznawczych jako kod") — budowa mechanizmu wyjścia PO TO, żeby
Energy Efficiency miała sens, byłaby dokładnie odwrotnością KPI v0.11.0.
Realistycznie: opcja na PRZYSZŁY sprint z innym KPI, nie na teraz.

**Co widzi recenzent:** do czasu realizacji tej opcji — status quo (błąd
kategorii, nienazwany) ALBO Opcja 1/2 jako stan przejściowy. Sama Opcja 3
nie jest czymś, co można "zrobić teraz" bez naruszenia zakresu sprintu.

## Rekomendacja audytora (do wyboru opcji) — brak; zastrzeżenie do nazwy — jest

Do wyboru MIĘDZY Opcją 1/2/3: brak — audytor przedstawił trzy opcje bez
wskazania preferowanej, prosząc wprost o rozstrzygnięcie na poziomie CTO.

Do KONKRETNEJ NAZWY w ramach Opcji 1 (już wybranej przez CTO): audytor
zgłosił jedno, konkretne zastrzeżenie — "Metabolic Cost" byłoby błędem
ODWRÓCENIA. `final_energy` mierzy ile energii ZOSTAŁO, nie ile wydano:
`default=0.4608` (więcej zostało → NIŻSZY koszt), `highly_plastic=0.4138`
(mniej zostało → WYŻSZY koszt). Metryka nazwana "Metabolic Cost" byłaby
ODWROTNIE skorelowana z kosztem — powtórzylibyśmy dzisiejszy błąd (MSE/MAE).
Poprawny "Metabolic Cost" = `initial_energy - final_energy` → ZMIENIA
WARTOŚĆ → łamie bramkę regresji. **Użyto "Final Energy Level"** — dosłownie
to, co pole mierzy, zero interpretacji kierunku. Uzasadnienie zapisane w
`clos_academy/cognitive_ontology.md` i `docs/VALIDITY_REPORT.md`, żeby za
rok nikt nie "poprawił" nazwy z powrotem na "Metabolic Cost" bez ponownego
przeliczenia formuły.

## Decyzja i implementacja (2026-07-17)

- **CTO wybrał Opcję 1** (rename), z zastrzeżeniem audytora do samej nazwy
  (patrz wyżej) — "Final Energy Level", nie "Metabolic Cost".
- Formuła `final_energy` **nie została zmieniona** — wartości
  0.460800 (default) / 0.413800 (highly_plastic) identyczne przed i po,
  zweryfikowane bezpośrednio z `run_pattern_echo()` po renamie.
- Zmienione: `clos_academy/cognitive_ontology.md`, `clos_scientist/capability_analyzer.py`
  (`CONCEPT_METRIC_MAP` + nowy `CONCEPT_KIND` — jawny podział
  cognitive/physiological_state), `clos_academy/population_validation.py`,
  `publications/competency_profile.json`/`.md` (regenerowane — nowe pola
  `minimal_profile.cognitive_axes`/`.physiological_state_variables`),
  `docs/VALIDITY_REPORT.md`. `panel.js` renderuje pojęcia generycznie z
  `c.concept` — brak literału "Energy Efficiency" do zmiany, automatycznie
  pokaże nową nazwę.
- Testy zaktualizowane: `tests/test_capability_analyzer.py` (2 miejsca).
  Opcje 2 i 3 pozostają NIE zaimplementowane (odrzucone/odłożone przez wybór
  Opcji 1).

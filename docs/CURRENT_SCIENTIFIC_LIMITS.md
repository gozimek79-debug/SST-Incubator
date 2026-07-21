# Current Scientific Limits — czego NIE wolno twierdzić

> **⚠ STATUS DANYCH: Exploratory Dataset v0.10 (SPRINT_v0.11.0.md).**
> Ograniczenia opisane ponizej (w tym §3, Working Memory) opieraja sie na
> populacji n=10/genom, ktorej analiza mocy (v0.11.0 P0) wykazala bardzo
> niska moc statystyczna. **Ten dokument NIE jest poprawiany ani wycofywany**
> — zakazy sformulowane ponizej pozostaja w mocy (a w niektorych przypadkach
> sa TERAZ jeszcze lepiej uzasadnione, patrz §3 zaktualizowane w duchu P0:
> "nie wykryto" != "nie ma"). Status **Power/Confirmatory validity: PENDING**
> do czasu re-run zatwierdzonego przez CTO (Wariant A/B/C — decyzja w toku).

> **AKTUALIZACJA 2026-07-21 — re-run konfirmacyjny (n=185) zamknięty
> 2026-07-20: zakaz §3 dla Working Memory i Pattern Recognition jest
> UNIEWAŻNIONY (nie tylko częściowo — patrz KOREKTA w §3, poprzednia wersja
> tej adnotacji była błędna).** Working Memory (p=8.1e-17, 69/253 par po
> FDR) i Pattern Recognition (p=4.5e-14, 77/253 par po FDR) mają status
> **VALIDATED** (`docs/METRIC_STATUS_TABLE.md` §4b, footnote¹⁰ + ¹⁵) —
> potwierdzone DWOMA niezależnymi testami (parowy i omnibusowy), nie tylko
> omnibusowo. Pattern Retention **EXPERIMENTAL** (p=0.0254, Red Team,
> 0/253 parowo — jedyna z trzech, gdzie sygnał jest wyłącznie omnibusowy).
> Ten dokument NIE jest edytowany w miejscu (§3 poniżej zostaje jako zapis
> historyczny etapu n=10) — pełne rozróżnienie co dokładnie zostało
> unieważnione, a co nie, jest w §3 poniżej i w `docs/VALIDITY_REPORT.md`
> (sekcja "AKTUALIZACJA 2026-07-21").

**Status: SPRINT_v0.10.1.md P7, Zadanie 6 CTO.** Ten dokument jest
lustrzanym odbiciem `docs/VALIDITY_REPORT.md` (który mówi: kiedy ufać
liczbie) i `docs/ROBUSTNESS_MATRIX.md` (który mówi: kiedy metryka
dyskryminuje) — tu chodzi o **granice interpretacji na poziomie całego
projektu**, nie pojedynczej osi. Adresat: ktokolwiek pisze o CLOS na
zewnątrz (preprint, prezentacja, rozmowa z recenzentem) — te ograniczenia
muszą być znane PRZED sformułowaniem jakiegokolwiek twierdzenia.

---

## 1. Nie AGI, nie uniwersalna inteligencja, nie ogólna teoria ontogenezy

CLOS bada **mierzalną ontogenezę** — rozwój stanu wewnętrznego jednego,
konkretnego modelu (`BrainTissue`, ~10 pól liczbowych) pod wpływem genomu i
środowiska. To NIE jest:

- **Nie AGI.** Zero planowania wieloetapowego, zero reprezentacji celów,
  zero transferu między zadaniami (`Planning`/`Generalization`/`Exploration`
  w `cognitive_ontology.md` są explicite `not yet measured` — nie
  "słabo zmierzone", tylko nieobecne).
- **Nie uniwersalna inteligencja.** Dwie lekcje (L1.1, L1.2) mierzą dwa
  bardzo wąskie zjawiska (odtwarzanie wzorca z pamięci po usunięciu bodźca;
  powrót/ustanowienie entropii w paśmie po pojedynczej perturbacji). Wynik
  na tych dwóch zadaniach nie uogólnia się na "inteligencję" w żadnym
  szerszym sensie.
- **Nie ogólna teoria ontogenezy.** Jeden model (`BrainTissue` + 7 funkcji
  `clos_brain/runtime/`), jeden schemat genomu (5-8 genów), jeden rodzaj
  środowiska (skalarny sygnał `[0,1]` per tick). Wyniki nie mówią nic o
  ontogenezie w systemach biologicznych, sieciach neuronowych głębokiego
  uczenia, czy jakimkolwiek innym substracie.

## 2. Wyniki są O MODELU, nie o poznaniu w ogóle

**Parametry genomów były USTAWIONE przez autorów, nie odkryte.** To
rozróżnienie jest fundamentalne dla poprawnej interpretacji populacji 23
genomów (v0.10.1 P3):

- Zakresy `plasticity∈[0.1,1.0]`, `learning_rate∈[0.01,1.0]`,
  `decay_rate∈[0.001,0.1]`, `homeostasis_target∈[0,1]`,
  `memory_capacity∈[10,1000]` pochodzą z `genome/presets.py`
  (`Gene.min_value`/`max_value`) — **wybrane przez autora kodu przy
  projektowaniu genomu**, nie zmierzone empirycznie ani wyprowadzone z
  jakiejkolwiek teorii biologicznej czy poznawczej.
- Przykład z `RAPORT_v0.9.md`: genom `highly_plastic` ma `decay_rate=0.05`
  (5× wyższy niż `default=0.01`) **ponieważ ktoś tak zaprojektował ten
  preset**, żeby przetestować hipotezę "wyższy decay_rate → gorsza
  retencja pamięci". Gdy eksperyment pokazuje, że `highly_plastic`
  faktycznie ma 100% cenzurowany `recovery_time` — **to jest
  potwierdzenie hipotezy konstrukcyjnej** ("zaprojektowałem genom tak, żeby
  się gorzej regulował, i rzeczywiście się gorzej reguluje"), **nie
  odkrycie** ("odkryliśmy, że wysoki decay_rate powoduje słabą regulację
  homeostazy" w jakimkolwiek sensie wykraczającym poza ten konkretny kod).
- To samo dotyczy 20 genomów LHS z v0.10.1: są próbką z **zadeklarowanego,
  arbitralnie wybranego pudełka parametrów**, nie próbką z "przestrzeni
  wszystkich możliwych genomów" w jakimkolwiek biologicznie/teoretycznie
  uzasadnionym sensie. Wniosek "35-43% populacji ma zdegenerowany
  `adaptation_tick`" jest prawdziwy DLA TEGO PUDEŁKA, nie jest
  stwierdzeniem o częstości występowania jakiejś cechy "w naturze" czy
  nawet "w przestrzeni sensownych genomów CLOS" (której nikt nie
  zdefiniował niezależnie od tego pudełka).

## 3. KLUCZOWE: flagowy endpoint NIE dyskryminuje genomów po korekcie
### [ZAPIS HISTORYCZNY — etap n=10; status UNIEWAŻNIONY dla WM/Pattern Recognition re-runem 2026-07-20, patrz adnotacja na końcu sekcji]

**Working Memory** — primary endpoint całej lekcji L1.1, jedyna oś
opisana w `README.md` jako reprezentatywny wynik — jest **100%
GENOME-ROBUST (mierzalna) w obu stosowanych środowiskach, ale 0 z 253 par
genomów przeżywa korektę Benjamini-Hochberg FDR w którymkolwiek z nich**
(`docs/VALIDITY_REPORT.md` §"Kluczowe odkrycie", `reports/population/
population_validation_v0_10_1.json`).

**Nie wolno twierdzić:** "CLOS mierzy różnice w working memory między
genomami" ani "genom X ma lepszą working memory niż genom Y" na
podstawie danych z tego projektu — łącznie z historycznym Cohen's
d=0.327 między `default`/`highly_plastic` (`competency_profile.md`,
v0.9/v0.10), który **nie utrzymuje się** po korekcie na 23 genomach.

**Wolno twierdzić:** "endpoint `mse_vs_pattern_after_stimulus_removal` jest
wiarygodnie, powtarzalnie mierzalny (realna wariancja międzyseedowa,
CI95 ważne) dla każdego z 23 przebadanych genomów" — to jest osobne,
prawdziwe i słabsze twierdzenie niż "wykrywa różnice między genomami".
Mylenie tych dwóch jest dokładnie błędem, który ten sprint miał wykryć.

**To samo ograniczenie dotyczy Pattern Recognition i Pattern Retention**
(też 100% mierzalne, 0/253 par po FDR w obu środowiskach) — trzy z
siedmiu zmierzonych osi w ogóle nie różnicują genomów w tej próbce.

---

**ADNOTACJA 2026-07-21 (re-run konfirmacyjny n=185, zamknięty 2026-07-20
— dopisana, sekcja powyżej NIE jest edytowana w miejscu):**

**KOREKTA (audytor złapał błąd w pierwszej wersji tej adnotacji, znaleziony
bezpośrednio na surowym pliku):** pierwotnie napisałem tu, że 0/253
"pozostaje prawdziwe i aktualne również na n=185 (test parowy)" dla
Working Memory i Pattern Recognition — **to jest fałszywe.** Sprawdziłem
`population_validation_v0_11_0.json` (pole
`pairwise_comparisons.n_fdr_significant_q_0_05`) i niezależnie przeliczyłem
Benjamini-Hochberg z surowych p-wartości — oba zgodne: **Working Memory =
69/253 (27%), Pattern Recognition = 77/253 (30%)**. Zakaz "Nie wolno
twierdzić" powyżej jest więc dla tych dwóch osi **UNIEWAŻNIONY W PEŁNI**,
nie tylko omnibusowo — oba niezależne testy (Welch-pary+FDR ORAZ
Kruskal-Wallis) zgadzają się co do istnienia różnicy międzygenomowej:
Working Memory p=8.1e-17 (**VALIDATED**), Pattern Recognition p=4.5e-14
(**VALIDATED**) — `docs/METRIC_STATUS_TABLE.md` §4b, footnotes¹⁰ ¹⁵.

**Pattern Retention jest JEDYNĄ z trzech osi, dla której 0/253 parowo
pozostaje prawdziwe na n=185** — tam faktycznie sygnał jest wyłącznie
omnibusowy: Kruskal-Wallis p=0.0254 (**EXPERIMENTAL**, Red Team,
`docs/METRIC_STATUS_TABLE.md` §7.1), test parowy przegapił słaby,
niemonotoniczny efekt.

**Nadal zabronione** (WM/Pattern Recognition): twierdzenie o KONKRETNEJ,
niesprawdzonej parze bez odczytania `pairwise_comparisons.details` dla tej
konkretnej pary — 184/253 (WM) i 176/253 (Pattern Recognition) par NADAL
nie przeżyło FDR, więc "genom X ma lepszą Working Memory niż genom Y" jest
fałszywe dla WIĘKSZOŚCI par, prawdziwe tylko dla wskazanych w pliku.
**Teraz dozwolone** (od 2026-07-20, WM/Pattern Recognition): "populacja 23
genomów jako całość różni się w Working Memory/Pattern Recognition —
zarówno parowo (69/253, 77/253 par) jak i omnibusowo — z zastrzeżeniem
winner's curse: wielkość efektu w eksploracji n=10 była zawyżona dla WM (f
0.2652→0.1537) i nietypowo wzrosła dla Pattern Recognition (f
0.130→0.1638)". Dla Pattern Retention dozwolone jest wyłącznie
twierdzenie omnibusowe (jak w §3 tabeli powyżej dla WM przed korektą).
Pełny mechanizm: `docs/METRIC_STATUS_TABLE.md` §7 (Red Team) i footnote¹⁵.

## 4. Zakres to 2 lekcje, 23 genomy, 3/9 środowisk — nie wszechświat

- **2 lekcje.** Cała architektura Capability Analyzer (relacja N:M,
  `clos_scientist/capability_analyzer.py`) była walidowana wyłącznie na
  L1.1 i L1.2. Nie ma dowodu, że framework skaluje się do trzeciej,
  strukturalnie innej lekcji — to jest luka wypisana wprost w
  `RAPORT_v0.10.md` i `docs/ROBUSTNESS_MATRIX.md`.
- **23 genomy** (20 próbkowanych LHS + 3 istniejące presety) to próbka
  eksploracyjna jednego, konkretnego pudełka parametrów (§2), z jednym
  ustalonym seedem próbkowania (`20101`). Nie jest to twierdzenie o
  "wszystkich możliwych genomach CLOS", a tym bardziej nie o genomach w
  jakimkolwiek innym systemie.
- **3 z 9 istniejących środowisk** (`noise_world`/`shock_world`,
  `stable_world`, `drift_world` — po jednym zestawie per lekcja) mają
  pełną analizę populacyjną (mierzalność + dyskryminacja FDR). Pozostałych
  5 środowisk z v0.10.1 P2 (`high_noise_world`, `recurring_shock_world`,
  `weak_shock_world`, `long_stable_shock_world`, `unpredictable_world`) ma
  WYŁĄCZNIE dowód usuwalności obserwatora + regresję + telemetrię
  (smoke-test na 2 genomach × 3 seedy) — **nie wolno twierdzić, że którakolwiek
  metryka jest ROBUST/FRAGILE na tych 5 środowiskach** — to po prostu
  niezmierzone, nie "prawdopodobnie podobne do już zmierzonych".

## 5. Hipotezy post-hoc to NIE ustalenia

`docs/VALIDITY_REPORT.md` opisuje silną korelację: genomy z
`decay_rate>~0.035` systematycznie degenerują `adaptation_tick`/
`final_energy` w L1.1. **Ta korelacja została zauważona PO zobaczeniu
wyników populacji, na tych samych 23 genomach** — nie była częścią planu
prerejestracji P1 (`preregistration_v0_10_1_population.json` deklarowała
próg mierzalności, próg GENOME-ROBUST, korektę FDR — nie próg
`decay_rate`).

**Nie wolno twierdzić:** "wykazaliśmy, że `decay_rate>0.035` powoduje
degenerację Adaptation" jako ustalony fakt. To jest **hipoteza robocza**,
wymagająca osobnej prerejestracji i weryfikacji na niezależnej próbce
(nowe seedy/genomy nieużyte do wyprowadzenia progu), zanim stanie się
czymś więcej niż obserwacją na tych konkretnych 23 punktach.

## 6. Skonsolidowane ograniczenia z wcześniejszych sprintów (bez zmian, tylko przypomniane)

- **`recovery_time` w L1.2 mierzy USTANOWIENIE, nie POWRÓT** homeostazy
  (`pre_shock_in_band_fraction=0.0` dla obu oryginalnych genomów, v0.9) —
  nie wolno pisać "Brain odzyskuje homeostazę po szoku" bez tego
  zastrzeżenia; poprawna nazwa endpointu to `time_to_sustained_band`.
- **Duże Cohen's d (np. Stability=9.46) świadczy o precyzji pomiaru
  (małej wariancji resztowej), nie o dużym efekcie praktycznym** (v0.10
  §6c) — nie mylić pewności statystycznej z wielkością efektu.
- **Name-gate:** logika `recovery_time`/`t_shock` w L1.2 aktywuje się
  wyłącznie dla scenariusza nazwanego dosłownie `"shock_world"` (P2) — nie
  wolno zakładać, że wyniki L1.2 generalizują się na jakikolwiek inny
  scenariusz "typu szokowego", nawet strukturalnie podobny.
- **Adaptation/Stability były zdegenerowane u źródła do v0.9 włącznie**
  (puste snapshoty, `RAPORT_v0.9.md`) — jakiekolwiek wnioski z raportów
  sprzed v0.10 P3 o tych dwóch osiach są nieważne retroaktywnie, nie tylko
  "ostrożne".

## 7. Co WOLNO twierdzić (żeby dokument nie czytał się jako czysta negacja)

- Infrastruktura CI95/`n_effective`/pseudoreplikacji poprawnie odróżnia
  sygnał od szumu — potwierdzone empirycznie na `stable_world` (zawsze
  `n_effective=1`, zero wyjątków na 23 genomach × wszystkich metrykach).
- Read-Only Observer nie wpływa na Execution Pipeline — dowiedzione
  empirycznie (nie tylko zadeklarowane), na 6 środowiskach, 2 lekcjach.
- Korekta na wielokrotne porównania (BH-FDR) faktycznie zmienia wnioski
  (np. Working Memory 3 surowo istotne pary → 0 po korekcie) — pokazuje,
  że infrastruktura wykrywa własne fałszywe alarmy, co jest mocnym
  argumentem za jej wiarygodnością jako narzędzia, nawet gdy wynik
  naukowy jest "brak sygnału".
- Procedura replikacji została zweryfikowana niezależnie, na innej
  platformie (`docs/REPLICATION.md` §4bis pkt 5) — to jest fakt, nie
  deklaracja.

# SPRINT v0.11.0 — Scientific Foundation [dyrektywa CTO, akceptacja CEO]

Gałąź: `v0.7.2-scientific-integrity`. Priorytet → testy → commit → push → audyt.
Status: **Research Grade Infrastructure for Artificial Ontogenesis.**

**NOWY KPI PROJEKTU (decyzja CTO/CEO — zmiana filozofii, nie kosmetyka):**
> „Każdy wynik wygenerowany przez laboratorium jest wiarygodny, replikowalny
> i metodologicznie obronny."

Od tego sprintu CLOS rozwijamy przede wszystkim jako **laboratorium badawcze
klasy research-grade**, nie jako system poznawczy. Sukces sprintu = możliwość
powiedzenia: *laboratorium potrafi odróżnić fakty od hipotez, a każdy wynik ma jasno
określony poziom wiarygodności.* NIE oczekuje się nowych wykresów, funkcji ani
„inteligentniejszego mózgu".

**Dokumentacja jest CZĘŚCIĄ PRODUKTU, nie dodatkiem** (CTO): każda zmiana
metodologiczna ma być zrozumiała **bez czytania kodu**.

Cel (CTO): NIE „zwiększyć inteligencję". **Uczynić laboratorium naukowo wiarygodnym.**
Rozwój zdolności poznawczych (Predictive Coding, Latent Space, Planning, Generalization)
WSTRZYMANY do czasu naprawy narzędzi pomiarowych.

---

## ZASADY NADRZĘDNE

**1. Cisza jest gorsza niż błąd — laboratorium samoopisujące (zasada konstytucyjna, CTO):**
> Jeśli metryka nie potrafi policzyć wyniku w danym kontekście — **zgłasza wyjątek,
> nie zwraca błędnego/cichego wyniku.**

Dziś `weak_shock_world` przechodzi przez harness L1.2 i **cicho nie produkuje
endpointu**. To ma zniknąć.

**Jakość wyjątku (wymóg CTO — nie wystarczy `ValueError(...)`):** każdy wyjątek MUSI
opisywać: **(a) która metryka, (b) jaki scenariusz, (c) jaki warunek został naruszony,
(d) dlaczego wynik odrzucony.** Wyjątek ma pomóc badaczowi ZROZUMIEĆ problem, nie tylko
zatrzymać wykonanie. Laboratorium ma być samoopisujące — zrozumiałe bez czytania kodu.

**2. ZERO OVERFITTINGU (zakaz CTO):** hipoteza `decay_rate ≈ 0.035` pozostaje WYŁĄCZNIE
hipotezą. **ZAKAZANE:** dostrajanie genomów, zmiany parametrów, zmiany progów pod tę
obserwację. Najpierw niezależna, prerejestrowana walidacja — dopiero potem wolno mówić
o regule. Jeśli w trakcie refaktoru jakikolwiek próg/parametr miałby się zmienić w
sposób zbieżny z tą hipotezą — STOP i eskaluj.

**3. DANE v0.10 = Exploratory Dataset (decyzja CTO):** wyniki v0.10/v0.10.1 NIE są
kasowane, przepisywane ani poprawiane. Otrzymują status **Exploratory Dataset v0.10**:
materiał badawczy — **nie dowód, nie podstawa twierdzeń, ale też NIE błąd**. To z nich
policzono `f_obs`, które uratowało nas przed fałszywym zakazem. Zadanie: oznaczyć
istniejące artefakty (`reports/population/`, raporty academy) tym statusem.

**4. Laboratorium ma obowiązek ODRZUCAĆ własne hipotezy (CTO):** nie budujemy systemu,
który potwierdza oczekiwania. Budujemy taki, który równie łatwo mówi „hipoteza obalona"
i „nie wiemy".

**5. Brak wykrytego efektu ≠ brak efektu (zasada CTO):** najpierw moc, dopiero potem
interpretacja. Wyniku negatywnego nie wolno interpretować jako dowodu braku efektu,
dopóki nie znamy mocy testu.

**6. Naprawiamy SPOSÓB POMIARU, nie WYNIKI (bramka regresji):**
Refaktor metryk NIE może zmienić opublikowanych liczb: **L1.1 0.156712 / 0.173229,
L1.2 15.4**. Dla `shock_world` semantyczna detekcja musi dać *dokładnie to samo*, co
dawał name-gate. Różnica → STOP i eskalacja. Inwarianty v0.9/v0.10 obowiązują
(behavior-frozen, usuwalność obserwatora, Execution/Observation).

**7. Nie duplikujemy źródeł prawdy:**
Istnieje `docs/VALIDITY_REPORT.md` (v0.10.1 P4, 449 linii) odpowiadający na pytania
Zadania 1. **Ewoluuj go** (dopisz formalne definicje + statusy) albo zastąp z jawną
notą „supersedes". NIE twórz drugiego dokumentu o tym samym.

**8. Laboratorium v1 = FORMALIZOWAĆ istniejące, nie przebudowywać:**
Eksperyment/scenariusz/metryki/prereg/raport/walidacja/replikacja **już działają**
(replikacja potwierdzona ślepym testem audytora na Linuksie). Wielki refaktor to duże
ryzyko dla inwariantów przy małym zysku.

Zakazane: Predictive Coding, Latent Space, Planning, Generalization jako kod;
zmiana logiki poznawczej; zmiana opublikowanych wyników.

---

## P0 — ANALIZA MOCY STATYSTYCZNEJ (BRAMKA — przed statusami metryk)

**Powód (odkrycie z recenzji zewnętrznej):** twierdzimy „Working Memory nie
dyskryminuje genomów". Dane mówią: „przy n=10/genom i FDR na 253 par **nie
wykryliśmy** różnic". To NIE to samo. Dwa wyjaśnienia:
- (a) metryka faktycznie nie różnicuje,
- (b) **brakuje mocy statystycznej**.

Obecne dane tego nie rozstrzygają — a `VALIDITY_REPORT`/`CURRENT_SCIENTIFIC_LIMITS`
postawiły (a) jako ustalenie i wpisały **zakaz** twierdzenia. To przeszacowanie wyniku
NEGATYWNEGO. Projekt nigdy nie zrobił power analysis (scipy nie było w zależnościach).

Zakres:
1. Policz moc obecnego projektu: n=10/genom, BH-FDR q=0.05, 253 par — **jaki najmniejszy
   efekt (Cohen's d) jesteśmy w stanie wykryć przy mocy 0.8?**
2. Jeśli moc jest niska: **re-run populacji przy n=30/genom** (23 × 3 środ. × 30 × 2 lekcje
   ≈ 4140 runów, szacunkowo ~25-30 min — koszt trywialny wobec wartości).
3. Rozstrzygnij (a) vs (b) EMPIRYCZNIE dla Working Memory / Pattern Recognition /
   Pattern Retention (wszystkie 100% ROBUST, zero par po FDR).
4. **Jeśli okaże się (b) — POPRAW `docs/VALIDITY_REPORT.md` i
   `docs/CURRENT_SCIENTIFIC_LIMITS.md`.** Zakaz oparty na niedomocnionym teście musi
   zostać przeformułowany na „nie wykryliśmy przy tej mocy", nie „nie dyskryminuje".
5. Prerejestruj re-run przed uruchomieniem (n, moc docelowa, próg) — jak w v0.10.1 P1.

**To jest bramka: statusy metryk (P3) NIE mogą powstać, dopóki nie wiemy, czy nasze
testy mają moc uzasadnić etykietę. INVALID z braku mocy = ten sam błąd co VALIDATED
bez replikacji.**

## P1 — Formalne definicje metryk (Zadanie 1 CTO)

- **Ewoluuj `docs/VALIDITY_REPORT.md`** (nie twórz duplikatu): dla każdej z 14 osi dodaj
  **formalną definicję matematyczną** (jak `recovery_time` w prereg L1.2): co dokładnie
  liczy, na jakim oknie, z jakimi warunkami brzegowymi.
- Dla każdej odpowiedz jawnie: czy **nazwa odpowiada pomiarowi**? czy mierzy zjawisko
  **po** zdarzeniu, a nie przed? jakie ma **ukryte założenia**?
- Znane do rozliczenia (nie odkrywaj od nowa): `adaptation_tick` mierzy okno PRZED
  szokiem w L1.2; `recovery_time`→`time_to_sustained_band` (arrival vs return);
  `t_shock ≤ 150` (KeyError powyżej); name-gate `"shock_world"`.

## P2 — Refaktor: semantyka zamiast nazw (Zadanie 2 CTO)

- Usuń **name-gates** (`scenario == "shock_world"` dosłownie), **hardcoded ticki**,
  **ukryte limity**. Metryka działa na **właściwości scenariusza** (np. „czy scenariusz
  deklaruje zdarzenie perturbacyjne i kiedy"), nie na nazwie.
- **Gdy nie potrafi policzyć → WYJĄTEK**, nie cichy brak/zły wynik (zasada nadrzędna 1 — z pełnym opisem: metryka/scenariusz/warunek/powód).
- **BRAMKA REGRESJI:** L1.1 0.156712/0.173229 i L1.2 15.4 **bajtowo niezmienione**;
  `test_step_regression`, `test_observer_removability`, `test_genome_params_regression`
  zielone. Różnica → STOP.
- Test: nowy świat szokowy (`weak_shock_world`) po refaktorze **albo liczy endpoint,
  albo rzuca wyjątek** — nie milczy.

## P3 — Cztery niezależne statusy metryk (decyzja CTO)

**Nie istnieje już pojedyncza etykieta „VALIDATED".** Każda metryka otrzymuje CZTERY
niezależne statusy (dyrektywa CTO):

| Status | Pytanie |
|---|---|
| **Measurement Validity** | Czy da się to zmierzyć? |
| **Construct Validity** | Czy mierzy to, co nazwa obiecuje? |
| **Statistical Power** | Czy mamy moc, by cokolwiek orzec? |
| **Confirmatory Status** | Czy wolno na tym oprzeć twierdzenie? |

Przykład (CTO): *Adaptation — ✔ mierzalna · ✘ konstrukcyjnie błędna · ✘ brak mocy ·
✘ nie może być interpretowana.*

### DOPRECYZOWANIE AUDYTORA: statusy per METRYKA × KONTEKST, nie per metryka

Dowód z naszych danych — ta sama metryka ma **przeciwne** statusy zależnie od kontekstu:
- `adaptation_tick` w **L1.1**: mierzy stabilizację energii od zimnego startu →
  **Construct Validity ✔**
- `adaptation_tick` w **L1.2**: mierzy okno **przed szokiem** (t_shock≥20, detektor od
  tick=10) → **Construct Validity ✘** — mierzy co innego, niż nazwa obiecuje

Jedna etykieta skłamałaby o jednym z tych kontekstów. To samo dla mocy: Working Memory
ma f=0.265 w `noise_world`, ale w `stable_world` jest deterministyczna (n_eff=1).
**Moc jest własnością kontekstu, nie metryki.**

→ Tabela statusów ma mieć wiersz na **metrykę × lekcja × środowisko** (30 kontekstów
z v0.10.1 P3), nie 14 wierszy na metrykę.

**Statistical Power i Confirmatory Status czekają na wynik re-runu** (bramka P0).
Measurement i Construct Validity mogą być przypisane teraz — nie zależą od mocy.

**AKCEPTACJA CTO/CEO — WPROST:** *„Jeżeli okaże się, że Adaptation przestanie istnieć,
Working Memory okaże się bezużyteczne, profil spadnie z 7 osi do 2 — akceptuję taki
wynik bez żadnych prób ratowania statystyk. Nie poprawiamy wyników. Poprawiamy prawdę
o systemie."*

**ZAKAZ JĘZYKOWY (CTO):** raporty NIE MOGĄ zawierać sformułowania „genomy się nie
różnią", jeśli analiza była niedomocniona. Poprawny komunikat: **„Eksperyment nie miał
wystarczającej mocy do rozstrzygnięcia hipotezy."**

## P4 — Rozdzielenie hipotez od faktów (Zadanie 4 CTO)

- `docs/ESTABLISHED_FINDINGS.md`: **wyłącznie** prerejestrowane + zreplikowane +
  potwierdzone.
- `docs/RESEARCH_HYPOTHESES.md`: `decay_rate ≈ 0.035`, wszystkie obserwacje post-hoc,
  przypuszczenia wymagające nowych eksperymentów.
- **Żadna hipoteza nie wpływa na kod produkcyjny** — sprawdź grepem i zaraportuj.
- Kandydat do ESTABLISHED: replikacja Windows↔Linux (ślepy test audytora, 2026-07-14).

## P5 — Experimental Framework: dokumentacja architektury (Zadanie 5 CTO)

- `docs/EXPERIMENTAL_FRAMEWORK.md`: **opisz to, co istnieje** (eksperyment, scenariusz,
  metryki, prereg, raport, walidacja, replikacja) + **jawne luki**. Formalizacja, nie
  przebudowa (zasada nadrzędna 8).
- Wpisz zasadę „cisza gorsza niż błąd" do `docs/architecture.md` obok Execution/Observation.

## P6 — Cognitive Roadmap (Zadanie 6 CTO)

- `docs/COGNITIVE_ROADMAP_v1.md`: dla Predictive Coding / Planning / Generalization /
  Latent Space — **wymagania naukowe, zależności, kryteria wejścia, kryteria zakończenia**.
- **ZERO implementacji.** Nowe moduły dopiero po spełnieniu kryteriów wejścia.
- Kryterium wejścia musi odnosić się do stanu metryk: nie buduj zdolności na metrykach
  bez statusu VALIDATED (albo jawnie uzasadnij dlaczego wolno).

---

## KRYTERIA ZAKOŃCZENIA (CTO)
Wszystkie metryki z formalną definicją · usunięte ukryte założenia (name-gates, limity)
· statusy przypisane (per-kryterium) · hipotezy oddzielone od faktów · kompletna
dokumentacja metodologiczna · architektura gotowa do dużych prerejestrowanych badań ·
**+ (audytor): moc statystyczna policzona, opublikowane liczby bajtowo zachowane,
wszystkie regresje zielone, 4 walidatory zielone.**

## DYSCYPLINA GITA
Jeden logiczny commit na priorytet; jawna lista plików (nie `git add -A`);
`git status --short` PRZED commitem; regresje + walidatory zielone przed commitem;
komunikat = realny stan. Push + audyt. Nie commituj `.claude/` ani śmieci.

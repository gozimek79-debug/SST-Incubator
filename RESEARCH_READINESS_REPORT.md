# Research Readiness Report

**SPRINT_v0.10.1.md P7, Zadanie 7 CTO. Jedno pytanie: czy można rozpocząć
proces publikacyjny?**

**Odpowiedź: zależy, co chcemy publikować. Na artykuł metodologiczny/
infrastrukturalny — TAK. Na artykuł z twierdzeniami o zdolnościach
poznawczych różnicujących genomy — JESZCZE NIE, i poniżej jest dokładnie
dlaczego.** Nie sprzedajemy gotowości, której nie ma — to jest sprint
walidacyjny, którego celem było znalezienie granic, nie potwierdzenie
sukcesu (SPRINT_v0.10.1.md, zasada nadrzędna), i granice się znalazły.

---

## 1. Mocne strony

### 1.1 Ślepy test replikacji — twardy fakt, nie deklaracja

Niezależny audytor (badacz spoza projektu) wykonał **czysty klon + czysty
venv + `pip install -r requirements.txt` + `pip install pytest` +
komendy dosłownie z `docs/REPLICATION.md`**, na **Linux (Ubuntu),
Python 3.12** — podczas gdy cała procedura była wcześniej zweryfikowana
tylko na Windows (Python 3.14.5). Wynik: **0.156712 / 0.173229 / 15.4 /
7 z 14 odtworzone dokładnie, 4 walidatory `exit 0`**
(`docs/REPLICATION.md` §4bis, punkt 5, zamknięty 2026-07-14).

To jest różnica jakościowa względem "twierdzimy, że nasze wyniki są
replikowalne" — **replikacja faktycznie się wydarzyła, na niezależnej
maszynie, innym systemie operacyjnym, innej wersji Pythona, przez osobę
bez dostępu do historii projektu.** To jest dokładnie ten rodzaj dowodu,
którego oczekuje się przed preprintem, i mało projektów na tym etapie ma
go w ogóle wykonany, nie tylko zadeklarowany.

### 1.2 Infrastruktura integralności naukowej jest realna, nie deklaratywna

- CI95/`n_effective`/pseudoreplikacja (`clos_curriculum/laboratory/statistics.py`,
  od v0.7.2) — odróżnia realną wariancję międzyseedową od powtórzeń
  identycznego, deterministycznego wyniku. Zweryfikowane wprost: na 23
  genomach `stable_world` (kontrola) daje `n_effective=1` dla KAŻDEJ
  metryki, KAŻDEGO genomu, bez wyjątku — mechanizm działa tak, jak powinien.
- Prerejestracja jako bramka, nie formalność — trzy przypadki, gdzie
  proces bramkowy faktycznie wpłynął na wynik przed implementacją: L1.2
  (próg `pre_shock_band_check` zmieniony 0.5→0.8 przed implementacją,
  v0.9), populacja v0.10.1 (metrologia zatwierdzona PRZED uruchomieniem
  1380 przebiegów).
- Execution/Observation Pipeline (`docs/architecture.md`) — zasada z
  falsyfikowalnym testem (usuwalność obserwatora), nie tylko architektoniczna
  deklaracja, dowiedziona empirycznie na 6 środowiskach × 2 lekcjach.
- **Korekta na wielokrotne porównania (BH-FDR) faktycznie coś zmienia** —
  Working Memory: 3 "surowo istotne" pary (p<0.05) na 253 → **0 po
  korekcie**. To pokazuje, że infrastruktura wykrywa WŁASNE fałszywe
  alarmy — silny argument za jej wiarygodnością jako narzędzia,
  niezależnie od tego, czy konkretny wynik naukowy jest pozytywny.

### 1.3 Track record uczciwego raportowania ograniczeń

Każdy sprint od v0.8.4 kończy się dokumentem wprost nazywającym, co NIE
działa: puste snapshoty (`RAPORT_v0.9.md`), degeneracja Adaptation/
Stability (ten sam dokument), name-gate i granica `t_shock≤150`
(`RAPORT_v0.10.md`/P2 tego sprintu), a teraz — najważniejsze — **flagowy
endpoint L1.1 nie różnicuje genomów po korekcie**
(`docs/VALIDITY_REPORT.md`). Żaden z tych wyników nie został ukryty ani
złagodzony w opisie.

---

## 2. Ograniczenia

- **17 z 30 kontekstów metryka×środowisko×lekcja jest GENOME-FRAGILE**
  (`docs/ROBUSTNESS_MATRIX.md`) — ponad połowa zmierzonej przestrzeni nie
  daje wiarygodnego CI95 w tej próbce genomów.
- **Flagowy endpoint (Working Memory) jest mierzalny, ale nie
  dyskryminuje genomów** po korekcie FDR — 0/253 par w obu stosowanych
  środowiskach. To samo dotyczy Pattern Recognition i Pattern Retention.
  Trzy z siedmiu zmierzonych osi nie niosą sygnału różnicującego genomy w
  tej populacji.
- **2 lekcje.** Architektura Capability Analyzer (N:M) nigdy nie była
  wystawiona na trzecią, strukturalnie inną lekcję.
- **3 z 9 środowisk** mają pełną analizę populacyjną; pozostałe 5 (P2) —
  tylko smoke-test usuwalności/telemetrii.
- **Homeostatic Resilience (drugi primary endpoint, L1.2)** jest
  mierzalny tylko dla 21.7% populacji (5/23 genomów) — reszta ucenzurowana.
- **Hipoteza `decay_rate≈0.035`** (mechanizm degeneracji Adaptation/Energy
  Efficiency) jest post-hoc, nieprzetestowana niezależnie —
  `docs/CURRENT_SCIENTIFIC_LIMITS.md` §5.
- **Genomy nie są próbką z niezależnie zdefiniowanej przestrzeni** —
  parametry i ich zakresy zostały ustawione przez autorów kodu
  (`genome/presets.py`), nie odkryte ani empirycznie uzasadnione
  (`docs/CURRENT_SCIENTIFIC_LIMITS.md` §2).
- **Ślepy test replikacji potwierdza Windows↔Linux, nie macOS** —
  węższe zamknięcie niż "wszystkie platformy".
- **Recenzja zewnętrzna ograniczona do jednego ślepego testu replikacji**
  — brak dotąd pełnego peer review kodu/metodologii poza tym.

---

## 3. Otwarte pytania

1. Czy `decay_rate>~0.035` faktycznie mechanistycznie powoduje
   degenerację Adaptation/Energy Efficiency, czy to koincydencja tej
   konkretnej próbki 23 genomów? Wymaga osobnej prerejestracji i nowej
   próbki (nie tej samej, na której hipotezę zauważono).
2. Czy Stability z L1.1 i L1.2 są współmierne jako repliki tej samej
   cechy genomu (różne konteksty zadaniowe), czy to błąd metodologiczny
   gdyby je połączyć? Decyzja świadomie odłożona od v0.10 P4.
3. Czy trzecia, strukturalnie inna lekcja potwierdziłaby architekturę
   N:M Capability Analyzer, czy ujawniłaby nowe problemy analogiczne do
   name-gate w L1.2?
4. Czy 5 środowisk z P2 (bez pełnej analizy populacyjnej) dałoby podobny
   rozkład ROBUST/FRAGILE co 3 już zbadane, czy zupełnie inny?
5. Czy da się zaprojektować endpoint L1.2 niezależny od dosłownej nazwy
   scenariusza (naprawiając name-gate), bez zmiany Core?
6. Dlaczego Working Memory/Pattern Recognition/Pattern Retention są
   idealnie mierzalne, ale zero-dyskryminujące — czy to mówi coś o samym
   zadaniu (za łatwe/za mało wrażliwe na te konkretne różnice genomowe),
   czy o zakresie przetestowanych genomów?

---

## 4. Rekomendacje przed pierwszym preprintem

1. **Ramuj artykuł jako pracę o METODOLOGII/INFRASTRUKTURZE walidacji
   eksperymentów poznawczych**, nie jako pracę o odkrytych zdolnościach
   poznawczych. Najsilniejszy, najbardziej obronny wynik tego projektu to
   sama zdolność infrastruktury do wykrycia, że pozornie obiecujący wynik
   z 2 genomów (Cohen's d=0.327) nie utrzymuje się na 23 — to jest wynik
   metodologiczny wart publikacji sam w sobie.
2. **Jeśli mimo to raportowane są wyniki na Working Memory** — obowiązkowo
   dołączyć kontekst FDR (0/253 par), nie tylko historyczny Cohen's d.
   Publikacja samego d=0.327 bez tego kontekstu byłaby wprowadzająca w
   błąd w świetle tego, co teraz wiadomo.
3. **Nie twierdzić nic o "typowym genomie" ani "przestrzeni genomów CLOS"**
   bez zastrzeżenia, że zakresy parametrów są wyborem projektowym, nie
   odkryciem (`CURRENT_SCIENTIFIC_LIMITS.md` §2).
4. **Przetestować hipotezę `decay_rate` w osobnym, prerejestrowanym
   badaniu** na nowej próbce, zanim pojawi się w jakimkolwiek tekście jako
   coś więcej niż "obserwacja do zbadania".
5. **Rozważyć trzecią lekcję** przed twierdzeniem, że architektura N:M
   Capability Analyzer jest ogólnym rozwiązaniem — obecnie jest
   zweryfikowana na 2 punktach danych (L1.1, L1.2), co jest słabym
   dowodem generalizacji.
6. **Nie nazywać żadnego wyniku "recovery"** bez sprawdzenia
   `pre_shock_in_band_fraction` — endpoint L1.2 mierzy ustanowienie, nie
   powrót, w obecnych danych.

**Podsumowanie:** infrastruktura jest solidna i częściowo niezależnie
zweryfikowana (replikacja cross-platform) — to jest gotowe do pokazania.
Zawartość naukowa (7 zmierzonych osi, z czego 3 nie dyskryminują genomów,
17/30 kontekstów fragile) NIE uzasadnia jeszcze artykułu o odkrytych
różnicach poznawczych między genomami. Te dwie rzeczy są rozdzielne —
można (i powinno się) opublikować pierwszą, nie czekając na drugą.

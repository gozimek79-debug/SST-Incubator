# Replication — odtworzenie głównych wyników wyłącznie z repo

**Status: SPRINT_v0.10.1.md P6 (Zadanie 5 CTO).** Ten dokument zakłada, że
czytelnik ma WYŁĄCZNIE: (a) to repozytorium sklonowane na commit podany
niżej, (b) tę stronę, (c) standardowe narzędzia (git, Python, pip). **Zero
dostępu do historii tej sesji, do SPRINT_*.md, do RAPORT_*.md, do jakiejkolwiek
wiedzy plemiennej.** Jeśli którykolwiek krok poniżej wymaga czegoś spoza tej
listy, to jest błąd tego dokumentu, nie założenie.

Commit, na którym te instrukcje zostały zweryfikowane:
`f721d737d93559666ff40a16cb51d5854b549ba1` (branch `v0.7.2-scientific-integrity`).

---

## 0. Środowisko

```bash
git clone https://github.com/gozimek79-debug/SST-Incubator.git
cd SST-Incubator
git checkout v0.7.2-scientific-integrity
```

**Python:** CI (`.github/workflows/ci.yml`) jest przypięte do **3.12**
(`actions/setup-python@v5`, `python-version: "3.12"`) — to jest oficjalny,
testowany target. Ta konkretna procedura replikacji została dodatkowo
zweryfikowana ręcznie na **Python 3.14.5** (nowszy niż CI, nieprzypięty
nigdzie indziej w repo) — wszystkie liczby niżej wyszły identyczne. Brak
`.python-version`/`pyproject.toml` przypinającego wersję dla lokalnego
developmentu — **to jest luka, wypisana jawnie w §4**, nie ukryta.

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest
```

`requirements.txt` (dokładne, przypięte wersje — jedyne, jakie repo
deklaruje):
```
pydantic==2.5.0
pyyaml==6.0.1
fastapi==0.104.1
uvicorn==0.24.0
networkx==3.2.1
matplotlib==3.8.2
```
`pytest` **nie jest w `requirements.txt`** (zainstaluj osobno, wersja
nieprzypięta — ta procedura zweryfikowana na `pytest-9.1.1`) — patrz §4.

**Katalog roboczy:** WSZYSTKIE komendy niżej MUSZĄ być uruchamiane z
katalogu głównego repo (`SST-Incubator/`) — kod lekcji robi
`sys.path.insert(0, os.getcwd())` i odwołuje się do `reports/`,
`publications/` ścieżkami względnymi. Uruchomienie z innego katalogu da
błędy importu, nie inne liczby.

---

## 1. Test suite (szybki sanity check przed właściwą replikacją)

```bash
pytest -q
```

**Oczekiwane:** `364 passed` (może się różnić w czasie o kilka-kilkanaście
sekund, ~200-235s w tej sesji). Jeśli którykolwiek test padnie, NIE
kontynuuj replikacji poniżej — commit jest w stanie niespójnym z tym
dokumentem.

```bash
python scripts/validate_publication.py
python scripts/validate_artifacts.py
python scripts/validate_panel.py
python scripts/validate_observability.py
```
**Oczekiwane:** wszystkie 4 kończą się `exit 0` i drukują `OK`.

---

## 2. L1.1 "Pattern Echo" — Working Memory (primary endpoint)

```bash
python -m clos_academy.lesson_L1_1
```

Trwa kilka sekund. Na końcu wypisuje m.in.:
```
Genome: default
  ...
  Summary: 10/10 passed, mean MSE@50=0.1567, ...
Genome: highly_plastic
  ...
  Summary: 10/10 passed, mean MSE@50=0.1732, ...
```

**Dokładna wartość** (6 miejsc po przecinku, nie zaokrąglona konsolowo) jest
w regenerowanym `reports/academy/L1_1_pattern_echo.json`:

```bash
python -c "import json; d=json.load(open('reports/academy/L1_1_pattern_echo.json',encoding='utf-8')); print(d['per_genome']['default']['experimental_stats']['mean']); print(d['per_genome']['highly_plastic']['experimental_stats']['mean'])"
```

**Oczekiwane (dokładnie, zero tolerancji — przebieg jest deterministyczny
dla ustalonego seeda):**
```
0.156712
0.173229
```

---

## 3. L1.2 "Shock Recovery" — Homeostatic Resilience (primary endpoint)

```bash
python -m clos_academy.lesson_L1_2
```

Wypisuje m.in. `mean_recovery_time=15.4` dla genomu `default`.

```bash
python -c "import json; d=json.load(open('reports/academy/L1_2_shock_recovery.json',encoding='utf-8')); print(d['per_genome']['default']['experimental_stats']['mean'])"
```

**Oczekiwane (dokładnie):**
```
15.4
```

Genom `highly_plastic` jest **100% ucenzurowany** (nigdy nie odzyskuje
homeostazy w oknie obserwacji W=150) — `mean` wychodzi `0` z definicji
`compute_ci95([])`, `ci95_valid=False`. To jest oczekiwany wynik naukowy
(`RAPORT_v0.9.md`), nie błąd replikacji.

---

## 4. Competency Profile — 7/14 osi z ważnym CI95

```bash
python -m clos_scientist.competency_profile
```

```bash
python -c "import json; d=json.load(open('publications/competency_profile.json',encoding='utf-8')); print(d['summary']['valid_ci95'], '/', d['summary']['total_concepts'])"
```

**Oczekiwane (dokładnie):**
```
7 / 14
```

Osie w profilu minimalnym: Pattern Recognition, Pattern Retention, Working
Memory, Adaptation, Stability, Energy Efficiency, Homeostatic Resilience —
lista jest w `publications/competency_profile.md` (generowana, nie ręczna).

---

## 5. Walidacja populacyjna — 11 GENOME-ROBUST / 17 GENOME-FRAGILE / 2 not_applicable

**UWAGA: to jest najdłuższy krok, ~7-9 minut** (23 genomy × do 3 środowisk ×
10 seedów × 2 lekcje = 1380 pojedynczych przebiegów symulacji).

```bash
python -m clos_academy.population_validation
```

Wypisuje na żywo klasyfikację per (lekcja, środowisko, metryka), np.:
```
  L1.1 / noise_world (23 genomow x 10 seedow)...
    Working Memory (MSE@50): GENOME-ROBUST (valid_rate=1.0)
    Adaptation: GENOME-FRAGILE (valid_rate=0.3478)
    ...
```

Po zakończeniu, policz zbiorczo:
```bash
python -c "
import json
d = json.load(open('reports/population/population_validation_v0_10_1.json', encoding='utf-8'))
robust = fragile = na = 0
for lesson, envs in d['lessons'].items():
    for env, metrics in envs.items():
        for label, res in metrics.items():
            if res['status'] == 'not_applicable': na += 1
            elif res['classification'] == 'GENOME-ROBUST': robust += 1
            else: fragile += 1
print(f'ROBUST={robust} FRAGILE={fragile} not_applicable={na}')
"
```

**Oczekiwane (dokładnie — próbkowanie LHS jest deterministyczne,
`population_sampling_seed=20101`, zadeklarowany w
`publications/preregistration_v0_10_1_population.json`):**
```
ROBUST=11 FRAGILE=17 not_applicable=2
```

---

## 6. Pełny obraz w jednej komendzie (opcjonalnie)

Kroki 2-5 razem, od zera, z jedną weryfikacją na końcu:

```bash
python -m clos_academy.lesson_L1_1 > /dev/null
python -m clos_academy.lesson_L1_2 > /dev/null
python -m clos_scientist.competency_profile > /dev/null
python -m clos_academy.population_validation > /dev/null
python -c "
import json
l1 = json.load(open('reports/academy/L1_1_pattern_echo.json', encoding='utf-8'))
l2 = json.load(open('reports/academy/L1_2_shock_recovery.json', encoding='utf-8'))
cp = json.load(open('publications/competency_profile.json', encoding='utf-8'))
pop = json.load(open('reports/population/population_validation_v0_10_1.json', encoding='utf-8'))
assert l1['per_genome']['default']['experimental_stats']['mean'] == 0.156712
assert l1['per_genome']['highly_plastic']['experimental_stats']['mean'] == 0.173229
assert l2['per_genome']['default']['experimental_stats']['mean'] == 15.4
assert cp['summary']['valid_ci95'] == 7
r=f=n=0
for envs in pop['lessons'].values():
    for metrics in envs.values():
        for res in metrics.values():
            if res['status']=='not_applicable': n+=1
            elif res['classification']=='GENOME-ROBUST': r+=1
            else: f+=1
assert (r,f,n) == (11,17,2), (r,f,n)
print('WSZYSTKIE GLOWNE WYNIKI ODTWORZONE POPRAWNIE')
"
```

(Na Windows/PowerShell zamiast `> /dev/null` użyj `| Out-Null`; sama logika
weryfikacji w Pythonie jest identyczna na obu platformach.)

---

## 4bis. Jawnie brakujące elementy / ograniczenia tej procedury

Ponumerowane osobno od kroku 4 dla czytelności — to jest wymagana przez
CTO lista braków, nie krok do wykonania.

1. **Brak przypiętej wersji Pythona w repo.** CI używa 3.12; nic w repo
   (brak `.python-version`, `pyproject.toml`, `runtime.txt`) nie wymusza
   tego lokalnie. Ta procedura zweryfikowana na 3.12-styl CI (pośrednio,
   przez zielone CI na każdym pushu) i wprost na 3.14.5 (ta sesja) — nie
   przetestowano wprost na 3.8-3.11, które teoretycznie repo mogłoby też
   obsługiwać (brak `python_requires` w jakimkolwiek pliku konfiguracyjnym).
2. **`requirements.txt` nie pokrywa całego repo.** Krytyczna ścieżka
   replikacji (`clos_academy`, `clos_scientist`, `clos_curriculum.laboratory`,
   `clos_world`, `clos_brain`, `clos_kernel`, `genome`, `birth`, `scripts/`)
   **nie importuje ŻADNEGO** z 6 pakietów w `requirements.txt`
   (zweryfikowane grepem po `import` we wszystkich tych katalogach) — te
   zależności służą innym częściom repo (`clos_dashboard`/`clos_tower`/
   `clos_studio`/`clos_cli`, nieużywanym w tej procedurze). W praktyce
   replikacja głównych wyników działałaby nawet BEZ `pip install -r
   requirements.txt` — instrukcja w §0 zostaje z ostrożności (zgodność z
   README), ale to nie jest zweryfikowana zależność.
3. **`pytest` nie jest przypięty żadną wersją** w żadnym pliku repo —
   zainstaluj najnowszy dostępny; ta procedura zweryfikowana na
   `pytest-9.1.1`. Starsza/nowsza wersja może dawać inny format wyjścia,
   nie inne wyniki testów.
4. **Czas wykonania kroku 5 (~7-9 minut) jest zależny od maszyny** —
   zmierzony na jednej konkretnej maszynie w tej sesji (patrz też ryzyko
   różnic sprzętowych niżej), nie jest gwarantowaną górną granicą.
5. ~~**Determinizm między platformami (Windows/Linux/macOS) nie został
   wprost zweryfikowany w tej sesji.**~~ **ZWERYFIKOWANY — 2026-07-14,
   przez niezależnego audytora, ślepy test replikacji.** Audytor (badacz
   spoza projektu) wykonał czysty klon + czysty venv + `pip install -r
   requirements.txt` + `pip install pytest`, uruchomił komendy dosłownie z
   tego dokumentu, na **Linux (Ubuntu), Python 3.12** — podczas gdy
   procedura była wcześniej zweryfikowana tylko na Windows (Python 3.14.5,
   ta sesja). Wynik: wszystkie główne liczby odtworzone dokładnie
   (`0.156712`/`0.173229`/`15.4`/`7 z 14`), wszystkie 4 walidatory
   zakończone `exit 0`. To jest niezależne potwierdzenie na innej maszynie,
   innym systemie operacyjnym i innej (młodszej niż CI, starszej niż ta
   sesja) wersji Pythona — nie tylko teoretyczne uzasadnienie (IEEE754,
   `pathlib`) sprzed tej weryfikacji. Determinizm Windows↔Linux dla tej
   procedury uznaje się za potwierdzony; macOS pozostaje niezweryfikowany
   (audytor testował Linux, nie macOS) — to węższa, pozostała luka, nie
   pełne zamknięcie punktu dla wszystkich trzech platform.
6. **`git` musi być zainstalowany i dostępny w PATH** — `clos_studio/publication/bundle.py`
   i `clos_academy/population_validation.py` wołają `git rev-parse HEAD`
   dla prowenancji (`_git_commit()`); przy braku gita funkcja po cichu
   zwraca `""` zamiast rzucać wyjątek — replikacja głównych LICZB (kroki
   2-5) nie ucierpi, ale pola `git_commit` w wygenerowanych raportach będą
   puste zamiast realnego hasha.
7. **Krok 5 pisze do dysku** `reports/population/population_validation_v0_10_1.json`
   (~1.4MB) — nadpisuje istniejący plik z repo. Uruchomienie tego kroku na
   klonie repo jest bezpieczne (odtwarza dokładnie ten sam plik, ten sam
   `population_sampling_seed`), ale warto o tym wiedzieć przed
   uruchomieniem na kopii roboczej z niezacommitowanymi zmianami gdzie
   indziej.

---

## Dla audytora: co dokładnie sprawdzić

Klon + wyłącznie ten dokument → uruchomić krok 6 ("Pełny obraz w jednej
komendzie") → skrypt kończy się `WSZYSTKIE GLOWNE WYNIKI ODTWORZONE
POPRAWNIE` albo rzuca `AssertionError` z dokładną wartością, która się nie
zgodziła. Brak potrzeby ręcznego porównywania liczb w konsoli — asercje w
kroku 6 są jedynym źródłem prawdy "zgadza się / nie zgadza się".

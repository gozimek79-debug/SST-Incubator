"""PC-001 K1 (kontrola surogatowa): deterministyczna permutacja pozycji
genomow w obrebie JEDNEGO bloku-seeda (23 genomy dzielace ten sam seed w
ukladzie skrzyzowanym - patrz docstring execution_package_v0_11/runners/
pc_001_confirmatory_runner.py i power_analysis_b4b.py). Zero zaleznosci od
random.Random/hash()/time/os.urandom - WYLACZNIE hashlib.sha256, ten sam
poziom kontroli odtwarzalnosci co wlasne implementacje wilcoxon_signed_rank/
mann_whitney_u/spearman_rho w statistics.py (projekt nie polega na
wewnetrznym zachowaniu bibliotek zewnetrznych/stdlib dla wielkosci, od
ktorych zalezy wynik wnioskowania).

ZLECENIE B4C-1 (05) zostawil DWIE decyzje jawnie otwarte, do wyboru,
uzasadnienia i ZGLOSZENIA (nie do cichego przyjecia domyslnej wartosci) -
obie ponizej.

======================================================================
DECYZJA 1: SHA256 -> liczba calkowita (k1_shuffle_seed, pole RAPORTOWANE)
======================================================================
k1_shuffle_seed = int.from_bytes(sha256_digest, byteorder="big") - CALY
32-bajtowy digest, big-endian, BEZ obcinania, BEZ modulo. Audytor
zademonstrowal, ze 5 roznych konwersji tego samego digestu (rozne wybory
bajtow/kolejnosci/modulo) daja 5 roznych liczb - zaden wybor nie jest
"naturalnie poprawny" bez jawnego przypiecia. Wybor CALEGO digestu
minimalizuje liczbe arbitralnych podecyzji (nie ma pytania "ktore bajty",
bo uzywane sa WSZYSTKIE 32). Ta liczba jest polem RAPORTOWANYM/
AUDYTOWALNYM (przyszly evaluator zapisuje ja jako k1_shuffle_seed) - NIE
jest wejsciem do tasowania ponizej (patrz Decyzja 2) - gdyby byla, obcinanie
do np. 64 bitow dla zgodnosci z jakims PRNG wprowadzaloby dokladnie ta
niejednoznacznosc, ktorej Decyzja 2 unika w calosci.

======================================================================
DECYZJA 2: Fisher-Yates napedzany strumieniem SHA256 (rekomendacja
audytora PRZYJETA), NIE random.Random
======================================================================
random.Random(seed).shuffle() NIE gwarantuje odtwarzalnosci MIEDZY
wersjami Pythona (projekt nie przypina wersji Pythona - brak pliku
pinning w repo). Implementacja ponizej eliminuje ta zaleznosc calkowicie:
KAZDA decyzja tasowania (indeks do zamiany, jeden na krok Fishera-Yatesa)
pochodzi z WLASNEGO, jawnego wywolania hashlib.sha256(material_ziarna +
licznik_kroku) - NIE z wewnetrznego, nieprzezroczystego stanu PRNG. Ten sam
wzorzec co reimplementacje testow statystycznych w tym projekcie (Wilcoxon/
Mann-Whitney/Spearman w statistics.py) - nie polegamy na zachowaniu
zewnetrznego/stdlib komponentu tam, gdzie od niego zalezy wynik
wnioskowania.

Odrzucenie probkowania odrzucajacego (rejection sampling): funkcja ponizej
przyjmuje n jako PARAMETR (nie zaklada z gory, ze n=23/liczba genomow) -
KTOKOLWIEK jej uzyje (dzis lub w przyszlosci) moze podac wieksze n, np.
n=EXPERIMENT_CONFIG["protocol"]["ticks_total"] (dzis 300), gdyby permutacja
mialaby dotyczyc pozycji tickow zamiast pozycji genomow. Poprawka CTO
(B4C-1 (07)): uzasadnienie ponizej NIE zaklada gornej granicy n=23 - liczone
dla gornej granicy realnie wystepujacej w tym projekcie (300, nie 23).
Mapowanie 256-bitowego bloku SHA256 na zakres [0, i] (i<300) przez modulo
daje odchylenie od jednorodnosci < 300/2^256 - wciaz astronomicznie ponizej
jakiejkolwiek mierzalnej wielkosci w tym eksperymencie (11 komorek, N=9);
rejection sampling zostal rozwazony i odrzucony jako niepotrzebna
zlozonosc dla tej skali n, NIEZALEZNIE od tego, czy n oznacza genomy czy
ticki.

======================================================================
DECYZJA 3 (umiejscowienie): NOWY, dedykowany plik - NIE wewnatrz runnera
======================================================================
pc_001_confirmatory_runner.py deklaruje explicite (docstring modulu):
"Runner NIE liczy... zero importu funkcji analizy statystycznej" - runner
zapisuje WYLACZNIE surowe dane. Permutacja K1 JEST wielkoscia
metodologiczna/inferencyjna (kontrola surogatowa dla testow K1-A/K1-B,
patrz publications/pc_001_bh_family.json) - nalezy do EVALUATORA (jeszcze
nienapisanego), nie do runnera. Ten plik jest wspolnym, testowalnym
prymitywem USTALONYM PRZED evaluatorem - ten sam wzorzec co
clos_curriculum/laboratory/statistics.py::linear_slope (B4C-2 (03)).
pc_001_confirmatory_runner.py NIE importuje tego modulu.

======================================================================
CZLONKOSTWO W CRITICAL_FILES_PC_001: CELOWO NIEOBECNY (B4C-1 (08), decyzja
CTO - REGULA OGOLNA, nie jednorazowe ustepstwo dla tego pliku)
======================================================================
Kryterium czlonkostwa w rejestrze: "czy zmiana tresci tego pliku moglaby
zmienic liczby produkowane przez eksperyment". Plik, ktorego NIC NIE
IMPORTUJE, nie moze zmienic zadnej liczby - jest NIEOSIAGALNY z
jakiegokolwiek uruchamianego dzis kodu.

CZLONKOSTWO IDZIE ZA OSIAGALNOSCIA, NIE ZA INTENCJA. Ten plik jest
docelowo trwalym prymitywem (evaluator go zaimportuje - patrz DECYZJA 3
powyzej), ale "docelowo" nie jest "dzis" - w momencie, gdy evaluator
faktycznie go zaimportuje, kryterium osiagalnosci zaczyna byc spelnione i
WTEDY plik wchodzi do rejestru (53 -> 55, razem z samym evaluatorem). Do
tego czasu jest kodem, ktory nic nie produkuje - jego nieobecnosc w
rejestrze DZIS nie jest przeoczeniem.

Precedens w tym repo: compute_noise_world_floor.py/
compute_pure_noise_world_floor.py trwale POZA rejestrem (jednorazowe,
nigdy nie importowane przez pipeline) - ale ten plik ROZNI SIE od nich:
tamte sa trwale nieosiagalne z definicji (jednorazowe skrypty), ten plik
jest DZIS nieosiagalny, ale PRZESTANIE byc, gdy evaluator powstanie.

======================================================================
WYMOG: JEDNA WSPOLNA PERMUTACJA NA BLOK-SEED (nie per genom)
======================================================================
Seed jest CZYNNIKIEM BLOKUJACYM dzielonym przez wszystkie 23 genomy w
ukladzie skrzyzowanym. Permutacja K1 tasuje POZYCJE GENOMOW w obrebie
JEDNEGO bloku - gdyby kazdy genom dostal WLASNA, niezalezna permutacje,
struktura blokowa zostalaby zniszczona (ten sam blad klasy co "seed losowany
per-genom", ostrzezony w docstringu runnera). k1_shuffle_seed i
derive_k1_permutation() ponizej sa funkcja WYLACZNIE confirmatory_seed
(NIE genome_id) - wywolanie derive_k1_permutation(seed, n) niezaleznie od
tego, dla ktorego z 23 genomow jest akurat liczone, MUSI zwrocic BITOWO
IDENTYCZNA permutacje (patrz tests/test_pc_001_k1_shuffle.py::
test_bit_identical_across_independent_calls).

TA SAMA zaleznosc od "kompletnej, identycznej siatki" co linear_slope
(statistics.py) widziana z drugiej strony: linear_slope zaklada kompletna,
identyczna siatke tickow (rowna dlugosc ticks/values, var(t)!=0);
derive_k1_permutation() zaklada kompletna, identyczna siatke GENOMOW (n
pozycji, jedna na genom, zadna brakujaca) - gdyby siatka genomow miala
braki (inna liczba genomow miedzy przebiegami tego samego seeda), nie
byloby jasne, ktora pozycja permutacji odpowiada ktoremu genomowi. Jedno
wspolne wymaganie kompletnosci siatki, dwie strony tego samego eksperymentu.
"""

import hashlib
from typing import List

K1_SHUFFLE_ALGORITHM_ID = "PC001_K1_SHUFFLE_V1"

# Separator domenowy - zapobiega kolizji z jakimkolwiek innym, przyszlym
# uzyciem hashowania zalezniego od seeda gdziekolwiek indziej w PC-001.
_SEED_MATERIAL_PREFIX = "PC001|K1|SHUFFLE|v1|"


def k1_shuffle_seed(confirmatory_seed: int) -> int:
    """Decyzja 1: caly digest SHA256, big-endian, bez obciecia/modulo. Pole
    RAPORTOWANE (audytowalne), NIE wejscie do derive_k1_permutation()."""
    material = f"{_SEED_MATERIAL_PREFIX}{confirmatory_seed}".encode("utf-8")
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest, byteorder="big")


def _stream_index(confirmatory_seed: int, step_counter: int, upper_inclusive: int) -> int:
    """Jedna decyzja Fishera-Yatesa (Decyzja 2): SHA256(material + separator +
    licznik_kroku), potraktowany jako liczba, zredukowany modulo do zakresu
    [0, upper_inclusive]. Modulo bias odrzucony jako nieistotny - patrz
    docstring modulu."""
    material = f"{_SEED_MATERIAL_PREFIX}{confirmatory_seed}|{step_counter}".encode("utf-8")
    digest = hashlib.sha256(material).digest()
    raw = int.from_bytes(digest, byteorder="big")
    return raw % (upper_inclusive + 1)


def derive_k1_permutation(confirmatory_seed: int, n: int) -> List[int]:
    """Fisher-Yates na indeksach [0..n-1], napedzany WYLACZNIE
    hashlib.sha256(material+licznik) - zero random.Random, zero hash()
    wbudowanego, zero stanu globalnego. Deterministyczna: to samo
    (confirmatory_seed, n) -> bitowo identyczny wynik przy KAZDYM wywolaniu,
    niezaleznie od tego, ile razy i w jakiej kolejnosci zostala wywolana
    wczesniej (brak wspoldzielonego stanu miedzy wywolaniami)."""
    if n < 0:
        raise ValueError(f"n musi byc >= 0, otrzymano {n!r}")
    permutation = list(range(n))
    for i in range(n - 1, 0, -1):
        j = _stream_index(confirmatory_seed, step_counter=n - 1 - i, upper_inclusive=i)
        permutation[i], permutation[j] = permutation[j], permutation[i]
    return permutation


def k1_permutation_digest(permutation: List[int]) -> str:
    """SHA256 hex digest permutacji - zapisywany obok k1_shuffle_seed jako
    dowod, KTORA permutacja faktycznie zostala uzyta (niezalezny od tego,
    czy k1_shuffle_seed/algorytm ponizej kiedys sie zmieni - digest opisuje
    WYNIK, nie proces)."""
    material = ",".join(str(x) for x in permutation).encode("utf-8")
    return hashlib.sha256(material).hexdigest()

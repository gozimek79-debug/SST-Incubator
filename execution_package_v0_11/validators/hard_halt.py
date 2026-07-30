"""BUILD-005 (Execution Package v0.11, Faza 1 Build, Architekt 2026-07-19;
AUD-001 ZAMKNIETE 2026-07-19 - patrz execution_package_v0_11/hashes/baseline_hash.txt).

Hard-Halt: jesli hash != baseline (AUD-001) -> HALT (wyjatek, NIE
warning/continue).

HISTORIA ROZBIEZNOSCI (rozwiazana): audytor podal poczatkowo sam hash
(cca6f8f9...ec935) bez definicji zakresu/algorytmu - 7 prob reprodukcji
(Core-only 4 katalogi, potem 24-plikowa rekonstrukcja wg kategorii "runtime+
World+lekcje+walidatory+prereg") nie dala zgodnosci. Audytor dostarczyl
kanoniczna specyfikacje (AUD_001_CANONICAL.txt): dokladna lista 24 sciezek +
dokladny algorytm agregacji. Nawet z ta lista, PIERWSZA proba (surowe bajty
z dysku) NIE zgadzala sie - przyczyna: `git config core.autocrlf=true` na
tym Windows-owym checkout'cie normalizuje konce linii na CRLF przy checkout,
podczas gdy AUD-001 zostal policzony na tresci znormalizowanej do LF (tak,
jak jest przechowywana w git/na Linuxie). Po normalizacji CRLF->LF PRZED
hashowaniem, hash odtwarza sie DOKLADNIE: cca6f8f933a73c1ff9ca9a3e482b966fef4c430ee50f3ed6c35137d3ab8ec935.

ALGORYTM (dokladnie wg AUD_001_CANONICAL.txt):
    h = sha256()
    for p in sorted(CRITICAL_FILES_AUD_001):
        content = read_bytes(p) z normalizacja CRLF->LF
        h.update(p.encode() + sha256(content).hexdigest().encode())
    baseline = h.hexdigest()

Normalizacja CRLF->LF jest zaimplementowana WPROST w kodzie (nie przez
wywolanie `git show`), zeby przyszly badacz mogl zweryfikowac hash z samego
katalogu roboczego, bez zaleznosci od gita/konkretnego commita - dziala
identycznie niezaleznie od platformy/ustawienia core.autocrlf.
"""

import hashlib
from pathlib import Path
from typing import List, Tuple

# --- Zakres waski (Core-only), zachowany dla wstecznej zgodnosci/referencji ---
CORE_DIRECTORIES = ["clos_brain", "clos_kernel", "genome", "birth"]

# --- AUD-001 KANONICZNE - dokladna lista 24 plikow (audytor, AUD_001_CANONICAL.txt) ---
CRITICAL_FILES_AUD_001 = [
    "clos_academy/echo_runtime.py",
    "clos_academy/lesson_L1_1.py",
    "clos_academy/lesson_L1_2.py",
    "clos_brain/runtime/__init__.py",
    "clos_brain/runtime/action.py",
    "clos_brain/runtime/homeostasis.py",
    "clos_brain/runtime/perception.py",
    "clos_brain/runtime/plasticity.py",
    "clos_brain/runtime/precision.py",
    "clos_brain/runtime/prediction.py",
    "clos_world/scenarios.py",
    "clos_world/world_runtime.py",
    "publications/preregistration_L1_1.json",
    "publications/preregistration_L1_1_ANEKS_2026-07-15_MSE_do_MAE.json",
    "publications/preregistration_L1_1_v0.8.json",
    "publications/preregistration_L1_2.json",
    "publications/preregistration_v0_10_1_population.json",
    "publications/preregistration_v0_11_0_ANEKS_2026-07-19_run_count_i_fdr.json",
    "publications/preregistration_v0_11_0_power_reproduction.json",
    "scripts/validate_artifacts.py",
    "scripts/validate_bundle_freshness.py",
    "scripts/validate_observability.py",
    "scripts/validate_panel.py",
    "scripts/validate_publication.py",
]
assert len(CRITICAL_FILES_AUD_001) == 24, f"oczekiwano 24 plikow, jest {len(CRITICAL_FILES_AUD_001)}"

# AUD-001 (2026-07-19, zweryfikowany niezaleznie): odcisk kodu, ktory
# wyprodukowal wyniki v0.11. Od 2026-07-28 NIE odtwarza sie z HEAD - przyczyna:
# PC KROK 2 (D-004/O-001) legalnie zmienil lesson_L1_1.py, lesson_L1_2.py,
# snapshot_engine.py w warstwie obserwacyjnej (addytywnie, test usuwalnosci
# przechodzi). To NIE jest usterka: kod nie jest juz tym kodem.
# Odtworzenie v0.11 wymaga: git checkout cfc15e2.
# NIE aktualizowac tej wartosci. Baseline'ow sie nie aktualizuje.
#
# PC-001 KROK 1 (2026-07-28), doprecyzowanie po KROK 0: AUD-001 zostal
# policzony algorytmem v1 (compute_files_hash - niejednoznaczna specyfikacja,
# patrz docstring tamtej funkcji: wykonawca i audytor otrzymali z niej rozne
# wyniki przy niezaleznej reprodukcji tego samego drzewa). Z tego powodu
# AUD_001_BASELINE NIE MOZE zostac dzis przeliczony algorytmem v2 i porownany
# 1:1 - takie porownanie byloby porownaniem dwoch roznych funkcji, nie
# weryfikacja tej samej wartosci. AUD-001 pozostaje REKORDEM HISTORYCZNYM
# (co dokladnie zweryfikowal audytor 2026-07-19, algorytmem v1, na komicie
# cfc15e2) - NIE wartoscia do biezacej weryfikacji. Biezaca weryfikacja
# (PC-001 i kolejne eksperymenty) uzywa wylacznie algorytmu v2
# (compute_files_hash_v2) i wlasnego, osobno nazwanego baseline'u
# (PC_001_BASELINE, ponizej) - nigdy nie nadpisuje ani nie "aktualizuje"
# AUD_001_BASELINE.
AUD_001_BASELINE = "cca6f8f933a73c1ff9ca9a3e482b966fef4c430ee50f3ed6c35137d3ab8ec935"

# --- PC-001 KROK B (D-006/D-007, 2026-07-28): CRITICAL_FILES_PC_001 ---
#
# Kryterium wlaczenia (jedno, stosowane konsekwentnie): "czy zmiana tresci
# tego pliku moglaby zmienic liczby, ktore wyprodukuje eksperyment PC-001".
# Algorytm: compute_files_hash_v2 (przypiety w KROK 0, potwierdzony niezaleznie
# przez audytora - patrz tests/test_hard_halt_hash_algorithm.py).
#
# CZESC 1 - z CRITICAL_FILES_AUD_001 (24), TAK/NIE per pozycja:
#
#   TAK (9, przeniesione do PC-001):
#     clos_academy/lesson_L1_1.py, lesson_L1_2.py - generuja L1.1/L1.2,
#       wlacznie z wywolaniem create_snapshot(prediction_error=...).
#     clos_brain/runtime/__init__.py, perception.py, plasticity.py,
#       precision.py, prediction.py - bezposredni lancuch last_input/
#       last_prediction/memory, ktory PRODUKUJE prediction_error. plasticity.py
#       zweryfikowane w kodzie: update_memory() zapisuje (prediction, error) do
#       brain.memory, ktore predict() czyta NASTEPNY tick (wazenie
#       1/(1+record.error)) - wiec wplywa na PE na kolejnych tickach, nie tylko
#       obserwuje.
#     clos_world/scenarios.py, world_runtime.py - generuja sygnal per tick
#       (last_input pochodna), tu tez trafia recurring_shock_world (K3b) i
#       pure_noise_world (K4, do dodania KROK C).
#
#   NIE (15, nie przenoszone):
#     clos_academy/echo_runtime.py - uzywane WYLACZNIE w fazie ciszy L1.1
#       (tick>=100), ktora PC-001 jawnie wylacza z analizy (L1.1 wnosi tylko
#       faze bodzca 0-99, CURRENT_SCIENTIFIC_LIMITS §8). Wykonanie sekwencyjne
#       (bodziec -> potem cisza) wyklucza wplyw wsteczny na ticki 0-99.
#     clos_brain/runtime/action.py - act()/get_action() NIGDY nie jest wolane
#       w lesson_L1_1.py/lesson_L1_2.py (zweryfikowane grepem) - petla otwarta,
#       akcja Brain nie wraca do world.step().
#     clos_brain/runtime/homeostasis.py - regulate() CZYTA
#       prediction_error_buffer[-1], ale zapisuje wylacznie do
#       energy/entropy/*_history; ani entropy, ani energy nie sa czytane przez
#       perceive()/predict() (zweryfikowane w obu plikach) - brak sciezki
#       zwrotnej do PE.
#     7x publications/preregistration_{L1_1,L1_1_ANEKS,L1_1_v0.8,L1_2,
#       v0_10_1_population,v0_11_0_ANEKS,v0_11_0_power_reproduction}.json -
#       dokumentuja PRZESZLE lekcje/re-run; progi/hipotezy w lesson_L1_1.py/
#       lesson_L1_2.py sa hardkodowane w .py, NIE wczytywane z tych JSON w
#       runtime. AUD-001 chronilo je z innego powodu (integralnosc
#       dokumentacji v0.11), poza zakresem PC-001.
#     5x scripts/validate_*.py - walidatory CI dzialajace PO powstaniu
#       wynikow; nie zasilaja obliczen.
#
# CZESC 2 - nowe pozycje wprost zlecone w KROK B:
#   clos_kernel/snapshot_engine.py - niesie prediction_error dzis,
#     prediction/input od KROK C; blad w Snapshot/create_snapshot() cicho
#     zepsulby surowe dane PC-001 bez dotykania Core.
#   4x publications/preregistration_PC_001*{.md,.json} - REKOMENDACJA CTO,
#     ZATWIERDZAM: kryterium "zmiana liczb" czytane w sensie szerszym -
#     zmiana progu/definicji w tym dokumencie zmienia DECYZJE PASS/FAIL/
#     INCONCLUSIVE (§6/§9 warunkow decyzyjnych), co jest "liczba, ktora
#     produkuje eksperyment" w praktycznym sensie (werdykt). Wlaczenie
#     WSZYSTKICH czterech (md+json dla PC-001 i Aneksu 1) zamyka dokladnie
#     luke, ktorej dotyczy ten cyk pracy: ani kanoniczny tekst, ani
#     reprezentacja maszynowa nie zmieni sie bez zlamania hasha.
#   execution_package_v0_11/runners/pipeline.py - dispatch runow +
#     jedyne miejsce wywolania enforce_hard_halt(); zmiana call-site (np.
#     wylaczenie sprawdzenia) jest DOKLADNIE tym, co Hard-Halt ma wykrywac.
#   execution_package_v0_11/validators/hard_halt.py - SAMOODWOLANIE:
#     plik definiujacy algorytm/liste/enforce_hard_halt() musi chronic sam
#     siebie, inaczej ktos mogby cicho oslabic enforce_hard_halt() (np. na
#     no-op) bez wywolania halta, bo hard_halt.py nie sprawdzalby wtedy
#     samego siebie. Ta sama luka istniala w AUD-001 (nie byl tam wlaczony) -
#     NIE naprawiam AUD-001 (zamrozony), zamykam ja tylko dla PC-001.
#
# CZESC 3 - ZNALEZISKA WYKRACZAJACE POZA JAWNE ZLECENIE (zgloszone, nie
# ukryte ani nie wlaczone milczaco) - zweryfikowane w kodzie, nie zgadywane:
#   clos_brain/brain_runtime.py - orkiestrator step()/partial_step()
#     (kolejnosc krokow, PipelineStep, _CERTIFIED_SKIPPABLE). ANI JEDEN z 24
#     plikow AUD-001 nie chronil KOLEJNOSCI wywolan (tylko poszczegolne
#     kroki osobno) - zamiana kolejnosci compute_error/predict() zmienilaby
#     sens prediction_error, i nic by tego nie zlapalo. Lukra w AUD-001,
#     zamykana tu dla PC-001.
#   clos_brain/tissue.py - BrainTissue.prediction_depth (domyslnie 3),
#     attention_threshold (0.3), meta_cognition_sensitivity (0.5) NIE sa
#     nadpisywane przez lesson_L1_1.py/lesson_L1_2.py (tylko 5 innych pol
#     jest) - potwierdzone WPROST w docstringu
#     clos_curriculum/laboratory/population.py ("BrainTissue uzywa swoich
#     wlasnych defaultow dataclass (3, 0.3, 0.5) dla KAZDEGO z 23 genomow").
#     Te 3 defaulty bezposrednio parametryzuja predict().
#   clos_curriculum/laboratory/population.py - LHS (seed=20101) generuje
#     FAKTYCZNE wartosci liczbowe dla 20 z 23 genomow (pop_000-pop_019).
#     Zmiana granic/algorytmu/seeda tutaj zmienia genomy, ktore PC-001
#     faktycznie uruchamia.
#   genome/presets.py - definiuje liczby dla 3 genomow-kotwic (default,
#     minimal, highly_plastic).
#   genome/engine.py, genome/genome.py, genome/gene.py, birth/engine.py,
#     birth/brain.py - zweryfikowany lancuch tworzacy expressed_genes:
#     create_genome() -> Genome.express_all() (genome/genome.py, uzywa
#     Gene z gene.py) -> BirthEngine.create_from_genome() (birth/engine.py)
#     -> Brain.__init__ (birth/brain.py:43, `self.expressed_genes =
#     expressed_genes` - PRZEPISANE BEZ TRANSFORMACJI, ale to WLASNIE ten
#     przepisujacy punkt trzeba chronic). birth/validator.py, certificate.py,
#     identity.py, cognitive_state.py NIE wchodza - nie transformuja
#     expressed_genes (walidacja/metadane/martwy dla lekcji CognitiveState).
#   execution_package_v0_11/runners/aggregate_results.py - TENTATYWNE TAK:
#     tu zyje fdr_correction_omnibus, jawny precedens cytowany w PC-001 §2.2.
#     Jesli PC-001 uzyje tej samej funkcji, plik nalezy do lancucha decyzji.
#
# B3 (2026-07-28): LUKA ZAMKNIETA. wilcoxon_signed_rank/kendall_tau/
# spearman_rho/mann_whitney_u dopisane do clos_curriculum/laboratory/
# statistics.py (ZERO scipy w kodzie produkcyjnym - decyzja CTO: scipy zyje
# POZA repo, wiec nie wchodzi do hasha, podbicie jego wersji nie moze cicho
# zmienic wynikow analizy; scipy jest zaleznoscia TESTOWA wylacznie, patrz
# tests/test_pc_001_statistics.py, walidacja do 1e-6). K7 (heurystyka galezi
# awaryjnej, Aneks 2) - osobny modul, clos_scientist/
# fallback_branch_diagnostic.py (to NIE jest test statystyczny). Oba pliki
# ponizej - kryteria/definicje reguly decyzyjnej nie moga sie zmienic bez
# zlamania hasha, dokladnie jak same dokumenty prerejestracji.
CRITICAL_FILES_PC_001 = [
    "birth/brain.py",
    "birth/engine.py",
    "clos_academy/lesson_L1_1.py",
    "clos_academy/lesson_L1_2.py",
    "clos_brain/brain_runtime.py",
    "clos_brain/runtime/__init__.py",
    "clos_brain/runtime/perception.py",
    "clos_brain/runtime/plasticity.py",
    "clos_brain/runtime/precision.py",
    "clos_brain/runtime/prediction.py",
    "clos_brain/tissue.py",
    "clos_curriculum/laboratory/population.py",
    "clos_curriculum/laboratory/statistics.py",
    "clos_kernel/snapshot_engine.py",
    "clos_scientist/fallback_branch_diagnostic.py",
    "clos_world/scenarios.py",
    "clos_world/world_runtime.py",
    "execution_package_v0_11/runners/aggregate_results.py",
    "execution_package_v0_11/runners/pipeline.py",
    "execution_package_v0_11/validators/hard_halt.py",
    "genome/engine.py",
    "genome/gene.py",
    "genome/genome.py",
    "genome/presets.py",
    "publications/preregistration_PC_001.json",
    "publications/preregistration_PC_001.md",
    "publications/preregistration_PC_001_ANEKS_1_2026-07-28.json",
    "publications/preregistration_PC_001_ANEKS_1_2026-07-28.md",
    # Aneks 2 (2026-07-28): T7 (galaz awaryjna predict() - srednia kroczaca
    # wejscia) + K7 (pomiar raportowany, POZA regula decyzyjna - regula
    # zostaje 9-warunkowa). Wlaczone tym samym uzasadnieniem co PC-001/Aneks 1:
    # kryteria/definicje nie moga sie zmienic bez zlamania hasha.
    "publications/preregistration_PC_001_ANEKS_2_2026-07-28.json",
    "publications/preregistration_PC_001_ANEKS_2_2026-07-28.md",
]
assert len(CRITICAL_FILES_PC_001) == 30, f"oczekiwano 30 plikow, jest {len(CRITICAL_FILES_PC_001)}"


class HardHaltError(Exception):
    """Podniesiony gdy hash nie zgadza sie z baseline - PRZERYWA natychmiast,
    nie loguje jako warning i nie kontynuuje."""


def _normalized_content_hash(path: Path) -> str:
    """sha256(zawartosc) PO normalizacji CRLF->LF - eliminuje zaleznosc od
    platformy/core.autocrlf. Plik przechowywany w git jako LF (konwencja
    tego repo) da IDENTYCZNY hash niezaleznie od tego, czy checkout jest
    Windows (CRLF na dysku) czy Linux (LF na dysku)."""
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def compute_files_hash(repo_root: Path, files: List[str]) -> str:
    """AUD-001 KANONICZNY ALGORYTM (v1 - ZAMROZONY, NIE ZMIENIAC): dla kazdego
    pliku (posortowane sciezki) -> sha256(sciezka_bytes + sha256(znormalizowana_
    zawartosc)_hex_bytes), agregowane w jeden sha256. NIE to samo co "sciezka +
    surowa zawartosc" (poprzednia, bledna implementacja) - tu zawartosc jest
    NAJPIERW haszowana OSOBNO, a jej HEX jest tym, co wchodzi do agregatu.

    PC-001 KROK 0 (2026-07-28): ten algorytm PRODUKUJE AUD_001_BASELINE i jest
    z nim NIEROZLACZNIE zwiazany - zostaje NIETKNIETY, wylacznie do reprodukcji
    historycznego baseline'u AUD-001 (git checkout cfc15e2). Ma znana, udokumentowana
    tutaj usterke specyfikacji: BRAK jawnego separatora miedzy polami (sciezka
    <-> hash tresci) i miedzy rekordami kolejnych plikow w agregacie - w praktyce
    NIE koliduje (content_hash_hex ma ZAWSZE stala dlugosc 64 znaki hex, wiec
    granica sciezka/hash jest de facto jednoznaczna), ale nie jest to JAWNIE
    wymuszone w formacie bajtow. Nowe baseline'y (PC_001_BASELINE i kolejne)
    UZYWAJA compute_files_hash_v2() ponizej, gdzie separator jest jawny.
    NIE nadpisywac tej funkcji - zmiana zachowania unicestwiper reprodukowalnosc
    AUD-001."""
    h = hashlib.sha256()
    for rel in sorted(files):
        p = repo_root / rel
        content_hash_hex = _normalized_content_hash(p)
        h.update(rel.encode("utf-8") + content_hash_hex.encode("utf-8"))
    return h.hexdigest()


def compute_files_hash_v2(repo_root: Path, files: List[str]) -> str:
    """ALGORYTM v2 - PRZYPIETY (PC-001 KROK 0, 2026-07-28), do uzytku przez
    WSZYSTKIE nowe baseline'y od PC_001_BASELINE wzwyz. Rozwiazuje 4 punkty
    niejednoznacznosci zgloszone przez audytora (rozne hashe z tego samego
    drzewa: wykonawca 8380c084..., audytor 3319e30d... przy proaudycji v1):

    1. KOLEJNOSC PLIKOW: `sorted(files)` na LITERALNYCH stringach sciezek,
       zapisanych w listach CRITICAL_FILES_* zawsze z separatorem '/'
       (POSIX-style), NIEZALEZNIE od platformy uruchomienia. Klucz sortowania
       to sam string (Python `sorted()`, domyslne porownanie leksykograficzne
       code-pointow, ASCII, wielkosc liter ma znaczenie) - NIE budujemy klucza
       z `pathlib.Path` (co wprowadzaloby zaleznosc od separatora OS-owego).

    2. NORMALIZACJA: `_normalized_content_hash()` czyta surowe bajty z dysku i
       zamienia WYLACZNIE sekwencje `\\r\\n` (CRLF) na `\\n` (LF), PRZED
       liczeniem sha256 tresci. Samotne `\\r` (stary styl Mac) NIE jest
       normalizowane - w tym repo nie wystepuje (tylko Windows CRLF / Unix
       LF); gdyby sie pojawilo, dalby inny hash na roznych platformach - poza
       zakresem tej specyfikacji, jawnie udokumentowane jako znane ograniczenie,
       nie cichy blad.

    3. TRESC vs TRESC+NAZWA: hashowana jest PARA (sciezka, hash tresci) per
       plik, NIE sama tresc. Hash agregatu jest wiec wrazliwy na PRZENIESIENIE
       pliku (ta sama tresc, inna sciezka -> inny hash agregatu) - to
       ZAMIERZONE: baseline identyfikuje dokladny zestaw {sciezka: tresc}, nie
       tylko multiset samych tresci (przeniesienie pliku bez zmiany tresci
       nadal jest zmiana, ktora Hard-Halt ma wykryc).

    4. SEPARATOR (poprawka v1 -> v2): miedzy sciezka a hex-hashem tresci ORAZ
       miedzy kompletnym rekordem jednego pliku a nastepnym wstawiany jest
       jawny bajt NUL (b"\\x00"). NUL nie moze wystapic ani w sciezce
       zakodowanej UTF-8, ani w hex-digescie (0-9a-f), wiec KAZDY rekord ma
       jednoznaczne granice pol - usuwa to (nawet czysto teoretyczne) ryzyko
       kolizji typu "ab"+"c" == "a"+"bc" przy konkatenacji zmiennodlugosciowych
       sciezek bez separatora.

    FORMULA (dokladnie):
        h = sha256()
        for rel in sorted(files):
            content_hash_hex = sha256(normalize_crlf_to_lf(read_bytes(rel))).hexdigest()
            h.update(rel.encode("utf-8"))
            h.update(b"\\x00")
            h.update(content_hash_hex.encode("utf-8"))
            h.update(b"\\x00")
        baseline = h.hexdigest()

    Test poprawnosci: tests/test_hard_halt_hash_algorithm.py zawiera DRUGA,
    NIEZALEZNA (nie wywolujaca tej funkcji) implementacje tej samej formuly na
    malym, recznie sprawdzalnym zestawie plikow - obie MUSZA dac ten sam wynik.
    """
    h = hashlib.sha256()
    for rel in sorted(files):
        p = repo_root / rel
        content_hash_hex = _normalized_content_hash(p)
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(content_hash_hex.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def compute_core_hash(repo_root: Path, core_dirs: List[str] = None) -> str:
    """ZACHOWANE dla referencji/wstecznej zgodnosci - Core-only (4 katalogi),
    STARY algorytm (sciezka+surowa zawartosc, bez normalizacji CRLF). NIE
    jest to AUD-001 - tylko punkt odniesienia z wczesniejszej iteracji."""
    core_dirs = core_dirs or CORE_DIRECTORIES
    files: List[Path] = []
    for d in core_dirs:
        base = repo_root / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts:
                files.append(p)

    h = hashlib.sha256()
    for p in sorted(files, key=lambda x: x.relative_to(repo_root).as_posix()):
        rel = p.relative_to(repo_root).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(p.read_bytes())
    return h.hexdigest()


def check_critical_files_hash(repo_root: Path, baseline: str,
                               files: List[str] = None) -> Tuple[bool, str]:
    """Zwraca (matches, current_hash) dla zakresu AUD-001 (24 pliki krytyczne,
    domyslnie CRITICAL_FILES_AUD_001, algorytm kanoniczny). NIE podnosi
    wyjatku - to robi enforce_hard_halt()."""
    files = files if files is not None else CRITICAL_FILES_AUD_001
    current = compute_files_hash(repo_root, files)
    return current == baseline, current


def enforce_hard_halt(repo_root: Path, baseline: str = AUD_001_BASELINE,
                       files: List[str] = None) -> str:
    """BUILD-005: jesli hash != baseline -> HardHaltError (HALT), nie warning.
    DOMYSLNIE uzywa AUD-001 (24 pliki krytyczne, algorytm kanoniczny).
    Zwraca current_hash gdy zgodny."""
    matches, current = check_critical_files_hash(repo_root, baseline, files)
    if not matches:
        raise HardHaltError(
            f"HARD-HALT: hash plikow krytycznych ({current}) != baseline ({baseline}). "
            f"Jeden z 24 plikow krytycznych (runtime/World/lekcje/walidatory/prereg) "
            f"zostal zmieniony wzgledem zatwierdzonego baseline'u AUD-001 - "
            f"wykonanie PRZERWANE, nie kontynuowane."
        )
    return current


# UWAGA (samoodwolanie, znalezione przy liczeniu hasha): hard_halt.py jest
# TERAZ czloniem WLASNEGO CRITICAL_FILES_PC_001 (patrz uzasadnienie wyzej -
# "kto pilnuje strazy"). To oznacza, ze WARTOSC baseline'u NIE MOZE byc
# zapisana jako literal w tym pliku - kazdy taki zapis zmienia hash SAMEGO
# SIEBIE, co czyni PC_001_BASELINE niestabilnym (zaobserwowane empirycznie:
# pierwsza probe wpisania stalej dala hash A, po wpisaniu hash pliku sie
# zmienil na B, co uniewazniło A). Rozwiazanie: wartosc baseline'u zyje
# WYLACZNIE w oddzielnym, NIE-hashowanym pliku
# execution_package_v0_11/hashes/pc_001_baseline_hash.txt (dokladnie ten sam
# wzorzec co execution_package_v0_11/hashes/baseline_hash.txt dla AUD-001 -
# ten plik rowniez NIE jest czlonem CRITICAL_FILES_AUD_001). `baseline` w
# funkcjach ponizej jest WYMAGANYM parametrem (bez domyslnej wartosci) -
# wolujacy (przyszly runner PC) czyta go z tamtego pliku, nigdy z literalu
# w tym module.
def check_critical_files_hash_v2(repo_root: Path, baseline: str,
                                  files: List[str] = None) -> Tuple[bool, str]:
    """Jak check_critical_files_hash, ale algorytmem v2 (compute_files_hash_v2)
    i domyslnym zakresem CRITICAL_FILES_PC_001 - dla PC-001 i kolejnych
    eksperymentow. NIE mieszac z v1/AUD-001 (rozne algorytmy, rozne listy).
    `baseline` BEZ domyslnej wartosci - patrz uwaga o samoodwolaniu powyzej."""
    files = files if files is not None else CRITICAL_FILES_PC_001
    current = compute_files_hash_v2(repo_root, files)
    return current == baseline, current


def enforce_hard_halt_v2(repo_root: Path, baseline: str,
                          files: List[str] = None) -> str:
    """Odpowiednik enforce_hard_halt() dla przebiegow PC (i kolejnych
    eksperymentow uzywajacych algorytmu v2) - CRITICAL_FILES_PC_001, NIE
    AUD_001_BASELINE/CRITICAL_FILES_AUD_001. `baseline` MUSI byc podany
    jawnie przez wolujacego (czytany z
    execution_package_v0_11/hashes/pc_001_baseline_hash.txt) - brak
    domyslnej wartosci CELOWO (patrz uwaga o samoodwolaniu powyzej). Uzyc tej
    funkcji (nie enforce_hard_halt()) w kazdym runnerze PC-001 -
    enforce_hard_halt() zostaje zarezerwowany wylacznie dla v0.11/AUD-001."""
    files = files if files is not None else CRITICAL_FILES_PC_001
    matches, current = check_critical_files_hash_v2(repo_root, baseline, files)
    if not matches:
        raise HardHaltError(
            f"HARD-HALT (PC, v2): hash plikow krytycznych ({current}) != baseline "
            f"({baseline}). Jeden z {len(files)} plikow krytycznych PC-001 zostal "
            f"zmieniony wzgledem zatwierdzonego baseline'u PC_001_BASELINE - "
            f"wykonanie PRZERWANE, nie kontynuowane."
        )
    return current


def check_stable_world_disjoint_seeds(package_root: Path) -> None:
    """AUD-004: cross-lesson contamination = 0 dla stable_world - seedy
    L1.1 i L1.2 musza byc rozlaczne (zero czesci wspolnej)."""
    import json

    l11 = json.loads((package_root / "environments" / "stable_world" / "L1_1_pattern_echo" / "seed_policy.json").read_text(encoding="utf-8"))
    l12 = json.loads((package_root / "environments" / "stable_world" / "L1_2_shock_recovery" / "seed_policy.json").read_text(encoding="utf-8"))

    def _parse_range(expr: str) -> set:
        # "range(1, 94)" -> range object -> set
        inner = expr[expr.index("(") + 1: expr.index(")")]
        lo, hi = (int(x.strip()) for x in inner.split(","))
        return set(range(lo, hi))

    seeds_l11 = _parse_range(l11["seeds"])
    seeds_l12 = _parse_range(l12["seeds"])
    overlap = seeds_l11 & seeds_l12
    if overlap:
        raise HardHaltError(
            f"AUD-004 FAIL: seedy stable_world L1.1/L1.2 NAKLADAJA SIE ({sorted(overlap)[:5]}...) "
            f"- kontaminacja miedzy-lekcyjna wykryta, oczekiwano zbioru pustego."
        )
    if len(seeds_l11) + len(seeds_l12) != 185:
        raise HardHaltError(
            f"AUD-004 FAIL: suma seedow stable_world = {len(seeds_l11) + len(seeds_l12)}, oczekiwano 185."
        )

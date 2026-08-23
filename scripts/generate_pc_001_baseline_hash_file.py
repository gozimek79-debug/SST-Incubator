"""Generator execution_package_v0_11/hashes/pc_001_baseline_hash.txt.

PROBLEM (zgloszenie trzeciego audytora, B5-00): ten plik przechowywal WLASNA,
recznie utrzymywana kopie listy CRITICAL_FILES_PC_001 - 51 pozycji, podczas
gdy autorytatywna lista w execution_package_v0_11/validators/hard_halt.py ma
52 (brakowalo execution_package_v0_11/runners/pc_001_confirmatory_runner.py,
dodanego w B4C-01/03/04). Plik przedstawial sie w naglowku jako "51 PLIKOW
KRYTYCZNYCH (posortowane, dokladnie w tej kolejnosci uzyte w hashu)" - czyli
zapraszal do policzenia baseline'u B5 z TEJ listy. Gdyby ktos tak zrobil,
PC_001_BASELINE zostalby zamrozony bez runnera, ktory faktycznie produkuje
dane eksperymentu - dokladnie ten scenariusz, dla ktorego istnieje bramka B4c.

ROZWIAZANIE: ten sam wzorzec co scripts/spec_md_to_json.py i
scripts/generate_artifacts_index.py - plik pochodny GENEROWANY z jedynego
zrodla prawdy (tu: CRITICAL_FILES_PC_001), nigdy edytowany recznie. Reczna
synchronizacja dwoch list jest PRZYCZYNA tego bledu, nie lekiem na niego -
stad generator, nie jednorazowa poprawka liczby/wiersza.

CO JEST GENEROWANE, CO ZOSTAJE STATYCZNE: liczba w naglowku
("N PLIKOW KRYTYCZNYCH") i sama lista sciezek - generowane z
CRITICAL_FILES_PC_001. Cala reszta prozy (STATUS/POWOD/ALGORYTM/STATUS LISTY,
w tym liczby HISTORYCZNE takie jak "47->49->51") to zapis decyzji podjetych
w przeszlosci - opis wzrostu, nie stan biezacy - i zostaje statyczna tresc
tego skryptu, identyczna z dotychczasowa zawartoscia pliku.

KOLEJNOSC LISTY: sorted(CRITICAL_FILES_PC_001), NIE kolejnosc deklaracji w
hard_halt.py (ktora jest chronologiczna/narracyjna, nie posortowana).
compute_files_hash_v2() sortuje sciezki literalnie PRZED haszowaniem (patrz
jej docstring, punkt 1) - zapis w tym pliku ma pokazywac czlowiekowi
DOKLADNIE te kolejnosc, w ktorej hash faktycznie liczy pliki, nie kolejnosc
deklaracji w kodzie.

Uzycie: python scripts/generate_pc_001_baseline_hash_file.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from execution_package_v0_11.validators.hard_halt import CRITICAL_FILES_PC_001  # noqa: E402

OUT_PATH = REPO_ROOT / "execution_package_v0_11" / "hashes" / "pc_001_baseline_hash.txt"

HEADER_BLOCK = """# PC-001 - PC_001_BASELINE
#
# STATUS: TBD - CELOWO NIEPOLICZONY JESZCZE (decyzja CTO/audytora, 2026-07-28,
# zmiana kolejnosci KROK B).
#
# POWOD: CRITICAL_FILES_PC_001 (lista ponizej) jest ZATWIERDZONA co do
# CZLONKOSTWA i UZASADNIENIA per pozycja, ale "znana luka" wciaz otwarta w
# momencie zatwierdzenia listy: kod liczacy testy statystyczne reguly
# decyzyjnej (Wilcoxon par, Kendall tau, Spearman, Mann-Whitney, BH-FDR) NIE
# ISTNIEJE jeszcze w repo. Ten kod TEZ wejdzie do CRITICAL_FILES_PC_001 (KROK
# B3), zanim eksperyment ruszy. Gdyby baseline zostal policzony TERAZ (przed
# B2/B3/B4), zostalby natychmiast uniewazniony przez dopisanie pliku analizy -
# czyli i tak trzeba by go policzyc DRUGI raz, a pierwsza wartosc nigdy nie
# zostalaby do niczego uzyta. Zamiast tego: NAJPIERW caly pipeline (Snapshot
# prediction/input + pure_noise_world w B2, kod analizy zwalidowany przeciw
# scipy w B3, analiza mocy w B4), POTEM jeden, ostateczny PC_001_BASELINE
# (B5) pokrywajacy RAZEM generowanie danych I analize - nie tylko dane.
#
# Do czasu B5: enforce_hard_halt_v2() NIE MA wartosci domyslnej dla baseline
# (funkcja wymaga jawnego przekazania - patrz hard_halt.py) - wiec nic nie
# moze przypadkiem polegac na tej niepolieczonej jeszcze wartosci.
#
# GDY B5 policzy finalna wartosc, ten plik zostanie zaktualizowany (NIE
# cichym nadpisaniem - z data i odnotowaniem, ze to jest wartosc POKRYWAJACA
# caly pipeline, nie tylko dane wykonawcze) i wartosc trafi tutaj, w formacie
# identycznym jak w baseline_hash.txt (AUD-001).
#
# ALGORYTM (juz przypiety i potwierdzony, nie zmieni sie do B5): v2
# (execution_package_v0_11/validators/hard_halt.py::compute_files_hash_v2),
# przypiety w PC-001 KROK 0, potwierdzony niezaleznie przez audytora na
# malym, recznie sprawdzalnym przykladzie (patrz
# tests/test_hard_halt_hash_algorithm.py). Rozni sie od algorytmu v1 uzytego
# przez AUD_001_BASELINE (jawny separator NUL miedzy polami/rekordami) - NIE
# porownywac tych dwoch wartosci 1:1. Powod, dla ktorego wartosc baseline
# NIGDY nie bedzie literalem wewnatrz hard_halt.py (nawet po B5): ten plik
# jest CZLONEM WLASNEJ listy CRITICAL_FILES_PC_001 (patrz uzasadnienie
# nizej) - zapisanie wartosci jako stalej W NIM zmienialoby jego wlasny hash
# przy kazdym wpisaniu (zaobserwowane empirycznie przy pierwszej probie tego
# baseline'u - pierwsza wpisana wartosc uniewazniala sama siebie). Wartosc
# zyje WYLACZNIE tutaj, w pliku, ktory NIE jest czlonem CRITICAL_FILES_PC_001.
#"""

MID_BLOCK = """# kryterium wlaczenia: "czy zmiana tresci tego pliku moglaby zmienic liczby,
# ktore wyprodukuje eksperyment PC-001" - uzasadnienie per pozycja w
# execution_package_v0_11/validators/hard_halt.py, komentarz nad
# CRITICAL_FILES_PC_001. Rozszerzone 2026-07-28 o B3 (kod analizy statystycznej),
# B4a (NOTATKA_B4_ANALIZA_MOCY), W2/V-C dokumenty (D-018: Aneks 3, specyfikacja
# W2, analiza floor_env vs floor(t)), W2 KOD (floor_model.py, w2_endpoint.py,
# pc_001_experiment_config.py - liczy/stosuje endpoint, nie tylko go opisuje;
# compute_noise_world_floor.py CELOWO wykluczony - jednorazowy runner
# wyznaczajacy wartosc, nie kod stosowany w eksperymencie, decyzja CTO),
# zamkniecie fazy projektowania (D-019, 2026-07-28): W2 Completion Report i
# docs/GOVERNANCE_RULES.md (O-001/G-001/G-002/D-017 wiazace), Aneks 4
# (D-026, 2026-07-28): status K3b ARCHITECTURE-LIMITED, oraz Aneks 5
# (D-025D, 2026-07-28): K3a warunek 2 SUSPENDED PENDING WINDOW REDEFINITION.
# Rozszerzone 2026-08-04 (D-031, 47->49, przed B5): SPRINT_v0.11.0.md
# (dyrektywa cytowana przez 4 czlonkow rejestru - oba protokoly lekcji, testy
# statystyczne reguly decyzyjnej, definicje srodowisk) oraz
# publications/BEZPIECZENSTWO_POMIARU_recovery_spearman.md (jedyne zapisane
# uzasadnienie zakazu pomiarowego recovery_i, dotyczy zakresu Pilota Final) -
# oba bez pary .json, wzorem NOTATKA_B4_ANALIZA_MOCY (proza, zaden kod nie
# parsuje). Rozszerzone 2026-08-04 (Aneks 6, 49->51, po niezaleznej weryfikacji
# warunku zamrozenia z §7 aneksu, zlecenie Z1 - 276 przebiegow, pamiec nigdy
# nie oprozniona ponizej jednego rekordu po ticku 0): K7 -> Typ M (przedmiot
# G-005: CORE), T7 przeredagowane, korekta mechanizmu wobec Aneksu 5 (Aneks 5
# NIE nadpisany). Z para .json, wzorem Aneksow 1-5. Rozszerzone 2026-08-22
# (B4C-01/03/04, 51->52, przed B5): runner Eksperymentu Konfirmacyjnego PC-001 -
# kod WYKONYWANY przy kazdym przebiegu konfirmacji (generuje surowe trajektorie
# prediction_error), w odroznieniu od pilotow/runnerow podlog (dane WEJSCIOWE
# do decyzji projektowej, nie kod stosowany w eksperymencie):"""

FOOTER_BLOCK = """#
# Obliczenie WARTOSCI INTERIM (nie do porownania z niczym - baseline jest
# TBD, to tylko podglad, ile biezacy zestaw daje DZIS, do wewnetrznego
# sledzenia postepu, NIE do zamrozenia):
#   python -c "
#   import sys; sys.path.insert(0, 'execution_package_v0_11')
#   from pathlib import Path
#   from validators.hard_halt import compute_files_hash_v2, CRITICAL_FILES_PC_001
#   print(compute_files_hash_v2(Path('.'), CRITICAL_FILES_PC_001))
#   "
#
# STATUS LISTY: B2 (Snapshot prediction/input + pure_noise_world) dotyczyl
# juz obecnych plikow (snapshot_engine.py, scenarios.py) - bez nowych pozycji.
# B3 (kod analizy statystycznej: clos_curriculum/laboratory/statistics.py
# rozszerzone o wilcoxon_signed_rank/kendall_tau/spearman_rho/mann_whitney_u,
# + nowy modul clos_scientist/fallback_branch_diagnostic.py dla K7) DODAL 2
# pozycje - LUKA ZAMKNIETA, lista byla wtedy KOMPLETNA co do wiedzy z tamtego
# dnia. B4 (analiza mocy) NIE wymagal nowych plikow (uzywa funkcji z tego
# samego statistics.py). B4C-01 (runner konfirmacyjny) DODAL 1 pozycje -
# patrz uzasadnienie w hard_halt.py nad CRITICAL_FILES_PC_001 oraz
# SPECYFIKACJA_KANONICZNA_PC_001.md §2.12."""


def render() -> str:
    n = len(CRITICAL_FILES_PC_001)
    count_line = (
        f"# {n} PLIKOW KRYTYCZNYCH (posortowane, dokladnie w tej kolejnosci "
        "uzyte w hashu),"
    )
    file_lines = "\n".join(sorted(CRITICAL_FILES_PC_001))
    return "\n".join([HEADER_BLOCK, count_line, MID_BLOCK, file_lines, FOOTER_BLOCK]) + "\n"


def main() -> int:
    OUT_PATH.write_text(render(), encoding="utf-8")
    print(f"zapisano: {OUT_PATH} ({len(CRITICAL_FILES_PC_001)} plikow)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

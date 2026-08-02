"""PC-001 KROK B (D-006/D-007, 2026-07-28): CRITICAL_FILES_PC_001 +
PC_001_BASELINE - registro chroniacy prerejestracje PC-001 przed dryfem
PRZED powstaniem jakichkolwiek danych PC.

Ten plik dowodzi:
1. Wszystkie 45 plikow z CRITICAL_FILES_PC_001 (26 + Aneks 2: T7/K7 + B3: kod
   analizy statystycznej + B4a: NOTATKA_B4_ANALIZA_MOCY + W2/V-C (D-018):
   dokumenty (Aneks 3 + specyfikacja W2 + analiza floor_env vs floor(t)) +
   kod (floor_model.py, w2_endpoint.py, pc_001_experiment_config.py) +
   zamkniecie fazy projektowania (D-019): W2 Completion Report +
   docs/GOVERNANCE_RULES.md + Aneks 4 (D-026): status K3b
   ARCHITECTURE-LIMITED, 2026-07-28) istnieja i sa czytelne.
2. PC_001_BASELINE jest CELOWO TBD (nie policzony jeszcze) - decyzja CTO,
   zmiana kolejnosci KROK B: baseline ma pokryc RAZEM generowanie danych I
   kod analizy statystycznej (ten drugi jeszcze nie istnieje - B3), wiec
   liczenie go teraz oznaczaloby policzenie go dwa razy. Test pilnuje, ze
   plik rejestru jawnie mowi TBD, a nie zawiera przypadkowej/przedwczesnej
   wartosci, ktora ktos mogby pomylic z ostatecznym baseline'em.
3. hard_halt.py NIE zawiera literalu "PC_001_BASELINE =" (regresja
   samoodwolania: hard_halt.py jest CZLONEM WLASNEJ listy krytycznych
   plikow, wiec zapisanie wartosci baseline'u jako stalej W TYM PLIKU
   zmienialoby jego wlasny hash przy kazdym zapisie - zaobserwowane
   empirycznie przy tworzeniu tego baseline'u. Test pilnuje, zeby nikt
   przypadkiem nie cofnal tej poprawki).
4. enforce_hard_halt_v2() HALTuje na blednym baseline (negatywny test) i
   przechodzi, gdy podany baseline zgadza sie z biezacym stanem plikow
   (pozytywny test, na WARTOSCI POLICZONEJ W TESCIE, nie na zamrozonej
   stalej - bo zamrozonej stalej jeszcze nie ma) - z jawnie podanym baseline
   (funkcja NIE MA wartosci domyslnej, celowo).
"""

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "execution_package_v0_11"))
from validators.hard_halt import (
    compute_files_hash_v2,
    CRITICAL_FILES_PC_001,
    enforce_hard_halt_v2,
    HardHaltError,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_FILE = REPO_ROOT / "execution_package_v0_11" / "hashes" / "pc_001_baseline_hash.txt"
HARD_HALT_PY = REPO_ROOT / "execution_package_v0_11" / "validators" / "hard_halt.py"


class TestCriticalFilesPC001Exist:

    def test_all_45_files_exist(self):
        assert len(CRITICAL_FILES_PC_001) == 45
        missing = [f for f in CRITICAL_FILES_PC_001 if not (REPO_ROOT / f).exists()]
        assert not missing, f"pliki z CRITICAL_FILES_PC_001 nie istnieja: {missing}"

    def test_no_duplicates(self):
        assert len(CRITICAL_FILES_PC_001) == len(set(CRITICAL_FILES_PC_001))


class TestPC001BaselineIsExplicitlyTBD:
    """Baseline jest CELOWO niepolieczony (decyzja CTO, zmiana kolejnosci
    KROK B) - policzenie go teraz zostaloby uniewaznione przez B3 (kod
    analizy statystycznej jeszcze nie istnieje). Ten test pilnuje, zeby
    rejestr NIE zawieral przypadkowej wartosci wygladajacej jak gotowy hash."""

    def test_registry_file_explicitly_states_tbd(self):
        content = BASELINE_FILE.read_text(encoding="utf-8")
        assert "STATUS: TBD" in content, (
            "pc_001_baseline_hash.txt nie zawiera jawnego 'STATUS: TBD' - "
            "jesli baseline zostal juz policzony, ten test i jego docstring "
            "trzeba zaktualizowac swiadomie (krok B5), nie usunac po cichu"
        )

    def test_registry_file_does_not_contain_a_bare_64_char_hex_baseline_line(self):
        """Zabezpieczenie przed przypadkowym wklejeniem gotowego hasha (linia
        skladajaca sie WYLACZNIE z 64 znakow hex) zanim B5 formalnie go
        zatwierdzi."""
        import re
        for line in BASELINE_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert not re.fullmatch(r"[0-9a-f]{64}", stripped), (
                f"znaleziono linie wygladajaca jak gotowy sha256 baseline "
                f"({stripped[:16]}...) w pliku, ktory powinien byc TBD"
            )


class TestNoSelfReferentialLiteral:
    """Regresja bledu bootstrappingu znalezionego przy tworzeniu tego
    baseline'u: hard_halt.py jest czlonem WLASNEJ listy krytycznych plikow,
    wiec NIE MOZE zawierac literalu wartosci PC_001_BASELINE - taki zapis
    zmienia hash samego siebie przy kazdej probie ustalenia wartosci."""

    def test_hard_halt_py_does_not_embed_pc_001_baseline_literal(self):
        content = HARD_HALT_PY.read_text(encoding="utf-8")
        assert "PC_001_BASELINE =" not in content, (
            "hard_halt.py zawiera przypisanie 'PC_001_BASELINE = ...' - to "
            "reintrodukuje samoodwolanie (plik nalezy do wlasnej listy "
            "krytycznej), ktore uczynilo pierwsza probe tego baseline'u "
            "niestabilna. Wartosc MUSI zyc wylacznie w "
            "pc_001_baseline_hash.txt (poza CRITICAL_FILES_PC_001)."
        )


class TestEnforceHardHaltV2:

    def test_halts_on_wrong_baseline(self):
        with pytest.raises(HardHaltError):
            enforce_hard_halt_v2(REPO_ROOT, baseline="0" * 64)

    def test_passes_on_correct_baseline(self):
        """Baseline zamrozony jeszcze nie istnieje (TBD, patrz
        TestPC001BaselineIsExplicitlyTBD) - test liczy wartosc INLINE, z
        biezacego stanu plikow, wylacznie zeby dowiesc, ze
        enforce_hard_halt_v2 przechodzi, gdy podana wartosc faktycznie
        zgadza sie z tym, co jest na dysku (nie jest to test na zamrozona,
        zatwierdzona stala - tej jeszcze nie ma)."""
        current = compute_files_hash_v2(REPO_ROOT, CRITICAL_FILES_PC_001)
        result = enforce_hard_halt_v2(REPO_ROOT, baseline=current)
        assert result == current

    def test_baseline_has_no_default_value(self):
        """Sprawdza, ze funkcja wymusza jawne podanie baseline (brak
        domyslnej wartosci) - inaczej ktos moglby (przez pomylke) polegac
        na nieistniejacym, ukrytym domyslnym baseline'ie."""
        import inspect
        sig = inspect.signature(enforce_hard_halt_v2)
        assert sig.parameters["baseline"].default is inspect.Parameter.empty

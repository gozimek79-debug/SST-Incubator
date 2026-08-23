"""Gwarancja: execution_package_v0_11/hashes/pc_001_baseline_hash.txt jest
GENEROWANY z CRITICAL_FILES_PC_001, nie recznie utrzymywana kopia.

ZGLOSZENIE (trzeci audytor, B5-00, 2026-08-22): plik zawieral wlasna kopie
listy - 51 pozycji, podczas gdy CRITICAL_FILES_PC_001 (hard_halt.py) ma 52
(brakowalo execution_package_v0_11/runners/pc_001_confirmatory_runner.py).
Naglowek pliku przedstawial te 51 pozycji jako "dokladnie w tej kolejnosci
uzyte w hashu" - gdyby B5 policzyl PC_001_BASELINE z tej listy zamiast z
CRITICAL_FILES_PC_001, zamrozony zestaw pominalby kod faktycznie
produkujacy dane eksperymentu, a hash 51 plikow bylby POPRAWNYM hashem -
tylko nie tego zestawu, o ktorym mysli protokol. Blad bylby niewykrywalny
przez sam mechanizm Hard-Halt.

DLACZEGO KOLEJNOSC JEST CZESCIA GWARANCJI: compute_files_hash_v2() sortuje
sciezki literalnie (sorted()) PRZED haszowaniem (patrz jej docstring, punkt
1) - zapis w pliku ma pokazywac DOKLADNIE te kolejnosc, nie kolejnosc
deklaracji w hard_halt.py (ktora jest narracyjna/chronologiczna).

Konwencja projektu: kazdy test pozytywny ma test negatywny obok. Tu trzy
negatywy, tak jak zazadano - brakujaca pozycja, nadmiarowa pozycja, ta sama
zawartosc w innej kolejnosci - kazdy zbudowany na SYNTETYCZNYCH listach
(nie przez psucie prawdziwego pliku na dysku), zeby test byl czytelny i nie
zostawial za soba brudnego stanu repo.
"""

from pathlib import Path

from execution_package_v0_11.validators.hard_halt import CRITICAL_FILES_PC_001
from scripts.generate_pc_001_baseline_hash_file import render, OUT_PATH

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_FILE = REPO_ROOT / "execution_package_v0_11" / "hashes" / "pc_001_baseline_hash.txt"


def parse_file_list(text: str) -> list:
    """Wyciaga same sciezki plikow - linie, ktore NIE zaczynaja sie od '#'
    i nie sa puste. Zero interpretacji tresci prozy nad/pod lista."""
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def verify_file_list_matches_registry(file_list: list, registry: list) -> list:
    """Zwraca liste problemow (pusta = OK). Rozroznia trzy rodzaje bledu,
    zeby komunikat od razu mowil, ktory z nich to jest."""
    expected = sorted(registry)
    if file_list == expected:
        return []
    missing = sorted(set(expected) - set(file_list))
    extra = sorted(set(file_list) - set(expected))
    problems = []
    if missing:
        problems.append(f"brakuje w pliku: {missing}")
    if extra:
        problems.append(f"nadmiarowe w pliku: {extra}")
    if not missing and not extra:
        problems.append(
            "ta sama zawartosc co CRITICAL_FILES_PC_001, ale inna kolejnosc "
            "niz sorted(CRITICAL_FILES_PC_001) - compute_files_hash_v2 sortuje "
            "przed haszowaniem, wiec plik ma pokazywac te kolejnosc"
        )
    return problems


class TestGeneratorReadsAuthoritativeRegistry:
    """Dowod, ze generator NIE ma wlasnej, drugiej listy zaszytej w kodzie -
    importuje CRITICAL_FILES_PC_001 wprost z hard_halt.py."""

    def test_generator_module_imports_critical_files_pc_001_by_name(self):
        import inspect
        import scripts.generate_pc_001_baseline_hash_file as gen
        source = inspect.getsource(gen)
        assert "from execution_package_v0_11.validators.hard_halt import CRITICAL_FILES_PC_001" in source

    def test_rendered_output_writes_to_the_real_baseline_file_path(self):
        assert OUT_PATH == BASELINE_FILE


class TestCommittedFileMatchesRegeneration:
    """Wzorzec identyczny z scripts/validate_canonical_spec.py (test 6):
    regeneruj w pamieci i porownaj strukturalnie z zacommitowanym plikiem -
    nie hash osadzony w pliku. Jesli ten test pada, ktos edytowal
    pc_001_baseline_hash.txt recznie zamiast przez generator."""

    def test_committed_file_equals_fresh_render(self):
        assert BASELINE_FILE.read_text(encoding="utf-8") == render()


class TestFileListMatchesRegistryContentAndOrder:

    def test_positive_real_file_matches_real_registry(self):
        file_list = parse_file_list(BASELINE_FILE.read_text(encoding="utf-8"))
        problems = verify_file_list_matches_registry(file_list, CRITICAL_FILES_PC_001)
        assert problems == []

    def test_positive_count_equals_len_critical_files(self):
        file_list = parse_file_list(BASELINE_FILE.read_text(encoding="utf-8"))
        assert len(file_list) == len(CRITICAL_FILES_PC_001) == 53

    def test_negative_a_missing_entry_is_caught(self):
        expected = sorted(CRITICAL_FILES_PC_001)
        file_list_missing_one = expected[:-1]  # brakuje ostatniej pozycji posortowanej listy
        problems = verify_file_list_matches_registry(file_list_missing_one, CRITICAL_FILES_PC_001)
        assert problems != []
        assert any("brakuje w pliku" in p for p in problems)

    def test_negative_b_extra_entry_is_caught(self):
        expected = sorted(CRITICAL_FILES_PC_001)
        file_list_with_extra = expected + ["clos_brain/nieistniejacy_plik_do_testu.py"]
        problems = verify_file_list_matches_registry(file_list_with_extra, CRITICAL_FILES_PC_001)
        assert problems != []
        assert any("nadmiarowe w pliku" in p for p in problems)

    def test_negative_c_same_content_different_order_is_caught(self):
        expected = sorted(CRITICAL_FILES_PC_001)
        reversed_order = list(reversed(expected))
        assert set(reversed_order) == set(expected)  # dowod, ze to naprawde ta sama zawartosc
        assert reversed_order != expected  # dowod, ze kolejnosc faktycznie inna
        problems = verify_file_list_matches_registry(reversed_order, CRITICAL_FILES_PC_001)
        assert problems != []
        assert any("kolejnosc" in p for p in problems)


class TestHeaderCountIsComputedNotWritten:
    """Naglowek MA pochodzic z len(CRITICAL_FILES_PC_001), nie byc wpisanym
    literalem w skrypcie generatora (inaczej ten sam blad odtworzylby sie
    przy nastepnym dopisaniu pliku do rejestru)."""

    def test_generator_source_has_no_hardcoded_file_count_literal(self):
        import inspect
        import scripts.generate_pc_001_baseline_hash_file as gen
        source = inspect.getsource(gen.render)
        assert "len(CRITICAL_FILES_PC_001)" in source
        assert "53" not in source
        assert "52" not in source
        assert "51" not in source

    def test_header_line_in_committed_file_uses_current_len(self):
        n = len(CRITICAL_FILES_PC_001)
        header_line = f"# {n} PLIKOW KRYTYCZNYCH (posortowane, dokladnie w tej kolejnosci uzyte w hashu),"
        assert header_line in BASELINE_FILE.read_text(encoding="utf-8")

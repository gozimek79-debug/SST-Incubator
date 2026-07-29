"""PC-001 KROK 0 (D-006, 2026-07-28): algorytm hashowania rejestru krytycznych
plikow musi byc JEDNOZNACZNY, zanim jakikolwiek baseline (PC_001_BASELINE i
kolejne) zostanie ustalony. Wykonawca i audytor policzyli rozne hashe z tego
samego drzewa dla algorytmu v1 (8380c084... vs 3319e30d...) - dowod, ze
specyfikacja byla niedopieta (brak jawnego separatora miedzy polami/rekordami).

Ten plik dowodzi dwoch rzeczy o algorytmie v2 (compute_files_hash_v2):
1. Druga, NIEZALEZNA implementacja (nie wywolujaca hard_halt.py) tej samej
   formuly daje DOKLADNIE ten sam wynik na tym samym zestawie plikow.
2. Maly, recznie sprawdzalny przyklad (2 pliki, znana tresc) - audytor moze
   przeliczyc go samodzielnie w kilku liniach Pythona, bez klonowania repo,
   i porownac z wartoscia w tym pliku.
"""

import hashlib
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "execution_package_v0_11"))
from validators.hard_halt import compute_files_hash_v2, _normalized_content_hash


def _independent_reference_v2(repo_root: Path, files) -> str:
    """Druga implementacja TEJ SAMEJ formuly v2, napisana OSOBNO (buduje caly
    bufor bajtow z gory i hashuje go za jednym razem, zamiast wielu wywolan
    .update() jak w produkcyjnej compute_files_hash_v2) - celowo inna droga
    kodu, ta sama specyfikacja, do wykrycia rozbieznosci implementacyjnych."""
    buf = b""
    for rel in sorted(files):
        content = (repo_root / rel).read_bytes().replace(b"\r\n", b"\n")
        content_hash_hex = hashlib.sha256(content).hexdigest()
        buf += rel.encode("utf-8") + b"\x00" + content_hash_hex.encode("utf-8") + b"\x00"
    return hashlib.sha256(buf).hexdigest()


@pytest.fixture
def tiny_fixture_tree(tmp_path):
    """2 pliki, tresc znana z gory - a.txt (LF), sub/b.txt (CRLF, do testu
    normalizacji). Sciezki wzgledne uzywane w hashu: 'a.txt', 'sub/b.txt'."""
    (tmp_path / "a.txt").write_bytes(b"hello\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_bytes(b"world\r\n")
    return tmp_path


class TestHashAlgorithmV2Pinned:

    def test_two_independent_implementations_agree(self, tiny_fixture_tree):
        files = ["a.txt", "sub/b.txt"]
        produced = compute_files_hash_v2(tiny_fixture_tree, files)
        reference = _independent_reference_v2(tiny_fixture_tree, files)
        assert produced == reference, (
            "PC-001 KROK 0: dwie niezalezne implementacje formuly v2 daja rozne "
            "wyniki - algorytm NIE jest jednoznacznie przypiety, nie wolno na "
            "nim budowac zadnego baseline'u"
        )

    def test_known_worked_example_hand_verifiable(self, tiny_fixture_tree):
        """Wartosc PONIZEJ jest do recznego przeliczenia przez audytora, bez
        tego repo - patrz docstring modulu / raport KROK 0. Jesli ten test
        kiedykolwiek zacznie failowac, znaczy to, ze zmienil sie algorytm
        (regresja specyfikacji v2), nie ze zmienily sie pliki fixture
        (fixture jest hardkodowany w tym samym pliku, wyzej)."""
        files = ["a.txt", "sub/b.txt"]
        expected = "8d8562ec180710f80f78582ad9c04c4300156836aaf30b4226dd28e26e59331a"
        assert compute_files_hash_v2(tiny_fixture_tree, files) == expected

    def test_per_file_content_hash_matches_normalized_content_hash(self, tiny_fixture_tree):
        """CRLF w sub/b.txt musi normalizowac sie do tej samej tresci co LF -
        dowod, ze normalizacja jest faktycznie stosowana, nie tylko deklarowana."""
        h_a = _normalized_content_hash(tiny_fixture_tree / "a.txt")
        h_b = _normalized_content_hash(tiny_fixture_tree / "sub" / "b.txt")
        assert h_a == hashlib.sha256(b"hello\n").hexdigest()
        assert h_b == hashlib.sha256(b"world\n").hexdigest(), (
            "CRLF w sub/b.txt (world\\r\\n) powinno dac IDENTYCZNY hash co "
            "czyste LF (world\\n) - normalizacja nie zadziałala"
        )

    def test_deterministic_repeated_calls(self, tiny_fixture_tree):
        files = ["a.txt", "sub/b.txt"]
        first = compute_files_hash_v2(tiny_fixture_tree, files)
        second = compute_files_hash_v2(tiny_fixture_tree, files)
        assert first == second

    def test_file_order_in_list_does_not_matter(self, tiny_fixture_tree):
        """Lista wejsciowa w innej kolejnosci (nie posortowanej) MUSI dac ten
        sam hash - sortowanie dzieje sie wewnatrz funkcji, nie jest
        obowiazkiem wywolujacego."""
        forward = compute_files_hash_v2(tiny_fixture_tree, ["a.txt", "sub/b.txt"])
        reversed_input = compute_files_hash_v2(tiny_fixture_tree, ["sub/b.txt", "a.txt"])
        assert forward == reversed_input

    def test_path_rename_changes_hash_even_with_identical_content(self, tmp_path):
        """Punkt 3 specyfikacji: hash zalezy od PARY (sciezka, tresc), nie
        samej tresci - przeniesienie pliku (ta sama tresc) MUSI zmienic hash."""
        (tmp_path / "x.txt").write_bytes(b"same content\n")
        (tmp_path / "y").mkdir()
        (tmp_path / "y" / "x.txt").write_bytes(b"same content\n")

        hash_at_root = compute_files_hash_v2(tmp_path, ["x.txt"])
        hash_moved = compute_files_hash_v2(tmp_path, ["y/x.txt"])
        assert hash_at_root != hash_moved, (
            "ta sama tresc pod inna sciezka dala TEN SAM hash - hash nie "
            "identyfikuje pary (sciezka, tresc), tylko sama tresc (blad "
            "wzgledem punktu 3 specyfikacji v2)"
        )

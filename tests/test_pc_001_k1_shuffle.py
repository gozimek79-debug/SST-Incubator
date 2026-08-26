"""B4C-1 (05): testy prymitywu K1 (clos_scientist/pc_001_k1_shuffle.py).
Ustalony PRZED evaluatorem - patrz docstring modulu, ten sam wzorzec co
statistics.py::linear_slope (B4C-2 (03))."""

import ast
import hashlib
from pathlib import Path

import pytest

from clos_scientist.pc_001_k1_shuffle import (
    K1_SHUFFLE_ALGORITHM_ID,
    derive_k1_permutation,
    k1_permutation_digest,
    k1_shuffle_seed,
)

MODULE_PATH = Path(__file__).resolve().parent.parent / "clos_scientist" / "pc_001_k1_shuffle.py"


class TestNoForbiddenRandomnessSources:
    """Zakaz jawny (B4C-1 (05)): zero hash()/time/os.urandom/nieziarnowany
    random. Sprawdzone strukturalnie (AST), nie tylko deklaracja w
    docstringu - ten sam wzorzec co adresowe walidatory Specyfikacji."""

    def _imported_names(self):
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        return names

    def test_module_does_not_import_random(self):
        assert "random" not in self._imported_names()

    def test_module_does_not_import_time(self):
        assert "time" not in self._imported_names()

    def test_module_does_not_import_os(self):
        assert "os" not in self._imported_names()

    def test_module_source_does_not_call_builtin_hash(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        call_names = {
            node.func.id for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert "hash" not in call_names

    def test_module_imports_only_hashlib(self):
        assert self._imported_names() == {"hashlib", "typing"}


class TestK1ShuffleSeed:
    """Decyzja 1: caly digest SHA256, big-endian, jako int - patrz docstring
    modulu."""

    def test_matches_independent_full_digest_big_endian_computation(self):
        expected = int.from_bytes(
            hashlib.sha256(b"PC001|K1|SHUFFLE|v1|1001").digest(), byteorder="big"
        )
        assert k1_shuffle_seed(1001) == expected

    def test_golden_value_seed_1001(self):
        # Pinned - patrz uzasadnienie w docstringu modulu (kazda przyszla
        # zmiana formuly MUSI zmienic ta wartosc, inaczej test to wykryje).
        assert k1_shuffle_seed(1001) == 48402276344859411116573971181341580417624404655371505966785147737024815868724

    def test_deterministic_across_independent_calls(self):
        assert k1_shuffle_seed(1001) == k1_shuffle_seed(1001)

    def test_different_seeds_give_different_values(self):
        assert k1_shuffle_seed(1001) != k1_shuffle_seed(1002)

    def test_depends_only_on_confirmatory_seed_argument(self):
        """Sygnatura strukturalnie nie przyjmuje genome_id - jedyny sposob
        na przekazanie 'informacji o genomie' byloby wplecenie jej w
        confirmatory_seed, co zaden wywolujacy nie robi (patrz uklad
        skrzyzowany, docstring modulu)."""
        import inspect
        params = list(inspect.signature(k1_shuffle_seed).parameters)
        assert params == ["confirmatory_seed"]


class TestDeriveK1Permutation:
    def test_is_valid_permutation_of_range_n(self):
        for n in (0, 1, 2, 5, 23, 50):
            perm = derive_k1_permutation(1001, n)
            assert sorted(perm) == list(range(n))

    def test_bit_identical_across_independent_calls(self):
        """JEDNA wspolna permutacja na blok-seed - dwa niezalezne wywolania
        (np. raz dla genomu 'default', raz dla genomu 'minimal', ten sam
        seed) MUSZA zwrocic bitowo identyczny wynik (WYMOG B4C-1 (05))."""
        first = derive_k1_permutation(1001, 23)
        second = derive_k1_permutation(1001, 23)
        assert first == second
        assert first is not second  # niezalezne obiekty, nie ten sam obiekt list

    def test_golden_value_seed_1001_n23(self):
        assert derive_k1_permutation(1001, 23) == [
            10, 2, 18, 7, 20, 17, 19, 1, 11, 22, 16, 3, 6, 9, 12, 8,
            13, 14, 15, 21, 0, 5, 4,
        ]

    def test_golden_value_seed_42_n5(self):
        assert derive_k1_permutation(42, 5) == [4, 1, 3, 2, 0]

    def test_different_seeds_give_different_permutations(self):
        assert derive_k1_permutation(1001, 23) != derive_k1_permutation(1002, 23)

    def test_n_zero_returns_empty(self):
        assert derive_k1_permutation(1001, 0) == []

    def test_n_one_returns_single_element(self):
        assert derive_k1_permutation(1001, 1) == [0]

    def test_negative_n_raises(self):
        with pytest.raises(ValueError):
            derive_k1_permutation(1001, -1)

    def test_no_shared_state_leaks_between_seeds(self):
        """Wywolanie z jednym seedem nie moze wplynac na wynik dla innego -
        brak globalnego/modulowego stanu w implementacji."""
        a1 = derive_k1_permutation(1001, 23)
        derive_k1_permutation(9999, 23)
        a2 = derive_k1_permutation(1001, 23)
        assert a1 == a2


class TestK1PermutationDigest:
    def test_deterministic(self):
        perm = derive_k1_permutation(1001, 23)
        assert k1_permutation_digest(perm) == k1_permutation_digest(list(perm))

    def test_golden_value(self):
        perm = derive_k1_permutation(42, 5)
        assert k1_permutation_digest(perm) == (
            "f03ed02eda8be0ed76da262cfd6189b65f5e31448ea6ab698c298ced0214a6bc"
        )

    def test_different_permutations_give_different_digests(self):
        d1 = k1_permutation_digest(derive_k1_permutation(1001, 23))
        d2 = k1_permutation_digest(derive_k1_permutation(1002, 23))
        assert d1 != d2

    def test_is_hex_string(self):
        digest = k1_permutation_digest(derive_k1_permutation(1001, 23))
        assert len(digest) == 64
        int(digest, 16)  # nie podnosi ValueError


class TestAlgorithmIdentifier:
    def test_is_declared_string_constant(self):
        assert K1_SHUFFLE_ALGORITHM_ID == "PC001_K1_SHUFFLE_V1"
        assert isinstance(K1_SHUFFLE_ALGORITHM_ID, str)

"""Testy scripts/validate_bh_family.py (B4C-05 v4, CTO pkt 4).

Konwencja projektu: kazdy test pozytywny ma test negatywny obok. Negatywy
tutaj buduja SYNTETYCZNE, popsute kopie prawdziwego artefaktu w pamieci
(kopiuj + popsuj jedno pole) - nie dotykaja pliku na dysku, zeby test byl
czytelny i nie zostawial brudnego stanu repo. Kazdy z czterech negatywow
zadanych przez CTO jest pokazany osobno, z wynikiem.
"""

import copy
import json
from pathlib import Path

from scripts.validate_bh_family import (
    load_family,
    load_spec_2_6_labels,
    cell_base_condition,
    check_addresses_resolve,
    check_cells_in_spec_2_6,
    check_count_matches_m,
    check_no_excluded_among_active,
    check_primary_environment_matches_config,
    check_kierunek_wsparcia,
    check_no_file_line_addresses,
    run_all_checks,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_FAMILY = load_family()
REAL_2_6_LABELS = load_spec_2_6_labels()


class TestCellBaseCondition:

    def test_positive_suffix_stripping(self):
        assert cell_base_condition("K1-A") == "K1"
        assert cell_base_condition("K4-separacja") == "K4"
        assert cell_base_condition("A") == "A"

    def test_positive_k3a_hyphen_to_space(self):
        assert cell_base_condition("K3a-warunek1") == "K3a warunek 1"

    def test_negative_unrelated_id_is_not_mangled(self):
        """Dowod, ze funkcja nie 'ucina' losowo - id bez znanego sufiksu
        wraca bez zmian, wiec test 'komorka spoza §2.6' faktycznie testuje
        przynaleznosc, nie efekt uboczny normalizacji."""
        assert cell_base_condition("ZZZ-nieznany") == "ZZZ-nieznany"


class TestRealArtifactPassesAllChecks:
    """Dowod na prawdziwym pliku - jesli to pada, popsul sie sam artefakt,
    nie tylko synteyczne scenariusze ponizej."""

    def test_real_family_has_11_active_cells(self):
        assert len(REAL_FAMILY["cells_active"]) == 11
        assert REAL_FAMILY["m"] == 11

    def test_real_family_passes_all_checks(self):
        """Nazwa celowo bez liczby kontroli - liczba rosla juz raz (4->5,
        B4C-05 v5; 5->6, B4C-2 (07)) i literal w nazwie testu rozjechalby sie
        z run_all_checks() przy kolejnym dodaniu (ten sam blad klasy co
        '52 wobec 53')."""
        results = run_all_checks(REAL_FAMILY)
        failing = {name: probs for name, probs in results.items() if probs}
        assert failing == {}, failing

    def test_real_family_has_exactly_seven_checks_registered(self):
        assert sorted(run_all_checks(REAL_FAMILY).keys()) == [
            "a_adresy_rozwiazuja_sie",
            "b_komorki_w_spec_2_6",
            "c_licznosc_rowna_m",
            "d_brak_wykluczonych_wsrod_aktywnych",
            "e_srodowisko_primary_zgodne_z_config",
            "f_kierunek_wsparcia",
            "g_brak_adresow_plik_linia",
        ]


class TestNegativeA_UnresolvableAddress:
    """Zadany przez CTO negatyw #1: adres nierozwiazywalny."""

    def test_bad_section_address_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"][0]["adres_kryterium"] = "W2-SPEC §99.99 (sekcja nie istnieje)"
        problems = check_addresses_resolve(family)
        assert problems != []
        assert any("§99.99" in p for p in problems)

    def test_bad_symbol_address_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"][0]["adres_testu_w_kodzie"] = "STATS::nieistniejaca_funkcja_xyz"
        problems = check_addresses_resolve(family)
        assert problems != []
        assert any("nieistniejaca_funkcja_xyz" in p for p in problems)

    def test_negative_of_negative_good_address_is_not_flagged(self):
        """Odwrotny sanity-check: prawdziwy, istniejacy adres NIE jest lapany."""
        family = copy.deepcopy(REAL_FAMILY)
        problems = check_addresses_resolve(family)
        assert problems == []


class TestNegativeB_CellOutsideSpec26:
    """Zadany przez CTO negatyw #2: komorka spoza §2.6."""

    def test_fake_condition_not_in_spec_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"].append({
            "id": "K99-fake",
            "warunek": "Warunek wymyslony na potrzeby testu",
            "status": "SOLID",
            "srodowisko": "noise_world",
            "test": "STATS::wilcoxon_signed_rank",
            "adres_kryterium": "PC-001 §5 -> 'K1'",
        })
        problems = check_cells_in_spec_2_6(family, REAL_2_6_LABELS)
        assert problems != []
        assert any("K99-fake" in p for p in problems)

    def test_negative_of_negative_all_real_cells_are_in_spec(self):
        problems = check_cells_in_spec_2_6(REAL_FAMILY, REAL_2_6_LABELS)
        assert problems == []


class TestNegativeC_CountMismatchWithM:
    """Zadany przez CTO negatyw #3: niezgodnosc licznosci z m."""

    def test_extra_cell_without_bumping_m_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"].append(copy.deepcopy(family["cells_active"][0]))
        problems = check_count_matches_m(family)
        assert problems != []
        assert "12" in problems[0] and "11" in problems[0]

    def test_missing_m_field_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        del family["m"]
        problems = check_count_matches_m(family)
        assert problems != []

    def test_negative_of_negative_real_count_matches(self):
        assert check_count_matches_m(REAL_FAMILY) == []


class TestNegativeD_ExcludedCellAmongActive:
    """Zadany przez CTO negatyw #4: komorka wykluczona wsrod aktywnych."""

    def test_k3b_injected_into_active_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"].append({"id": "K3b", "warunek": "wstrzykniete do testu"})
        problems = check_no_excluded_among_active(family)
        assert problems != []
        assert "K3b" in problems[0]

    def test_k2_injected_into_active_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"].append({"id": "K2", "warunek": "wstrzykniete do testu"})
        problems = check_no_excluded_among_active(family)
        assert problems != []
        assert "K2" in problems[0]

    def test_negative_of_negative_real_active_has_no_excluded(self):
        assert check_no_excluded_among_active(REAL_FAMILY) == []


class TestEnvironmentProvenanceAgainstConfig:
    """Dodatkowa kontrola (nie z listy CTO, ale bezposrednia konsekwencja
    'odczytaj z CONFIG, nie literalem') - environment Primary musi zgadzac
    sie z CONFIG::EXPERIMENT_CONFIG, nie tylko byc jakas nazwa."""

    def test_positive_real_family_matches_config(self):
        assert check_primary_environment_matches_config(REAL_FAMILY) == []

    def test_negative_wrong_environment_string_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        for cell in family["cells_active"]:
            if cell["id"] == "K1-A":
                cell["srodowisko"] = "shock_world (CONFIG::EXPERIMENT_CONFIG['environments']['primary'])"
        problems = check_primary_environment_matches_config(family)
        assert problems != []
        assert "K1-A" in problems[0]


class TestKierunekWsparcia:
    """B4C-2 (07)/(15), decyzje CTO: kontrola f - kazda komorka aktywna MA
    'kierunek_wsparcia' (wartosc z dwuelementowego zbioru {ODRZUCENIE_H0,
    ROWNOWAZNOSC} - BRAK_ODRZUCENIA_H0 zastapiony po zamknieciu Negative-
    Control Inference Review) i niepuste 'kierunek_wsparcia_zrodlo'; komorka
    ROWNOWAZNOSC MA dodatkowo 'equivalence_margin_c'/'effect_metric',
    komorka ODRZUCENIE_H0 ich NIE MA; liczby zadeklarowane na poziomie
    glownym zgadzaja sie z faktycznym rozkladem."""

    ROWNOWAZNOSC_CELL_ID = "K1-A"  # dowolna z szesciu, uzywana w negatywach ponizej

    def _rownowaznosc_cell(self, family):
        return next(c for c in family["cells_active"] if c["id"] == self.ROWNOWAZNOSC_CELL_ID)

    def test_positive_real_family_passes(self):
        assert check_kierunek_wsparcia(REAL_FAMILY) == []

    def test_positive_real_family_has_5_6_split(self):
        counts = {"ODRZUCENIE_H0": 0, "ROWNOWAZNOSC": 0}
        for cell in REAL_FAMILY["cells_active"]:
            counts[cell["kierunek_wsparcia"]] += 1
        assert counts == {"ODRZUCENIE_H0": 5, "ROWNOWAZNOSC": 6}

    def test_positive_rownowaznosc_cells_have_equivalence_fields(self):
        rownowaznosc_ids = {"K1-A", "K1-B", "K4-A", "K4-B", "K5-A", "K5-B"}
        for cell in REAL_FAMILY["cells_active"]:
            if cell["id"] in rownowaznosc_ids:
                assert cell["kierunek_wsparcia"] == "ROWNOWAZNOSC"
                assert cell["equivalence_margin_c"] == 0.10
                assert cell["effect_metric"] in ("E_beta", "redukcja_W2")
            else:
                assert cell["kierunek_wsparcia"] == "ODRZUCENIE_H0"
                assert "equivalence_margin_c" not in cell
                assert "effect_metric" not in cell

    def test_negative_missing_field_on_one_cell_is_caught(self):
        """Weryfikacja pkt 4 (06): usuniete pole jednej komorki -> FAIL."""
        family = copy.deepcopy(REAL_FAMILY)
        del family["cells_active"][0]["kierunek_wsparcia"]
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("brak pola" in p and family["cells_active"][0]["id"] in p for p in problems)

    def test_negative_missing_field_on_every_cell_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        for cell in family["cells_active"]:
            del cell["kierunek_wsparcia"]
        problems = check_kierunek_wsparcia(family)
        assert len(problems) >= 11

    def test_negative_value_outside_allowed_set_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"][0]["kierunek_wsparcia"] = "MOZE_TAK_MOZE_NIE"
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("spoza dozwolonego zbioru" in p for p in problems)

    def test_negative_old_value_brak_odrzucenia_h0_is_now_rejected(self):
        """B4C-2 (15): BRAK_ODRZUCENIA_H0 nie jest juz dozwolona wartoscia
        per komorka - proba jej uzycia (np. przez przypadkowy powrot do
        starego brzmienia) MUSI FAILowac, nie ciche PASS."""
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"][0]["kierunek_wsparcia"] = "BRAK_ODRZUCENIA_H0"
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("spoza dozwolonego zbioru" in p for p in problems)

    def test_negative_empty_source_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"][0]["kierunek_wsparcia_zrodlo"] = ""
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("puste lub brakujace" in p for p in problems)

    def test_negative_missing_source_key_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        del family["cells_active"][0]["kierunek_wsparcia_zrodlo"]
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("puste lub brakujace" in p for p in problems)

    def test_negative_declared_counts_mismatch_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["kierunek_ODRZUCENIE_H0"] = 4
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("!= zadeklarowana" in p for p in problems)

    def test_negative_missing_declared_counts_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        del family["kierunek_ODRZUCENIE_H0"]
        del family["kierunek_ROWNOWAZNOSC"]
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("brak zadeklarowanych liczb" in p for p in problems)

    def test_negative_rownowaznosc_cell_missing_margin_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        del self._rownowaznosc_cell(family)["equivalence_margin_c"]
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("bez pola 'equivalence_margin_c'" in p for p in problems)

    def test_negative_rownowaznosc_cell_missing_metric_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        del self._rownowaznosc_cell(family)["effect_metric"]
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("bez pola 'effect_metric'" in p for p in problems)

    def test_negative_odrzucenie_h0_cell_with_margin_is_caught(self):
        """Obecnosc equivalence_margin_c na komorce ODRZUCENIE_H0 sugerowalaby
        TOST policzony dla komorki, ktora go nie uzywa - FAIL, nie ciche
        zignorowanie nadmiarowego pola."""
        family = copy.deepcopy(REAL_FAMILY)
        odrzucenie_cell = next(c for c in family["cells_active"] if c["kierunek_wsparcia"] == "ODRZUCENIE_H0")
        odrzucenie_cell["equivalence_margin_c"] = 0.10
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("NIE MOZE miec pola 'equivalence_margin_c'" in p for p in problems)

    def test_negative_historical_brak_odrzucenia_declared_nonzero_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["kierunek_BRAK_ODRZUCENIA_H0"] = 1
        problems = check_kierunek_wsparcia(family)
        assert problems != []
        assert any("!= 0" in p for p in problems)

    def test_zero_cells_fails_not_silent_pass(self):
        problems = check_kierunek_wsparcia({"cells_active": []})
        assert problems != []
        assert any("ZERO" in p for p in problems)


class TestZeroMatchesIsNeverSilentPass:
    """B4C-05 v5 pkt 5: 'Twoje kontrole a-e maja te sama strukture i te sama
    podatnosc' [jak validate_canonical_spec.py] - dowod, ze wszystkie piec
    teraz FAILuja na 'nic do sprawdzenia', zamiast cicho PASSowac."""

    def test_a_fails_when_family_has_zero_addresses(self):
        empty = {"cells_active": [], "cells_excluded": [], "m": 0}
        problems = check_addresses_resolve(empty)
        assert problems != []
        assert any("ZERO" in p for p in problems)

    def test_b_fails_when_cells_active_is_empty(self):
        empty = {"cells_active": []}
        problems = check_cells_in_spec_2_6(empty, load_spec_2_6_labels())
        assert problems != []
        assert any("ZERO" in p for p in problems)

    def test_c_fails_when_m_and_count_are_both_zero(self):
        empty = {"cells_active": [], "m": 0}
        problems = check_count_matches_m(empty)
        assert problems != []

    def test_d_fails_when_cells_active_is_empty(self):
        empty = {"cells_active": [], "cells_excluded": []}
        problems = check_no_excluded_among_active(empty)
        assert problems != []
        assert any("ZERO" in p for p in problems)

    def test_e_fails_when_no_cell_claims_primary(self):
        family = copy.deepcopy(REAL_FAMILY)
        for cell in family["cells_active"]:
            cell["srodowisko"] = cell.get("srodowisko", "").replace(
                "noise_world (CONFIG::EXPERIMENT_CONFIG['environments']['primary'])",
                "pure_noise_world (CONFIG::EXPERIMENT_CONFIG['environments']['K4'])",
            )
        problems = check_primary_environment_matches_config(family)
        assert problems != []
        assert any("ZERO" in p for p in problems)

    def test_negative_of_negative_real_family_still_passes_after_fix(self):
        results = run_all_checks(REAL_FAMILY)
        failing = {name: probs for name, probs in results.items() if probs}
        assert failing == {}, failing


class TestNoFileLineAddresses:
    """B4C-2 (20), znalezisko CTO: forma 'plik.py:NNN' nie jest w gramatyce
    adresow (SECTION/FRAGMENT/SYMBOL) - zaden z trzech walidatorow jej nie
    widzial, wiec trzy takie adresy w tym artefakcie zdryfowaly niezauwazenie
    po wstawieniu funkcji wyzej w statistics.py. Negatyw obowiazkowy (CTO
    wprost): wstaw taki adres i pokaz FAIL."""

    def test_positive_real_family_has_zero_file_line_addresses(self):
        assert check_no_file_line_addresses(REAL_FAMILY) == []

    def test_negative_inserted_file_line_address_is_caught(self):
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"][0]["adres_testu_w_kodzie"] = (
            "clos_curriculum/laboratory/statistics.py:741 (przyklad zakazanej formy)"
        )
        problems = check_no_file_line_addresses(family)
        assert problems != []
        assert any("statistics.py:741" in p for p in problems)

    def test_negative_symbolic_address_is_not_falsely_flagged(self):
        """Sanity-check w druga strone: forma STATS::nazwa_funkcji (dozwolona,
        nie dryfujaca) nie ma byc lapana przez ten sam wzorzec."""
        family = copy.deepcopy(REAL_FAMILY)
        family["cells_active"][0]["adres_testu_w_kodzie"] = "STATS::wilcoxon_signed_rank"
        problems = check_no_file_line_addresses(family)
        assert problems == []

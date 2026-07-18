"""SPRINT_v0.11.0.md, decyzja CTO 2026-07-18: scripts/validate_panel.py
rozszerzony o dwa dodatkowe sprawdzenia, poza dawnym skanem wklejonych
metryk:

  (A) panel.js NIE MOZE reimplementowac klasyfikacji valid/degenerate/
      insufficient (progi na ci95_valid/n_effective) poza jawnie nazwanym
      fallbackiem _fallbackClassifyConcepts - Python (competency_profile.py)
      jest jedynym zrodlem.
  (B) panel.js NIE MOZE czytac pola (comp./c./gd./obs./gs./status./metadata.),
      ktorego nie ma w odpowiednim realnym pliku (competency_profile.json /
      reports/status.json / publications/L1_1_pattern_echo/metadata.json).

Diagnoza, ktora do tego doprowadzila: panel.js liczyl klasyfikacje SAM
(dawne competencyRowState()), wiec zmiana ontologii 6+1 w Pythonie NIE
dotarla do panelu - bez cracha, bez ostrzezenia, na publicznym URL.
scripts/validate_panel.py (przed ta zmiana) tego nie lapal - sprawdzal
tylko literaly, nie zgodnosc struktury. Testy nizej dowodza, ze ta
konkretna luka jest teraz zamknieta.

Zadanie 3 (2026-07-18, wersjonowanie + widocznosc): "status"/"metadata"
dolaczone jako korzenie lancuchow (status.sprint/timestamp/commit z
reports/status.json, metadata.frozen/frozen_reason z bundle L1.1).
"""

import json

import pytest

from scripts.validate_panel import (
    _source_for_chain_scan,
    find_classification_reimplementation_violations,
    find_unknown_key_violations,
    main,
)


@pytest.fixture
def real_profile():
    with open("publications/competency_profile.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def real_status():
    with open("reports/status.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def real_metadata():
    with open("publications/L1_1_pattern_echo/metadata.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def real_panel_source():
    with open("clos_studio/panel/panel.js", encoding="utf-8") as f:
        return f.read()


class TestRealPanelIsClean:
    """Bramka: prawdziwy panel.js w repo musi przechodzic OBA nowe sprawdzenia."""

    def test_no_classification_reimplementation(self, real_panel_source):
        violations = find_classification_reimplementation_violations(real_panel_source)
        assert violations == [], violations

    def test_no_unknown_keys(self, real_panel_source, real_profile, real_status, real_metadata):
        violations = find_unknown_key_violations(real_panel_source, real_profile, real_status, real_metadata)
        assert violations == [], violations

    def test_main_exits_zero(self):
        assert main() == 0


class TestClassificationReimplementationDetected:
    """(A) Wzorzec `.every(...ci95_valid...)` POZA fallbackiem musi FAILOWAC;
    ten sam wzorzec WEWNATRZ _fallbackClassifyConcepts (juz obecny w
    prawdziwym pliku) nie jest zgloszony - dowiedzione w TestRealPanelIsClean."""

    def test_direct_comparison_outside_fallback_fails(self):
        source = (
            "function sneaky(c) { return c.genomes.default.ci95_valid === true; }"
        )
        violations = find_classification_reimplementation_violations(source)
        assert violations, "bezposrednie porownanie ci95_valid === poza fallbackiem MUSI byc wykryte"

    def test_every_with_ci95_valid_outside_fallback_fails(self):
        source = (
            "function sneaky(c) { return Object.keys(c.genomes).every("
            "function (g) { return c.genomes[g].ci95_valid === true; }); }"
        )
        violations = find_classification_reimplementation_violations(source)
        assert violations, ".every(...ci95_valid...) poza fallbackiem MUSI byc wykryte"

    def test_n_effective_threshold_outside_fallback_fails(self):
        source = "function sneaky(c) { return c.n_effective >= 5; }"
        violations = find_classification_reimplementation_violations(source)
        assert violations, "prog n_effective>=N poza fallbackiem MUSI byc wykryty"

    def test_same_pattern_inside_fallback_is_allowed(self):
        source = (
            "function _fallbackClassifyConcepts(concepts) { "
            "return concepts.filter(function (c) { "
            "return Object.keys(c.genomes).every(function (g) { "
            "return c.genomes[g].ci95_valid === true; }); }); }"
        )
        violations = find_classification_reimplementation_violations(source)
        assert violations == [], "wzorzec WEWNATRZ nazwanego fallbacku nie moze byc failem"

    def test_display_only_ci95_valid_is_not_flagged(self):
        """Wyswietlanie ci95_valid jako fakt (nie warunek) jest legalne -
        to dokladnie to, co panel.js robi w renderConceptRow dla gbar-ci."""
        source = 'return "ci95_valid=" + fmtBool(gd.ci95_valid);'
        violations = find_classification_reimplementation_violations(source)
        assert violations == [], violations


class TestUnknownKeyDetected:
    """(B) TEST NEGATYWNY wymagany przez CTO: usuniecie klucza z JSON,
    ktory panel.js faktycznie czyta, MUSI dac FAIL; przywrocenie - exit 0."""

    def test_reading_missing_top_level_key_fails(self, real_panel_source, real_profile):
        broken = dict(real_profile)
        del broken["minimal_profile"]
        violations = find_unknown_key_violations(real_panel_source, broken)
        assert violations, "usuniecie minimal_profile (czytanego przez panel.js) MUSI byc wykryte"

    def test_reading_missing_nested_key_fails(self, real_panel_source, real_profile):
        broken = json.loads(json.dumps(real_profile))
        del broken["minimal_profile"]["cognitive_axes"]
        violations = find_unknown_key_violations(real_panel_source, broken)
        assert violations, "usuniecie minimal_profile.cognitive_axes MUSI byc wykryte"
        assert any("cognitive_axes" in v[0] for v in violations)

    def test_restoring_key_passes_again(self, real_panel_source, real_profile, real_status, real_metadata):
        broken = json.loads(json.dumps(real_profile))
        del broken["minimal_profile"]["cognitive_axes"]
        assert find_unknown_key_violations(real_panel_source, broken, real_status, real_metadata) != []

        restored = json.loads(json.dumps(real_profile))
        assert find_unknown_key_violations(real_panel_source, restored, real_status, real_metadata) == []

    def test_fake_key_never_produced_by_python_fails(self, real_panel_source, real_profile):
        """Odwrotny kierunek: panel.js CZYTAJACY pole, ktorego Python nigdy
        nie produkuje, tez musi byc wykryty (nie tylko usuniecie istniejacego)."""
        fake_source = real_panel_source + "\n  function x(comp) { return comp.this_key_does_not_exist_anywhere; }\n"
        violations = find_unknown_key_violations(fake_source, real_profile)
        assert any("this_key_does_not_exist_anywhere" in v[0] for v in violations)

    def test_commit_object_c_is_not_confused_with_concept(self, real_panel_source, real_profile):
        """Regresja: 'c' w commits.map(function (c) {...}) to obiekt commita
        GitHub (c.sha, c.commit.message), NIE koncept - nie moze dawac
        falszywego alarmu (byl to rzeczywisty problem podczas budowy tego
        walidatora, patrz NON_CONCEPT_C_MARKERS)."""
        violations = find_unknown_key_violations(real_panel_source, real_profile)
        assert not any("c.sha" in v[0] or "c.commit" in v[0] for v in violations)


class TestStatusAndMetadataRoots:
    """Zadanie 3 (2026-07-18): status.sprint (VERSION -> write_status.py ->
    status.json -> panel) i metadata.frozen/frozen_reason (baner FROZEN)
    musza przechodzic dokladnie ten sam mechanizm sprawdzania kluczy (B)."""

    def test_missing_sprint_key_fails(self, real_panel_source, real_profile, real_status, real_metadata):
        broken_status = dict(real_status)
        del broken_status["sprint"]
        violations = find_unknown_key_violations(real_panel_source, real_profile, broken_status, real_metadata)
        assert any("status.sprint" in v[0] for v in violations)

    def test_restoring_sprint_key_passes(self, real_panel_source, real_profile, real_status, real_metadata):
        assert find_unknown_key_violations(real_panel_source, real_profile, real_status, real_metadata) == []

    def test_missing_frozen_reason_key_fails(self, real_panel_source, real_profile, real_status, real_metadata):
        broken_metadata = dict(real_metadata)
        del broken_metadata["frozen_reason"]
        violations = find_unknown_key_violations(real_panel_source, real_profile, real_status, broken_metadata)
        assert any("metadata.frozen_reason" in v[0] for v in violations)

    def test_promise_then_catch_not_confused_with_status_or_metadata_json_keys(self, real_panel_source, real_profile):
        """Regresja: 'loads.status.then(...)'/'loads.metadata.catch(...)' -
        tutaj status/metadata sa WLASCIWOSCIAMI obiektu loads (Promise), nie
        samym rootem status.json/metadata.json - .then/.catch to metody
        Promise, nie klucze JSON, i NIE moga byc sprawdzane wzgledem
        ksztaltu tych plikow (byl to rzeczywisty falszywy alarm podczas
        budowy tego walidatora)."""
        violations = find_unknown_key_violations(real_panel_source, real_profile, {}, {})
        assert not any(".then" in v[0] or ".catch" in v[0] for v in violations)


class TestSourceForChainScanIsSafe:
    """Regresje na dwoch rzeczywistych bledach napotkanych przy budowie
    _source_for_chain_scan: apostrof w komentarzu blokowym i apostrof w
    klasie znakow regex-literalu potrafily (przy naiwnym, wieloetapowym
    podejsciu regexowym) polknac setki linii kodu jako "jeden string"."""

    def test_apostrophe_inside_block_comment_does_not_swallow_following_code(self):
        source = (
            "/* np. zacache'owany artefakt - dalszy komentarz */\n"
            "function real(comp) { return comp.should_be_visible; }\n"
        )
        scanned = _source_for_chain_scan(source)
        assert "should_be_visible" in scanned

    def test_apostrophe_inside_regex_character_class_does_not_swallow_following_code(self):
        source = (
            'function escapeHtml(s) { return String(s).replace(/[&<>"\']/g, function (c) { return c; }); }\n'
            "function real(comp) { return comp.should_be_visible; }\n"
        )
        scanned = _source_for_chain_scan(source)
        assert "should_be_visible" in scanned

    def test_url_inside_string_not_treated_as_line_comment(self):
        source = 'var BASE = "https://raw.githubusercontent.com/owner/repo/branch/";\nfunction real(comp) { return comp.should_be_visible; }\n'
        scanned = _source_for_chain_scan(source)
        assert "should_be_visible" in scanned

    def test_length_is_preserved(self, real_panel_source):
        assert len(_source_for_chain_scan(real_panel_source)) == len(real_panel_source)

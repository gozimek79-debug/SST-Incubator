"""B4C-2 (08), decyzja CTO: przypina DLUGOSCI okien K3a warunek 1 - dwie
stale o wartosci 20 nie wyrazaja same z siebie asymetrii 21/20, robi to
konwencja domkniecia przedzialu w k3a_pre_post_shock_windows(). Zrodlo:
publications/preregistration_PC_001.md, wiersz 146: "Wzrost: srednia PE w
[shock_tick, shock_tick+20] > srednia w [shock_tick-20, shock_tick-1]."."""

from clos_scientist.pc_001_experiment_config import k3a_pre_post_shock_windows


class TestK3aWindowLengths:
    """Cytat zrodla (wiersz 146 preregistration_PC_001.md): pre-okno
    [shock_tick-20, shock_tick-1] (20 tickow), post-okno [shock_tick,
    shock_tick+20] (21 tickow, przedzial domkniety obustronnie w zrodle)."""

    def test_pre_window_has_20_ticks(self):
        pre, _post = k3a_pre_post_shock_windows(50)
        assert len(pre) == 20

    def test_post_window_has_21_ticks(self):
        _pre, post = k3a_pre_post_shock_windows(50)
        assert len(post) == 21

    def test_windows_are_adjacent_not_overlapping(self):
        pre, post = k3a_pre_post_shock_windows(50)
        assert max(pre) + 1 == min(post)
        assert set(pre) & set(post) == set()

    def test_pre_window_ends_at_shock_tick_minus_1(self):
        pre, _post = k3a_pre_post_shock_windows(50)
        assert max(pre) == 49

    def test_post_window_starts_at_shock_tick(self):
        _pre, post = k3a_pre_post_shock_windows(50)
        assert min(post) == 50

    def test_holds_for_other_shock_ticks_in_realistic_range(self):
        """shock_tick w [20,80] (clos_world.scenarios.SINGLE_PERTURBATION_
        SCENARIOS['shock_world']: randint(20,80)) - dowod, ze przypiecie
        dlugosci nie jest przypadkiem jednej wartosci."""
        for shock_tick in (20, 42, 80):
            pre, post = k3a_pre_post_shock_windows(shock_tick)
            assert len(pre) == 20
            assert len(post) == 21
            assert max(pre) + 1 == min(post)

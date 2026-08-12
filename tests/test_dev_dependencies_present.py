"""Straznik zaleznosci testowych (zgloszenie audytora CI-01B, 2026-08-11).

POMIAR AUDYTORA (srodowisko bez scipy, klon 45d8ea2): pytest.importorskip(
"scipy.stats") w tests/test_pc_001_statistics.py:19 stoi NA POZIOMIE MODULU.
Gdy scipy brakuje, pytest nie zglasza "60 skipped" (po jednym na kazdy z 60
testow tego pliku) - zglasza "1 skipped" (caly modul jako jedna pozycja
kolekcji). Liczba "1" obok "725 passed" jest rownie latwa do przeoczenia
jak jej brak - sam zapis liczby pominietych w status.json (patrz
write_status.py) tego nie naprawia.

Test ktory SAM SIEBIE pomija (importorskip) nie moze chronic przed cisza
wlasnego pominiecia. Ten test dziala inaczej: NIE uzywa importorskip. Gdy
scipy nie jest zainstalowane, PADA (failed), nie pomija sie (skipped) -
"failed" jest liczone i raportowane oddzielnie od "skipped" w kazdym trybie
pytest, wiec regresja (np. ktos usunie instalacje requirements-dev.txt z
ci.yml) daje czerwony, gloszny sygnal zamiast cichego spadku z 785 do 725.
"""


def test_scipy_stats_is_importable():
    try:
        import scipy.stats  # noqa: F401
    except ImportError as exc:
        raise AssertionError(
            "scipy.stats nie jest importowalne - zaleznosc testowa z "
            "requirements-dev.txt (patrz ten plik i komentarz w "
            "requirements-dev.txt) nie zostala zainstalowana w tym "
            "srodowisku. Bez niej tests/test_pc_001_statistics.py (60 "
            "testow walidacji reguly decyzyjnej PC-001 przeciw scipy do "
            "1e-6) CICHO znika z zestawu jako jedna pozycja '1 skipped', "
            "nie '60 skipped' - patrz zgloszenie CI-01B. Napraw instalacje "
            "zaleznosci (pip install -r requirements-dev.txt), nie ten test."
        ) from exc

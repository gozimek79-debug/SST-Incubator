# ANEKS 5 do PREREJESTRACJI PC-001 — K3a warunek 2: SUSPENDED PENDING WINDOW REDEFINITION

**Od:** CTO (na podstawie analizy wykonawcy, D-025D)
**Data:** 2026-07-28
**Status:** ZATWIERDZONY
**Podstawa:** D-025D · analiza kodu i minimalny pomiar diagnostyczny (16 przebiegów, seedy pilota)

---

## Jeden temat

Osobne znalezisko od Aneksu 4 (K3b) — **inna przyczyna, inny status**. Nie jest to dopisek
do Aneksu 4: K3b jest właściwością Core (ARCHITECTURE-LIMITED), K3a warunek 2 jest błędem
projektu pomiaru (naprawialny bez dotykania Core).

## Warunek 1 K3a — BEZ ZMIAN, SOLIDNY

Wzrost PE po wstrząsie (`mean PE[shock_tick, shock_tick+20] > mean PE[shock_tick-20, shock_tick-1]`):
**16/16 przebiegów spełnia**, strukturalnie gwarantowany — przed wstrząsem świat jest stałą
0.2 (PE≈0, trywialnie przewidywalne), po wstrząsie następuje prawdziwy skok. Ten warunek
pozostaje wiarygodny bez żadnych zastrzeżeń.

## Warunek 2 K3a — okna nie pasują do skali czasowej zjawiska

**Definicja (bez zmian, PC-001 §5):** `mean PE[shock_tick+40, shock_tick+60] <
mean PE[shock_tick, shock_tick+20]`.

**Problem:** adaptacja predykcji do nowego plateau kończy się w **~3-5 ticków**, nie 40-60.
Mechanizm (potwierdzony w kodzie, `clos_brain/runtime/prediction.py`): gałąź awaryjna
`predict()` to średnia z ostatnich `prediction_depth` wejść. **`prediction_depth=3` dla
wszystkich 23 genomów** — żaden genom (ani preset, ani LHS z `population.py`) go nie
nadpisuje. Przy stałym post-wstrząsowym plateau ta średnia zbiega w kilka ticków,
niezależnie od genomu.

**Konsekwencja:** okno 1 `[shock_tick, shock_tick+20]` zawiera **cały** proces adaptacji
(skok + zbieżność), okno 2 `[shock_tick+40, shock_tick+60]` próbkuje **czysty, już
ustabilizowany szum** — to samo pasmo, które dominuje już drugą połowę okna 1. Różnica
średnich między oknami jest funkcją tego, jak duży był początkowy skok (pierwsze ~5
ticków okna 1) względem losowej próbki szumu w oknie 2 — **nie sygnałem re-adaptacji**.

### Dowód: trajektoria seed=1, genom `default`, `shock_tick=28`

```
tick 28: PE=0.44   (skok w momencie wstrząsu)
tick 29: PE=0.13
tick 31: PE=0.09
tick 33: PE=0.008  (już w paśmie szumu)
ticki 33-48: oscylacja w paśmie ~0.01-0.13 (to samo pasmo co reszta obserwowanego okna,
             w tym okno 2)
```

### Pomiar zbiorczy

16 przebiegów (8 genomów × 2 seedy, wyłącznie seedy z zakresu pilota, rozłączne z
konfirmacją od 1001; pomiar diagnostyczny, nic nie zapisane na dysk):

```
warunek 1 (wzrost):        16/16 spełniony
warunek 2 (re-adaptacja):   8/16 spełniony
```

Rozkład warunku 2 koreluje z **seedem** (a więc `shock_tick`/`shock_magnitude`), nie z
genomem — 8/16 jest wynikiem **diagnostycznym** ("pomiar to szum"), nie eksperymentalnym:
nie mierzy różnicy między genomami, tylko pokazuje, że sam pomiar nie rozróżnia sygnału
od szumu przy obecnych oknach.

## Klasyfikacja (G-001)

**Typ M** dla warunku 2 K3a — endpoint (w tej konkretnej operacjonalizacji) nie mierzy
hipotezy PC (wynik zależy od losowego skoku, nie od tego, czy PC istnieje), i nie ma
poprawnej interpretacji obecnego wyniku (8/16 nie mówi nic o systemie, tylko o tym, że
dwa okna próbkują tę samą dystrybucję szumu).

**Różnica względem K3b (Aneks 4):**

| | K3b | K3a warunek 2 |
|---|---|---|
| Przyczyna | właściwość Core (regulator nie wyprowadza z nasycenia) | błąd definicji okien (za późno wobec dynamiki) |
| Naprawialność | NIE bez zmiany Core (G-004) | TAK, bez dotykania Core |
| Status | ARCHITECTURE-LIMITED (wraca po CLOS v0.12) | SUSPENDED PENDING WINDOW REDEFINITION |

## Skażenie

**Brak.** Pomiar wykonany na seedach z zakresu pilota (1-5), rozłącznych z konfirmacją
(od 1001). Nic nie zapisane na dysk. Wynik 8/16 jest diagnozą samego narzędzia pomiarowego
("czy okna rozróżniają sygnał od szumu"), nie próbą zmierzenia efektu PC.

## Status

**Warunek 2 K3a: SUSPENDED PENDING WINDOW REDEFINITION.** Warunek 1 K3a pozostaje aktywny
i wiarygodny. Ten aneks **NIE proponuje** nowych granic okien — to decyzja CTO, osobne
zadanie.

---

## Zamrożenie

Ten dokument wchodzi do `CRITICAL_FILES_PC_001` (oba formaty, md kanoniczny) —
klasyfikacja i status warunku 2 K3a nie mogą się zmienić bez złamania hasha.

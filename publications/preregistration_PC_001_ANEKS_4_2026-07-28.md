# ANEKS 4 do PREREJESTRACJI PC-001 — status K3b: ARCHITECTURE-LIMITED

**Od:** CTO
**Data:** 2026-07-28
**Status:** ZATWIERDZONY (D-026)
**Podstawa:** D-025A (zatwierdzenie W-01) · D-025E (rozstrzygnięcie ws. v0.11) · wynik W-01

---

## Jeden temat

K3b (Kendall tau na `recovery_i`, `recurring_shock_world`) otrzymuje status
**ARCHITECTURE-LIMITED**:

- K3b pozostaje **ZDEFINIOWANA** w metodologii PC-001 — definicja, formuła, miejsce w regule
  decyzyjnej nie są usuwane z dokumentacji.
- K3b **NIE jest wykonywana** w PC-001.
- K3b **NIE jest usunięta** z programu badawczego.
- K3b **wraca** po nowej wersji Core (CLOS v0.12).

## Powód

**Zweryfikowana właściwość badanego modelu CLOS v0.11 w analizowanych scenariuszach**
(nie "odkrycie naukowe" — to rozróżnienie językowe jest częścią tej decyzji, patrz D-026 pkt 3):
regulator homeostatyczny (`regulate()`) nie wyprowadza systemu z nasycenia entropii w oknie
dostępnym między kolejnymi wstrząsami `recurring_shock_world`. Zmierzone wprost (W-01,
`reports/pilot/w01_recovery_1_recurring_shock_world.json`): **88.4% przebiegów cenzurowanych**
(61/69, interval=40 ticków), z czego **73.9% (51/69)** utyka przy suficie entropii `[0,1]=1.0`
i nie wraca w oknie w ogóle — nie „recovery trwa 35–40 ticków", tylko brak powrotu.

## Konsekwencja dla reguły decyzyjnej

Reguła 9-warunkowa (PC-001 §6 + Aneks 1) → **8 warunków wykonywanych w PC-001**. K3b jest
**zawieszona**, nie usunięta — nie zmniejsza to liczby warunków w definicji metodologii, tylko
liczbę faktycznie ocenianych w tym konkretnym przebiegu badawczym.

## Zastrzeżenie: 21% (v0.11) i 88% (W-01) to RÓŻNE wielkości

Żeby za rok nikt nie zestawił tych dwóch liczb jako trendu pogarszania się tej samej właściwości:

| | v0.11 (Homeostatic Resilience) | W-01 (K3b, ten aneks) |
|---|---|---|
| Okno obserwacji | `W_WINDOW=150` ticków | 40 ticków (do kolejnego wstrząsu) |
| Środowisko | `shock_world` (**jeden** wstrząs) | `recurring_shock_world` (wstrząsy powtarzające się) |
| Warunek sustain | `N_SUSTAIN=10` | (nie dotyczy — mierzone: powrót w ogóle w oknie) |
| Wynik cenzurowania | ~21% | 88.4% |

**Różnica strukturalna** (D-025E): okno 3.75× krótsze (40 vs 150 ticków) **oraz** kolejny
wstrząs następuje, zanim poprzedni zdążył się wyczerpać — to nie jest ta sama miara w gorszych
warunkach, to miara innego zjawiska (powrót po pojedynczym wstrząsie w długim oknie vs powrót
między gęsto następującymi wstrząsami).

**Wniosek D-025E: brak podstaw do rewizji statusu Homeostatic Resilience w v0.11. Status
ZOSTAJE bez zmian.** Wcześniejsze sformułowanie audytora ("to samo zjawisko w ostrzejszej
formie") było pochopne i zostaje tu jawnie skorygowane, nie cicho wycofane.

---

## Zamrożenie

Ten dokument wchodzi do `CRITICAL_FILES_PC_001` (oba formaty, md kanoniczny) — status K3b i
zastrzeżenie o nieporównywalności 21%/88% nie mogą się zmienić bez złamania hasha.

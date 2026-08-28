# ERRATUM 1 do ANEKSU 1 (PREREJESTRACJA PC-001)

**Data:** 2026-08-27
**Status:** **ZATWIERDZONY** decyzją **CTO**, B4C-2 (09)
**Podstawa:** znalezisko wykonawcy podczas pisania evaluatora (B4C-2 (06)-(08)) - wewnętrzna
sprzeczność w ANEKS 1 → „Zmiana 3", potwierdzona przez CTO i skorygowana zanim jakiekolwiek
dane PC-001 zaczęły istnieć.
**Autor:** CTO (rozstrzygnięcie), wykonawca (znalezisko i szkic techniczny)
**Rodzaj dokumentu:** **ERRATUM** - poprawka do zamrożonego brzmienia ANEKS 1, nie
doprecyzowanie. ANEKS 1 pozostaje NIETKNIĘTY w swoim pierwotnym brzmieniu; to erratum
nadpisuje go **normatywnie** (co obowiązuje dziś), nie **tekstowo** (plik ANEKS 1 się nie zmienia).

> **DOPUSZCZALNOŚĆ ERRATUM:** D-006 pkt 3 zakazuje zmian w kryteriach *„po rozpoczęciu zbierania
> danych"*. Pilotaże techniczne i analiza mocy **istnieją**, ale **nie są danymi
> konfirmacyjnymi używanymi do oceny hipotezy PC-001**: seedy pilota (`pilot_final.py`,
> zakres 1-15, D-042) i dry-run (`pc_001_confirmatory_runner.py::DRY_RUN_SEED_START=50000`,
> 3 seedy) służą wyłącznie weryfikacji mechaniki i obliczalności podłogi/mianownika - żaden
> z nich nie wchodzi do rodziny BH-FDR ani do werdyktu. **Blok seedów konfirmacyjnych
> (1001-1050, `CONFIRMATORY_SEEDS_RESERVED`) pozostaje nietknięty** - żaden przebieg na tych
> seedach nie został wykonany. `PC_001_BASELINE` pozostaje `TBD` (B5 wstrzymane, decyzja CTO).
> Erratum jest więc dopuszczalne **dziś**, tą samą zasadą co ANEKS 1 sam - to ostatni moment,
> w którym korekta kryterium nie jest dostosowywaniem go do wyniku, bo wyniku nie ma.

---

## Powód erratum

Podczas implementacji evaluatora (B4C-2) wykonawca znalazł, że ANEKS 1 → „Zmiana 3" zawiera
**dwa zdania, które nie mogą być jednocześnie prawdziwe**, oba w obrębie tej samej zmiany.

**Zdanie 1 (uzasadnienie problemu, poprzedza nowe brzmienie):**

> „**Problem** (wskazany przez recenzenta): przy 22% w środowisku realnym i 19% w czystym
> szumie kryterium **formalnie przechodzi**, choć nie różnicuje niczego."

**Zdanie 2 (nowe brzmienie kryterium, wprowadzone tą samą zmianą):**

> „Efekt w środowisku inferencyjnym (`shock_world`) musi **istotnie przewyższać** efekt
> w `pure_noise_world` — porównanie rozkładów `redukcja` między środowiskami (Mann-Whitney U,
> `p < 0.05` po FDR), **oprócz** pierwotnego wymogu, że `pure_noise_world` nie spełnia A ani B."

**Sprzeczność, dwuczłonowa:**

**(a) Niezgodność liczbowa.** Liczby 22% i 19% w Zdaniu 1 to wartości `redukcja_W2` w
odniesieniu do progu Warunku B (20%, `CONFIG::CONDITION_B_REDUCTION_THRESHOLD`). Warunek B
jest zdefiniowany i mierzony wyłącznie w `noise_world` (Primary Endpoint, W2-SPEC §2.3;
`pure_noise_world` ma **własną** wersję tego samego testu jako K4-B). „Środowisko realne"
w Zdaniu 1 odnosi się więc do `noise_world` - ale Zdanie 2 nazywa drugą stronę porównania
`shock_world`. Te dwa środowiska (`noise_world` i `shock_world`) to różne pozycje w
`CONFIG::EXPERIMENT_CONFIG['environments']` (`primary` vs `K3`) - Zdanie 1 i Zdanie 2 nie
mogą opisywać tej samej pary środowisk.

**(b) Niewykonalność techniczna.** `redukcja_W2` wymaga zamrożonej podłogi środowiska
(W2-SPEC §2.2: `PE_red(t) = max(0, PE(t) - floor_env)`). Zamrożone podłogi istnieją
wyłącznie dla dwóch środowisk:

  - `noise_world`: `CONFIG::FROZEN_FLOOR_NOISE_WORLD` = 0.09589
  - `pure_noise_world`: `CONFIG::FROZEN_FLOOR_PURE_NOISE_WORLD` = 0.236972

`shock_world` **nie ma** zamrożonej podłogi - nigdy nie została wyznaczona, żaden runner jej
nie liczy (`pc_001_confirmatory_runner.py::verify_floors_before_run()` explicite pomija
`shock_world` - "K3 idzie inna sciezka"). Potwierdzone też historycznie: `pilot_final.py`
(`FLOOR_BY_ENVIRONMENT`) ma dokładnie dwa wpisy (noise_world, pure_noise_world) -
`shock_world` nigdy w nim nie występował, więc `redukcja_W2` dla `shock_world` nigdy nie
została i nie mogła zostać policzona w żadnym dotychczasowym pomiarze.

**Dlaczego K3a (warunek 1) nie ma tego problemu, a K4-separacja w brzmieniu dosłownym - ma:**
K3a porównuje **średnie** PE przed i po wstrząsie (`[shock_tick-20, shock_tick-1]` vs
`[shock_tick, shock_tick+20]`, PC-001 §5 → „K3") - stała podłoga (gdyby istniała) skróciłaby
się w **różnicy** średnich. K4-separacja porównuje **iloraz** (`redukcja_W2` jest ilorazem,
nie różnicą) - podłoga w ilorazie się **nie** skraca, tylko wprost przesądza o wyniku. Dlatego
W2-SPEC §5 („K3a/K3b: bez zmian") jest wewnętrznie spójne, a Zdanie 2 ANEKS 1 w brzmieniu
dosłownym - nie jest.

---

## Poprawka

**Obowiązujący tekst „shock_world" w kryterium K4-separacja (Zdanie 2 powyżej) zostaje
ZASTĄPIONY przez „noise_world".**

**Nowe, obowiązujące brzmienie kryterium K4-separacja:**

> Efekt w środowisku Primary (`noise_world`, `CONFIG::EXPERIMENT_CONFIG['environments']['primary']`)
> musi **istotnie przewyższać** efekt w `pure_noise_world`
> (`CONFIG::EXPERIMENT_CONFIG['environments']['K4']`) — porównanie rozkładów `redukcja_W2`
> między środowiskami (`STATS::mann_whitney_u`, `p < 0.05` po FDR), **oprócz** pierwotnego
> wymogu, że `pure_noise_world` nie spełnia A ani B.

Ta wersja jest zgodna z **oboma** zdaniami jednocześnie: Zdanie 1 (22%/19%, oba w
środowiskach, które **mają** zamrożoną podłogę) i mechanizmem `redukcja_W2` (wymaga
podłogi po obu stronach porównania).

**Okna pomiarowe:** `CONFIG::W_EARLY_TICKS` / `CONFIG::W_LATE_TICKS` - te same, którymi
liczy się Warunek A/B w `noise_world` i K4-A/K4-B w `pure_noise_world`. **Nie** okna
zakotwiczone w `shock_tick` (te należą wyłącznie do K3a, patrz zastrzeżenie niżej) -
uzasadnienie CTO: gdyby jedna strona porównania używała okien Primary, a druga okien
szokowych, kontrola przestałaby być separacją **środowisk** i zaczęłaby mieszać dwa różne
endpointy w jednym teście.

**Metoda liczenia `redukcja_W2` musi być IDENTYCZNA (to samo wywołanie tej samej funkcji)
po obu stronach porównania** - inaczej test Manna-Whitneya porównywałby dwie różne wielkości
pod jedną nazwą.

**Nie wyznacza się nowej zamrożonej podłogi dla `shock_world`.** Rozważano to jako wariant
dosłowny (nowy pomiar Monte Carlo, 100 000 realizacji, test ważności V-C) i **odrzucono** -
CTO wybrał wariant zgodny z uzasadnieniem (ten dokument), bo nie wymaga żadnych nowych
obliczeń i usuwa sprzeczność u źródła, zamiast dorabiać infrastrukturę pod błędnie
zredagowane zdanie.

---

## Zastrzeżenie: K3a nietknięte

To erratum dotyczy **wyłącznie** K4-separacja. K3a (warunek 1) **nie zmienia się** -
środowisko (`shock_world`), okna (`[shock_tick-20, shock_tick-1]` / `[shock_tick,
shock_tick+20]`, PC-001 §5 → „K3") i test (`STATS::wilcoxon_signed_rank(alternative='greater')`)
pozostają dokładnie takie, jak w ANEKS 1 i `publications/pc_001_bh_family.json`.

## Zastrzeżenie: K4-A i K4-B nietknięte, nadal pod Negative-Control Inference Review

K4-A i K4-B (obie strony „brak efektu w czystym szumie") nie są przedmiotem tego erratum -
pozostają pod otwartym Negative-Control Inference Review (B4C-2 (06), decyzja CTO pkt 7/8),
tak samo jak K1-A, K1-B, K5-A, K5-B.

## Skład rodziny bez zmian

`m = 11` i `N_operational = 9` **bez zmian**. To erratum nie zmienia liczby komórek ani
liczby seedów - koryguje wyłącznie **które środowisko** jest drugą stroną porównania w
JEDNEJ z jedenastu już istniejących komórek.

---

## Zamrożenie

Po zatwierdzeniu erratum zostaje zamrożone jako
`publications/preregistration_PC_001_ERRATUM_1_2026-08-27.json`, z hashem w rejestrze
(`CRITICAL_FILES_PC_001`, razem z tym dokumentem .md). Korekta wykonana **przed pierwszym
przebiegiem konfirmacyjnym PC-001** i **przed policzeniem `PC_001_BASELINE`** (B5).

---

*Wykonalność zweryfikowana w kodzie: `CONFIG::FROZEN_FLOOR_NOISE_WORLD` i
`CONFIG::FROZEN_FLOOR_PURE_NOISE_WORLD` istnieją i są używane przez
`clos_scientist/w2_endpoint.py::compute_pe_reducible`; brak analogicznej stałej dla
`shock_world` zweryfikowany przeglądem `clos_scientist/pc_001_experiment_config.py` i
`execution_package_v0_11/runners/pc_001_confirmatory_runner.py::verify_floors_before_run`.*

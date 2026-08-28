# ERRATUM 2 do publications/power_analysis_PC_001.json

**Data:** 2026-08-29
**Status:** **ZATWIERDZONY** decyzją **CTO**, B4C-2 (12)
**Podstawa:** audyt CTO po pushu B4C-2 (11) - `CONFIG::N_OPERATIONAL_SEEDS` (8) rozjechany z
`publications/pc_001_bh_family.json::N_operational` (9), zamrożonym m=11.
**Autor:** CTO (rozstrzygnięcie i audyt), wykonawca (szkic techniczny)
**Rodzaj dokumentu:** **ERRATUM** - poprawka do wartości wykonawczej zapisanej w
`publications/power_analysis_PC_001.json`, nie doprecyzowanie. Ten plik pozostaje
**NIETKNIĘTY** w swoim pierwotnym brzmieniu (nie edytujemy w miejscu - historia liczenia
mocy dla m=4 ma zostać prawdziwa, taka, jaka była); to erratum nadpisuje wartość
wykonawczą **NORMATYWNIE**, nie tekstowo.

> **DOPUSZCZALNOŚĆ ERRATUM:** D-006 pkt 3 zakazuje zmian w kryteriach *„po rozpoczęciu
> zbierania danych"*. Blok seedów konfirmacyjnych (1001-1050, `CONFIRMATORY_SEEDS_RESERVED`)
> pozostaje **nietknięty** - żaden przebieg na tych seedach nie został wykonany.
> `PC_001_BASELINE` pozostaje `TBD` (B5 wstrzymane). Erratum jest więc dopuszczalne **dziś**.

---

## Powód erratum

Podczas audytu pushu B4C-2 (11) CTO znalazł, że `CONFIG::N_OPERATIONAL_SEEDS` (8) i
`publications/pc_001_bh_family.json::N_operational` (9) mówią różne liczby. Test
prowieniencji (`tests/test_n_operational_seeds_provenance.py`) był **zielony** - ale
wiązał `CONFIG` z `publications/power_analysis_PC_001.json`, czyli ze źródłem, które
**przestało obowiązywać** w momencie zamrożenia rodziny BH na m=11 (B4C-05). Straznik nie
przeoczył rozjazdu - **poświadczył** go, bo porównywał dwie rzeczy, z których jedna była
już historią.

**Dlaczego 8 nie wystarcza dziś:** `power_analysis_PC_001.json` wyprowadziło N_operational=8
dla rodziny **czterech** testów (A, B, K4, K6, `m_tests=4`), z najostrzejszym progiem BH
`(1/4)*0.05 = 0.0125`. Rodzina BH została od tego czasu zamrożona na **m=11**
(B4C-05, decyzja CTO) - najostrzejszy próg BH spadł do `(1/11)*0.05 = 0.004545454545454546`.

**Dosłowny cytat źródła (`publications/power_analysis_PC_001.json`,
`required_seeds.n_operational`):**

> „source": „NIE Z MONTE CARLO. Decyzja CTO (B4B-03, pkt 2), oparta na rozdzielczosci
> dokladnego testu Wilcoxona wobec prerejestrowanej korekty BH-FDR - nie na marginesie
> bezpieczenstwa ani na dodatkowej symulacji."

> „definition": „Pierwsze N, przy ktorym minimalna OSIAGALNA (nie zaobserwowana)
> dwustronna wartosc p dokladnego testu Wilcoxona spada PONIZEJ najostrzejszego progu BH
> w rodzinie czterech testow (A, B, K4, K6) - czyli przy ktorym pojedynczy test MOZE
> przejsc korekte samodzielnie, niezaleznie od tego, jak wypadna pozostale trzy."

> „crossing": „n=7: min p=0.015625 > 0.0125 (NIE wystarcza). n=8: min p=0.0078125 < 0.0125
> (wystarcza). N_operational=8 jest najmniejszym n spelniajacym warunek."

Definicja sama w sobie jest wciąż poprawna - **liczba testów w mianowniku (`m_tests=4`)
przestała być prawdziwa.** Przy dzisiejszym m=11: minimalne osiągalne dwustronne p
dokładnego testu Wilcoxona przy n=8 wynosi **0.0078125**; najostrzejszy próg BH przy
m=11 wynosi **0.004545454545454546**. `0.0078125 > 0.004545454545454546` - **dziesięć
z jedenastu komórek** (wszystkie oprócz K3a-warunek1, jedynej jednostronnej) formalnie
**nie mogą** osiągnąć istotności po korekcie, niezależnie od danych. Eksperyment
uruchomiony dziś na n=8 zwróciłby NIE WSPARTA z konstrukcji, spalając osiem seedów z
bloku zarezerwowanego bez możliwości pozytywnego wyniku.

---

## Poprawka

**Wartość wykonawcza `required_seeds.n_operational.value = 8` z
`publications/power_analysis_PC_001.json` zostaje NORMATYWNIE ZASTĄPIONA przez
`N_operational = 9`, na podstawie finalnej rodziny BH `m=11`
(`publications/pc_001_bh_family.json::N_operational`).**

Przy n=9: minimalne osiągalne dwustronne p Wilcoxona = 0.00390625, próg BH przy m=11 =
0.004545454545454546 - `0.00390625 <= 0.004545454545454546`, margines 0.00063920 (mały,
ale realny). n=9 jest najmniejszym n spełniającym warunek dla dzisiejszej rodziny.
Pełna tabela: `publications/pc_001_bh_family.json::tabela_osiagalnosci_p`.

**Historyczna wartość 8 POZOSTAJE elementem proweniencji B4b i NIE JEST już wartością
wykonawczą PC-001.** `publications/power_analysis_PC_001.json` NIE jest edytowany w
miejscu - nadpisanie starego JSON-a zatarłoby fakt, że analiza mocy B4b **prowadziła
wtedy do 8**, a dopiero późniejsza analiza rodziny m=11 pokazała, że 8 już nie wystarcza.
Ten fakt historyczny (n=8 był poprawnym wynikiem dla m=4 w chwili policzenia) ma zostać
**prawdziwy i czytelny**, nie zastąpiony po cichu.

**Źródłem wykonawczym dla N jest odtąd wyłącznie
`publications/pc_001_bh_family.json::N_operational`.** `CONFIG::N_OPERATIONAL_SEEDS`
czyta tę wartość (przepisaną ręcznie, z adresem w komentarzu - `pc_001_bh_family.json`
nie jest importowalnym modułem Pythona) i `CONFIRMATORY_SEEDS` wyprowadza się z niej
automatycznie (`range(CONFIRMATORY_SEEDS_START, CONFIRMATORY_SEEDS_START +
N_OPERATIONAL_SEEDS)` - zakres 1001-1009 powstaje sam, nie jest wpisywany osobno).

---

## Zastrzeżenia

**m=11 BEZ ZMIAN.** To erratum nie otwiera ponownie decyzji o składzie rodziny BH -
koryguje wyłącznie liczbę seedów wymaganą przez rodzinę, która już jest zamrożona.

**Blok zarezerwowany (1001-1050) BEZ ZMIAN**, w tym jego górna granica -
`CONFIRMATORY_SEEDS_RESERVED_MAX_N=50` ma zapas znacznie większy niż wymagany wzrost
8→9 (uzasadnienie logarytmicznego marginesu, patrz `CONFIG`, komentarz nad
`CONFIRMATORY_SEEDS_RESERVED`).

**`publications/power_analysis_PC_001.json` POZA rejestrem `CRITICAL_FILES_PC_001`
pozostaje** - nie zmienia żadnej liczby produkowanej przez eksperyment (to erratum,
zarejestrowane, robi to zamiast niego).

---

## Zamrożenie

Po zatwierdzeniu erratum zostaje zamrożone jako
`publications/preregistration_PC_001_ERRATUM_2_2026-08-29.json`, z hashem w rejestrze
(`CRITICAL_FILES_PC_001`, razem z tym dokumentem .md). Korekta wykonana **przed
pierwszym przebiegiem konfirmacyjnym PC-001** i **przed policzeniem `PC_001_BASELINE`**
(B5).

---

*Wykonalność zweryfikowana w kodzie: `CONFIG::CONFIRMATORY_SEEDS` jest wyprowadzony
(`range(...)`), nie wpisany na sztywno - podniesienie `N_OPERATIONAL_SEEDS` z 8 na 9
przelicza zakres seedów samo, bez osobnej edycji. Trzy miejsca poza CONFIG (harmonogram
checkpointów runnera, jego komentarz, jeden test) trzymały liczbę 552 (23×8×3) jako
literal - poprawione osobno, patrz commit.*

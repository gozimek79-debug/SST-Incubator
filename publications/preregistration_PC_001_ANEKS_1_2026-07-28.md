# ANEKS 1 do PREREJESTRACJI PC-001

**Data:** 2026-07-28
**Status:** **ZATWIERDZONY** decyzją **CTO D-007** · doprecyzowania D-007 pkt 1–2 naniesione
**Podstawa:** recenzja niezależnego neurocybernetyka (8.0/10) · D-007 · §12 PC-001 (mechanizm aneksów)
**Autor:** audytor niezależny

> **DOPUSZCZALNOŚĆ ANEKSU:** D-006 pkt 3 zakazuje zmian w kryteriach *„po rozpoczęciu zbierania
> danych"*. **Żadne dane PC-001 nie istnieją** — eksperyment nie został uruchomiony (baseline
> `PC_001_BASELINE` nie jest jeszcze ustalony, `Snapshot` nie niesie jeszcze `prediction`/`input`,
> analiza mocy nie została wykonana). Aneks jest więc dopuszczalny **dziś** i **niedopuszczalny
> po pierwszym przebiegu.** To ostatni moment, w którym wzmocnienie kryteriów nie jest
> dostosowywaniem ich do wyniku.

---

## Powód aneksu

Recenzja zewnętrzna wskazała, że **kontrola K3 w pierwotnym brzmieniu przepuściłaby habituację
jako Predictive Coding.** Zarzut jest trafny: kryterium „PE rośnie po wstrząsie, potem maleje"
opisuje równie dobrze wygaszanie reakcji na nowy bodziec, które nie jest przewidywaniem.

Aneks wzmacnia cztery punkty. **Każda zmiana zawęża, żadna nie rozszerza** przestrzeni wyników
uznawanych za wsparcie hipotezy.

---

## Zmiana 1 — K3 wzmocnione (habituacja vs model generatywny)

**Pierwotne brzmienie** (`shock_world`, dwa warunki: wzrost PE po wstrząsie, ponowny spadek)
**pozostaje w mocy jako warunek konieczny.**

**Dodany warunek trzeci**, w środowisku `recurring_shock_world` (wstrząsy co `interval = 40` ticków,
offset deterministyczny z seeda; przy 300 tickach ≈ 7 powtórzeń):

> **Czas ponownej adaptacji musi maleć przy kolejnych wstrząsach — kierunkowo I w wielkości.**
>
> Operacjonalizacja: dla każdego wstrząsu `i` zdefiniuj `recovery_i` = liczba ticków od wstrząsu
> do momentu, w którym `PE` wraca poniżej średniej z okna `[shock_i − 20, shock_i − 1]`.
>
> **Warunek K3b-1 (kierunek):** **Kendalla tau < 0**, istotne (`p < 0.05`). Tau wybrane zamiast
> `β` regresji: jest nieparametryczne (spójnie z całym protokołem) i **samo jest miarą wielkości
> efektu**, nie tylko kierunku.
>
> **Warunek K3b-2 (wielkość):** mediana `recovery_i` w **drugiej połowie** wstrząsów musi być
> **co najmniej 20% krótsza** niż w pierwszej połowie. Przy `interval = 40` i 300 tickach daje
> to ≈7 wstrząsów → porównanie 1–3 vs 5–7 (środkowy pomijany przy nieparzystej liczbie).
>
> **Oba warunki wymagane.** Struktura jest celowo identyczna z Primary Endpoint (kierunek +
> wielkość), bo adresuje ten sam problem: sam trend przepuszcza szereg typu `5 4 5 4 3 4`,
> gdzie `β < 0` przy praktycznie zerowym efekcie.
>
> **Próg 20% w K3b-2 jest tą samą konwencją projektu co w Primary Endpoint** (patrz Zmiana 4) —
> nie jest wyprowadzony z literatury. Użyty dla spójności wewnętrznej protokołu.

**Uzasadnienie dyskryminacyjne:**

| Mechanizm | Przewidywanie dla `recovery_i` |
|---|---|
| **Habituacja / sensytyzacja** | wzorzec podobny przy każdym wstrząsie; `recovery` **nie maleje systematycznie** |
| **Uczenie sekwencji** (T5) | brak modelu okresowości → `recovery` stabilne |
| **Model generatywny (PC)** | system uczy się **okresowości** wstrząsów → `recovery` **maleje**, skok PE się kurczy |

**Falsyfikacja:** brak malejącego trendu `recovery_i` → nie da się odróżnić od habituacji.
**Hipoteza nie została wsparta.**

**Odrzucona alternatywa:** recenzent proponował „powrót do pierwotnych reguł → PE musi znów
wzrosnąć". Odrzucone, bo test jest niediagnostyczny: system z **zachowanym** modelem regime'u A
powinien po powrocie być **mniej** zaskoczony, nie bardziej. Kryterium wskazywałoby w złą stronę.

---

## Zmiana 2 — K6 (nowa kontrola): responsywność na świat

**Adresuje T1** („system redukuje PE, bo przestał reagować na świat") — dotąd zapisany jako problem
otwarty, niemierzony.

**Charakter:** kontrola **analityczna post-hoc**, **zero dodatkowych przebiegów.** Możliwa dzięki
zapisowi `prediction` i `input` osobno (D-004 pkt 3, zasada O-001).

**Procedura:** dla każdego przebiegu policzyć **korelację `prediction(t)` z `input(t)`**
(Spearman, nieparametrycznie) po całym mierzalnym oknie.

**Kryterium PC:** korelacja musi być **istotnie różna od zera**. Predykcja **musi** współzmieniać
się z wejściem.

**Falsyfikacja:** predykcja stała lub nieskorelowana z wejściem → system nie modeluje świata,
tylko zbiegł do wartości minimalizującej metrykę. **T1 potwierdzone, hipoteza nie została wsparta** —
niezależnie od spełnienia Primary Endpoint.

**Uwaga interpretacyjna (wymagana przez D-007 pkt 1):**

> **K6 wyklucza brak reakcji na świat, lecz NIE stanowi samodzielnego dowodu istnienia modelu
> generatywnego.** Wysoka korelacja `prediction ≈ input(t)` jest osiągalna przez zwykły filtr
> lub opóźnione powtórzenie wejścia — bez jakiegokolwiek przewidywania. K6 jest warunkiem
> **koniecznym, nie wystarczającym**.

K6 nie zastępuje pełnego testu funkcji (roadmapa, §10 PC-001) — wyklucza jedynie najgrubszy
przypadek: system całkowicie odklejony od wejścia. **W raporcie końcowym K3 (adaptacja)
i K6 (sprzężenie ze światem) muszą być raportowane w OSOBNYCH sekcjach** — mierzą różne
własności i nie wolno ich przedstawiać jako jednego wyniku (uwaga CTO, D-007).

---

## Zmiana 3 — K4 przeformułowane: separacja zamiast dwóch progów

**Pierwotne brzmienie:** „w `pure_noise_world` nie wolno uzyskać spełnienia A ani B".

**Problem** (wskazany przez recenzenta): przy 22% w środowisku realnym i 19% w czystym szumie
kryterium **formalnie przechodzi**, choć nie różnicuje niczego.

**Nowe brzmienie:**

> Efekt w środowisku inferencyjnym (`shock_world`) musi **istotnie przewyższać** efekt
> w `pure_noise_world` — porównanie rozkładów `redukcja` między środowiskami
> (Mann-Whitney U, `p < 0.05` po FDR), **oprócz** pierwotnego wymogu, że `pure_noise_world`
> nie spełnia A ani B.

**Odrzucona alternatywa:** recenzent proponował próg absolutny „mediana w szumie < 10%".
Odrzucone — to kolejna arbitralna liczba obok arbitralnego 20%. **Separacja statystyczna jest
mocniejsza i nie wymaga zgadywania progu.**

---

## Zmiana 4 — jawne oznaczenie pochodzenia progu 20%

Recenzent słusznie wskazał brak uzasadnienia. **Uczciwa odpowiedź, nie uzasadnienie dorobione
po fakcie:**

> **Próg 20% jest konwencją projektu**, przyjętą w AIA v4. **Nie jest wyprowadzony z literatury
> przedmiotu** ani z analizy oczekiwanej wielkości efektu w tej architekturze. Jest arbitralną,
> ale **zapisaną z góry** poprzeczką — jego wartością jest niezmienność, nie trafność.
>
> **Zmiana progu po obejrzeniu danych jest niedopuszczalna** i unieważnia prerejestrację.
> Jeśli wynik wypadnie blisko progu (np. 18% lub 22%), raportuje się **liczbę i decyzję progową
> osobno** — bez przeformułowywania kryterium.

---

## Zmiana 5 — artefakt analizy mocy: wskazana ścieżka

Analiza mocy była już wymagana (§2.3, §11 pkt 4, D-005 pkt 3), ale bez wskazania miejsca zapisu.

> Wynik analizy mocy zapisywany jako **`publications/power_analysis_PC_001.json`**, przed
> uruchomieniem eksperymentu, jako datowany artefakt podlegający audytowi.

---

## Zaktualizowana reguła decyzyjna (§6 PC-001 + aneks)

Hipotezę o obecności mechanizmu zgodnego z Predictive Coding uznaje się za **wspartą** wyłącznie
gdy **wszystkie** warunki zachodzą dla L1.2:

| # | Warunek | Źródło |
|---|---|---|
| 1 | **A** — `β < 0` istotne (trend malejący) | PC-001 §2.1 |
| 2 | **B** — mediana redukcji **≥ 20%** (konwencja, patrz Zmiana 4) | PC-001 §2.1 |
| 3 | `p < 0.05` po FDR | PC-001 §2.2 |
| 4 | **K1** — efekt nie występuje w danych przetasowanych | PC-001 §5 |
| 5 | **K3a** — PE rośnie po wstrząsie i ponownie maleje | PC-001 §5 |
| 6 | **K3b** — **czas ponownej adaptacji maleje przy kolejnych wstrząsach** | **Aneks, Zmiana 1** |
| 7 | **K4** — brak efektu w czystym szumie **ORAZ istotna separacja** od środowiska realnego | **Aneks, Zmiana 3** |
| 8 | **K5** — efekt znika po ablacji surogatowej | PC-001 §5 |
| 9 | **K6** — **predykcja istotnie skorelowana z wejściem** | **Aneks, Zmiana 2** |

**K2** (`stable_world`) pozostaje **przesłanką opisową, poza inferencją statystyczną** (D-005 pkt 4).

---

## Zaktualizowana tabela Threats → kontrola

| # | Zagrożenie | Kontrola rozstrzygająca |
|---|---|---|
| T1 | system przestaje reagować na świat | **K6** (było: brak testu) |
| T2 | predykcja zbiega do średniej | **K4 z separacją** (było: K4 z progiem absolutnym) |
| T3 | amplituda sygnału maleje | K2 (opisowo) |
| T4 | efekt podłogi | Warunek A + inspekcja trajektorii; **PC-002** |
| T5 | uczenie sekwencji, nie przewidywanie | K3a |
| **T6** | **habituacja / sensytyzacja** | **K3b** (nowe zagrożenie, wcześniej nieadresowane) |

---

## Nowe wymagania techniczne (uzupełnienie §11 PC-001)

| # | Wymaganie | Podstawa |
|---|---|---|
| 6 | Przebiegi w `recurring_shock_world` (K3b) — środowisko **istnieje**, nie wymaga budowy | Aneks, Zmiana 1 |
| 7 | `Snapshot` musi nieść `prediction` **i** `input` osobno — bez tego **K6 i K5 są niewykonalne** | D-004 pkt 3, Aneks Zmiana 2 |
| 8 | Analiza mocy obejmuje także testy K3b (trend `recovery_i`) i K4 (separacja) | Aneks, Zmiany 1 i 3 |

---

## Do decyzji CTO (poza zakresem aneksu — governance, nie metodologia)

Recenzent zaproponował zobowiązanie: *„jeśli PC-001 pozytywny, PC-002 musi zostać uruchomiony
w ciągu X miesięcy, inaczej PC-001 nie może być publikowany jako dowód uczenia się"*.

**Termin jest decyzją CEO/CTO, nie audytora.** Ale jedna część jest metodologiczna i **rekomendowana
do wpisania niezależnie od terminu:**

> PC-001 sam w sobie **nie może być publikowany jako dowód uczenia się.** Dopuszczalne jest
> wyłącznie twierdzenie o **danych zgodnych z redukcją błędu predykcji** w warunkach
> wykluczających kontrole K1, K3–K6. Twierdzenie o uczeniu wymaga PC-002 (kształt trajektorii)
> i testu generalizacji.

To wzmocnienie klauzuli językowej z §6 PC-001 (D-006 pkt 2).

---

## Zasada konserwatywnej interpretacji — kategoria INCONCLUSIVE (D-007 pkt 2)

Wynik eksperymentu klasyfikuje się **trójwartościowo**, nie binarnie:

| Kategoria | Warunek | Interpretacja |
|---|---|---|
| **WSPARTA** | Primary Endpoint (1–3) **oraz wszystkie** kontrole (4–9) spełnione | dane zgodne z hipotezą PC |
| **INCONCLUSIVE** | Primary Endpoint spełniony, **ale ≥1 kontrola mechanistyczna (K1–K6) nie przechodzi** | **ani wsparcie, ani obalenie**; podstawa do PC-002 |
| **NIE WSPARTA** | Primary Endpoint niespełniony | hipoteza nie została wsparta w tym układzie |

> **Wynik INCONCLUSIVE nie wspiera ani nie obala hipotezy Predictive Coding.** Oznacza, że błąd
> predykcji spada, ale **nie udało się wykluczyć alternatywnych wyjaśnień**. Taki wynik stanowi
> podstawę do opracowania kolejnej prerejestracji (PC-002) i **nie może być prezentowany jako
> wsparcie hipotezy** — także w streszczeniach, prezentacjach i komunikacji zewnętrznej.

**Uzasadnienie kategorii:** w praktyce naukowej znaczna część wyników jest niejednoznaczna.
Wymuszanie klasyfikacji PASS/FAIL prowadzi do dwóch błędów: nadinterpretacji wyniku częściowego
jako sukcesu albo odrzucenia obiecującego kierunku jako porażki. Kategoria INCONCLUSIVE chroni
przed obydwoma.

**Uwaga o mocy:** wynik NIE WSPARTA musi być raportowany łącznie z osiągniętą mocą statystyczną
(§7 PC-001). Bez tej liczby nie wolno go zapisać jako `MEASURED_BUT_NULL` — to bezpośrednia
lekcja P0.

---

## Zamrożenie

Po zatwierdzeniu aneks zostaje zamrożony razem z PC-001 jako
`publications/preregistration_PC_001_ANEKS_1_2026-07-28.json`, z hashem w rejestrze.
Od momentu pierwszego przebiegu **żadne dalsze zmiany kryteriów nie są dopuszczalne** — wyłącznie
nowa prerejestracja (PC-002).

---

*Wykonalność zweryfikowana w kodzie: `recurring_shock_world` istnieje (`clos_world/scenarios.py:54`,
`interval = 40`, offset deterministyczny z seeda). K6 i K5 wymagają zapisu `prediction`/`input`
osobno — zatwierdzonego w D-004, jeszcze niezaimplementowanego.*

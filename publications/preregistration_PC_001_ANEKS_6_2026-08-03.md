# ANEKS 6 do PREREJESTRACJI PC-001 — mechanizm predykcji: korekta wyjaśnienia, nie wniosku

**Od:** audytor niezależny · **Dla:** CTO
**Data:** 2026-08-02 · klon `v0.7.2-scientific-integrity` @ `be43712`
**Status:** **ZATWIERDZONY.** Warunek z §7 **spełniony** — patrz §7.1.
**Podstawa:** decyzje CTO z 2026-08-02 (K7 → Typ M · T7 pozostaje · korekta przez aneks,
nie nadpisanie · studium wstrzymane) · G-001 · G-004 · D-017

**Przedmiot znaleziska (G-005):** **CORE** — właściwość badanego systemu, nie błąd metodologii
i nie usterka infrastruktury.
**Klasyfikacja poprawki (G-001):** **Typ M** dla K7 — decyzja CTO, warunkowa, patrz §7.

> **Konwencja etykiet — rozstrzygnięta (CEO, 2026-08-02).** Oś przedmiotu używa nazw pełnych:
> **METODOLOGIA / INFRASTRUKTURA / CORE**. Litery **M** i **I** pozostają zarezerwowane
> wyłącznie dla G-001 (Measurement Failure / Interpretation Improvement), żeby „Typ I" nigdy
> nie był dwuznaczny. Obie osie są **ortogonalne**: ten dokument jest przykładem przedmiotu
> CORE przy poprawce Typu M.

---

## Jeden temat

Mechanizm, którym `predict()` wytwarza predykcję po wstrząsie, jest inny niż opisany
w Aneksie 2 (T7, K7) i w Aneksie 5 (uzasadnienie zawieszenia warunku 2 K3a).

**Obserwacje z obu aneksów pozostają w mocy. Zmienia się model wyjaśniający.**
Aneksy 2 i 5 nie są nadpisywane ani wycofywane — pozostają jako ślad tego, dlaczego
sądzono inaczej.

---

## 1. Co ustalono

### 1.1 Arytmetyka — nie wymaga eksperymentu

`clos_brain/runtime/prediction.py`, warunek doboru rekordów pamięci:

```
abs(r.stimulus_hash - input_hash) < brain.attention_threshold * 1000
```

- `_hash_stimulus()` zwraca liczbę całkowitą z `[0, 100]` → maksymalny możliwy dystans
  wynosi 100.
- `attention_threshold` jest stały we wszystkich 23 genomach w ścieżce lekcji L1.1/L1.2
  (`BrainTissue` używa wartości domyślnej dataclass; `clos_curriculum/laboratory/population.py`
  nie umieszcza tego pola wśród wymiarów LHS; lekcje go nie czytają) → próg wynosi 300.

> **Warunek jest spełniony zawsze, gdy pamięć jest niepusta.** `matching_records` to **cała
> pamięć**, nie jej podzbiór. Gałąź `else` — awaryjna, licząca średnią kroczącą wejść — jest
> osiągalna wyłącznie przy pustej pamięci.

### 1.2 Pomiar potwierdzający

Instrumentacja `predict()`, 300 ticków, genom `default`, cztery środowiska, seedy 1–3:
gałąź pamięciowa 299 wywołań, gałąź awaryjna 1 (tick 0, pamięć jeszcze pusta). Bez wyjątku.

**Skażenie: brak.** Mierzono **którą gałęzią biegnie wykonanie**, nie żadną wielkość
wchodzącą do reguły decyzyjnej. Seedy z zakresu pilota, rozłączne z konfirmacją. Nic nie
zapisano na dysk.

### 1.3 Czym jest predykcja w gałęzi pamięciowej

Średnia ważona pól `record.prediction`, z wagami `1/(1+error)`. Pola te są inicjalizowane
wartością `brain.last_input` (`plasticity.py`, gałąź dodania rekordu) i przy niskim błędzie
przyciągane dalej ku `last_input`. Inspekcja pamięci po przebiegu potwierdza: każdy rekord
przechowuje wartość odpowiadającą swojemu bucketowi wejścia.

**Predykcja jest zatem filtrem po przeszłych wejściach** — tyle że innym niż zakładano.

---

## 2. Konsekwencja dla T7 — zagrożenie pozostaje, mechanizm inny

**Decyzja CTO: T7 pozostaje, zmienia się opis mechanizmu. Testu nie usuwa się.**

T7 (Aneks 2, Zmiana 6) opisuje zagrożenie: *predykcja skorelowana z wejściem bez modelu
generatywnego, bo jest średnią kroczącą wejścia.* Zagrożenie jest **realne i szersze**, niż
zapisano — realizuje się nie w gałęzi awaryjnej (raz na przebieg), lecz w gałęzi pamięciowej
(praktycznie cały przebieg).

**Brzmienie obowiązujące T7 po tym aneksie:**

| # | Mechanizm trywialny | Dlaczego daje spadek PE | Która kontrola go odróżnia |
|---|---|---|---|
| **T7** | **Predykcja jako filtr po przeszłych wejściach** — średnia ważona zapamiętanych wartości, inicjalizowanych i aktualizowanych z `input` | predykcja współzmienia się z wejściem **bez modelu generatywnego**; korelacja `prediction`↔`input` powstaje z konstrukcji pamięci, nie z przewidywania | **K4** (separacja), **K5** (ablacja). **K7 — patrz §3** |

Zmiana jest **zawężająca**: zagrożenie okazuje się obejmować cały przebieg, a nie jeden tick.

---

## 3. Konsekwencja dla K7 — Typ M (decyzja CTO, warunkowa)

**Decyzja CTO: Typ M.** Uzasadnienie CTO: kontrola nie obserwuje mechanizmu, który deklaruje
obserwować; nie blokuje Primary Endpointu, ale nie spełnia swojej funkcji kontrolnej.

K7 (Aneks 2, Zmiana 7) szacuje odsetek ticków w gałęzi awaryjnej, z progami interpretacyjnymi
przyjętymi z góry. Strukturalnie odsetek ten wynosi jeden tick na przebieg — **poniżej
najniższego progu w każdym genomie, środowisku i seedzie**. K7 będzie więc zawsze raportować,
że K6 jest wiarygodny; nie dlatego, że jest, tylko dlatego, że mierzona wielkość jest
strukturalnie bliska zeru.

### 3.1 Skutek dla reguły decyzyjnej: żaden

K7 nie wchodzi do reguły decyzyjnej (Aneks 2 stwierdza to wprost). Nie może więc spowodować
błędnego wsparcia ani błędnego odrzucenia hipotezy. **Reguła decyzyjna pozostaje bez zmian.**

### 3.2 Skutek dla raportowania K6: istotny i wymaga zapisania

Aneks 1 (Zmiana 2) zastrzega, że **K6 jest warunkiem koniecznym, nie wystarczającym**.
Aneks 2 wprowadził K7 jako narzędzie, które pozwala ocenić, na ile K6 jest wiarygodny.

> **Po tym aneksie K6 pozostaje aktywnym warunkiem decyzyjnym, ale traci diagnostykę, która
> miała go kwalifikować.** Raport końcowy nie może przedstawiać K6 jako zweryfikowanego przez
> K7. Musi natomiast zawierać jawne stwierdzenie, że mechanizm wytwarzania predykcji
> (§1.3) czyni dodatnią korelację `prediction`↔`input` **oczekiwaną z konstrukcji**,
> niezależnie od obecności Predictive Coding.

To jest zaostrzenie, nie złagodzenie: czytelnik dostaje mocniejsze zastrzeżenie niż dotąd.

### 3.3 Czego ten aneks NIE proponuje

**Nie proponuje nowej definicji K7 ani zastępczej kontroli mechanizmu.** Kontrola obserwująca
gałąź pamięciową byłaby **nową kontrolą** i podlega G-003 — sześciu wymaganiom jednocześnie,
w tym mechanicznej klasyfikacji typu danych dla analizy mocy. Zaprojektowanie jej „przy okazji"
tego aneksu powtórzyłoby wzorzec, który unieruchomił K3b.

Rekomendowany status K7 do czasu takiego projektu: **zawieszona jako diagnostyka K6, zdefiniowana
i nieusunięta** — analogicznie do K3b (ARCHITECTURE-LIMITED) i warunku 2 K3a (SUSPENDED PENDING
WINDOW REDEFINITION). Etykieta statusu należy do CTO.

---

## 4. Konsekwencja dla Aneksu 5 — uzasadnienie, nie wniosek

**Decyzja CTO: Aneksu 5 nie poprawiać. Korekta przez ten aneks.**

Aneks 5 wyjaśnia niepowodzenie warunku 2 K3a tak: *gałąź awaryjna `predict()` to średnia
z ostatnich `prediction_depth` wejść; przy stałym post-wstrząsowym plateau ta średnia zbiega
w kilka ticków.*

Gałąź awaryjna nie działa po wstrząsie. Zbieżność zachodzi **w gałęzi pamięciowej**, rządzonej
strukturą bucketów, wagami `1/(1+error)`, kolejnością wstawiania rekordów i zanikiem pamięci.

**Co pozostaje w mocy:**

- dowód trajektoryjny (`PE` spada do pasma szumu w kilka ticków) — jest obserwacją, nie
  wyjaśnieniem, i nie zależy od tego, która gałąź go wyprodukowała;
- pomiar zbiorczy warunku 1 i warunku 2 K3a;
- **status warunku 2 K3a: SUSPENDED PENDING WINDOW REDEFINITION — bez zmian**;
- **status warunku 1 K3a: aktywny, gwarantowany strukturalnie — bez zmian**;
- klasyfikacja Typ M dla warunku 2 K3a — bez zmian.

**Co przestaje obowiązywać:** twierdzenie, że skala czasowa readaptacji jest prostą funkcją
`prediction_depth`, a więc wielkością przewidywalną bez uruchamiania systemu. To twierdzenie
było jedyną podstawą do uznania, że okna da się przeprojektować na podstawie samego generatora
i parametrów genomu.

---

## 5. Konsekwencja dla K3a Window Design Study — wstrzymane

**Decyzja CTO: wstrzymać.**

Studium miało odpowiedzieć, jakie okna rzeczywiście mierzą readaptację. Pierwszym krokiem wg
G-003 pkt 6 jest mechaniczna klasyfikacja typu danych potrzebnych do zaplanowania mocy —
i klasyfikacja ta zależy od mechanizmu:

| Mechanizm | Skala czasowa zależy od | Typ danych (G-003 pkt 6) | Skutek dla pkt 4 |
|---|---|---|---|
| jak w Aneksie 5 | generatora + stałego parametru genomu | dane środowiska | spełniony |
| jak w implementacji | trajektorii stanu pamięci w przebiegu | **nierozstrzygnięte; możliwe, że dane eksperymentalne** | jeśli eksperymentalne → **automatycznie niespełniony** |

Druga linijka to ta sama pułapka co przy K3b. **Rozstrzygnięcie wymaga osobnego zadania:**
czy skalę czasową readaptacji da się wyprowadzić z generatora i struktury pamięci **bez
uruchamiania mózgu** — analogicznie do `clos_world/floor_model.py`, gdzie podłogę wyznaczono
z generatora, nie z przebiegów.

**G-003 zadziałał zgodnie z przeznaczeniem.** Przy K3b luka wyszła sześć tur po zaprojektowaniu
kontroli. Tutaj — przed napisaniem pierwszej linijki projektu.

---

## 6. Obserwacje o badanym systemie — nie propozycje zmian

Zapisane jako **wynik badań nad CLOS v0.11**, nie jako usterki. G-004 zakazuje modyfikowania
Core, żeby kontrola stała się wykonalna; poprawienie któregokolwiek z poniższych stworzyłoby
nową wersję badanego systemu.

- **`attention_threshold` jest w tej konfiguracji bezczynny.** Dla dowolnej wartości powyżej
  `0.1` próg przekracza maksymalny możliwy dystans hashy. Filtr „podobieństwa bodźca" nie
  filtruje.
- **`prediction_depth` nie wybiera rekordów najbardziej podobnych ani najświeższych.**
  `matching_records[-prediction_depth:]` to ostatnie pozycje listy w kolejności **wstawiania**,
  czyli buckety najpóźniej zobaczone po raz pierwszy; aktualizacja rekordu nie zmienia jego
  pozycji.

Precedens rozstrzygnięcia jest ten sam co przy nasyceniu entropii (Aneks 4, D-026): zweryfikowana
właściwość badanego modelu, nie usterka.

---

## 7. Warunek zamrożenia — WIĄŻĄCY

> **Ten aneks nie może zostać zamrożony, dopóki znalezisko z §1 nie zostanie potwierdzone
> niezależnie przez wykonawcę** (zlecenie Z1).

Powód proceduralny: cała treść aneksu opiera się na pomiarze i inspekcji wykonanych przez
audytora. Audytor nie zatwierdza własnej pracy — zasada zapisana w obiegu pracy, wielokrotnie
potwierdzona w tym projekcie wychwyceniem błędów audytora przez wykonawcę.

**Punkt wymagający szczególnej uwagi przy weryfikacji:** czy `apply_decay()` może **opróżnić
pamięć w trakcie przebiegu** (usuwa rekordy powyżej progu błędu). Audytor **nie zbadał tego
osobno** — oparł się na pomiarze zbiorczym, który tego nie rozstrzyga.

**Jeśli pamięć może się opróżniać**, gałąź awaryjna nie jest martwa, lecz rzadka, a wtedy:

- §3 wymaga przeredagowania — K7 nie byłby kontrolą nieobserwującą swojego mechanizmu,
  lecz kontrolą o niskiej czułości;
- **klasyfikacja K7 jako Typ M wymaga ponownego rozważenia** — kontrola o niskiej czułości,
  dla której istnieje poprawna zawężona interpretacja, spełnia raczej kryteria Typu I;
- §2 i §4 pozostają w mocy niezależnie od wyniku.

### 7.1 Warunek SPEŁNIONY — weryfikacja niezależna wykonana

Wykonawca potwierdził znalezisko **niezależnie od audytora**, na próbie **szerszej niż
oryginalna**: pełny zestaw genomów, cztery środowiska, trzy seedy z zakresu pilota.

| Ustalenie | Wynik weryfikacji |
|---|---|
| Zakres wartości zwracanych przez funkcję haszującą bodziec | potwierdzony |
| Stałość progu dopasowania we wszystkich genomach ścieżki L1.1/L1.2 | potwierdzona |
| Częstość gałęzi awaryjnej: raz na przebieg, w ticku zerowym | potwierdzona, bez wyjątku |
| **Punkt najsłabszy — czy pamięć może się opróżnić w trakcie przebiegu** | **rozstrzygnięty**: rozmiar pamięci nie spadł poniżej jednego rekordu po ticku zerowym w żadnym przebiegu |

**Wniosek:** gałąź awaryjna jest **strukturalnie osiągalna, lecz empirycznie nigdy nie
wznawiana** po ticku zerowym. Warunek zapisany w §7 — potwierdzenie przez wykonawcę,
ze szczególną uwagą na możliwość opróżnienia pamięci — jest **spełniony**.

**Klasyfikacja K7 jako Typ M zostaje w mocy.** Scenariusz warunkowy z §7 („gałąź rzadka,
nie martwa" → rozważyć Typ I) **nie zachodzi**.

**Odnotowane uczciwie:** mechanizm opróżnienia pamięci **istnieje** — funkcja zaniku jest
wywoływana cyklicznie i usuwa rekordy powyżej progu błędu. Nie zaobserwowano jego zadziałania
w badanym zakresie. To jest **wynik empiryczny na skończonej próbie**, nie dowód niemożliwości.
Gdyby przy innej konfiguracji genomu albo dłuższym przebiegu pamięć się opróżniła, wniosek
wymaga ponownego rozważenia — i ten akapit jest miejscem, do którego wtedy należy wrócić.

---

## 8. Czego ten aneks nie zmienia

- **Primary Endpoint i W2** — `PE_red`, podłoga, procedura V-C, okna pomiarowe: bez zmian.
- **Reguła decyzyjna** — bez zmian; K7 nigdy do niej nie należał.
- **Pilot B4a-2** — nieunieważniony; zapisał wyłącznie `W_early_red`.
- **Status K3b** (ARCHITECTURE-LIMITED) i **warunku 1 K3a** — bez zmian.
- **Status Homeostatic Resilience w v0.11** — bez zmian.

---

## 9. Zamrożenie

Po zatwierdzeniu przez CTO **i po spełnieniu warunku z §7** aneks zostaje zamrożony jako
`publications/preregistration_PC_001_ANEKS_6_2026-08-03.{md,json}` (oba formaty, markdown
kanoniczny) i dodany do `CRITICAL_FILES_PC_001` — tym samym uzasadnieniem co Aneksy 4 i 5:
status kontroli i klasyfikacja zagrożenia nie mogą się zmienić bez złamania hasha.

**Kolejność wobec Specyfikacji Kanonicznej:** Specyfikacja może odnieść się do tego aneksu
dopiero, **gdy ten plik istnieje w repo** — jej walidator odrzuca odnośniki do nieistniejących
plików. Aktualizacja mapy §4 Specyfikacji (wersja v1.1) następuje więc **po** commicie Aneksu 6,
nie równolegle.

---

*Arytmetyka progu dopasowania zweryfikowana przez inspekcję kodu; częstość gałęzi przez
instrumentację wykonania; zawartość pamięci przez inspekcję stanu po przebiegu. Nie liczono
żadnej wielkości wchodzącej do reguły decyzyjnej. Wszystko na klonie `be43712`.*

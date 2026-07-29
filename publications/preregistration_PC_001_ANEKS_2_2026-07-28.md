# ANEKS 2 do PREREJESTRACJI PC-001

**Data:** 2026-07-28
**Status:** PROJEKT do zatwierdzenia i zamrożenia przez CTO
**Podstawa:** znalezisko audytora podczas audytu B2 · decyzja CTO (opcja B) · §12 PC-001
**Autor:** audytor niezależny

> **DOPUSZCZALNOŚĆ:** żadne dane PC-001 nie istnieją (baseline TBD, kod analizy nie powstał,
> analiza mocy nie wykonana). Aneks jest dopuszczalny dziś i **niedopuszczalny po pierwszym
> przebiegu** (D-006 pkt 3).

> **ZAKRES:** aneks **nie zmienia reguły decyzyjnej.** Dodaje jedno zagrożenie do tabeli
> interpretacyjnej i jeden **pomiar raportowany**. Reguła pozostaje 9-warunkowa (PC-001 §6 + Aneks 1).

---

## Powód aneksu

Podczas audytu B2 audytor zauważył w dowodzie działania, że na ticku 0 `prediction == input`
dokładnie. Inspekcja kodu wykazała, że **`clos_brain/runtime/prediction.py` ma gałąź awaryjną**:
gdy w pamięci nie ma rekordów pasujących do bieżącego bodźca, predykcja staje się
**średnią kroczącą ostatnich `prediction_depth` wejść**.

**Konsekwencja dla K6:** jeśli genom spędza w tej gałęzi znaczną część przebiegu,
`prediction` jest **filtrem wejścia**, nie modelem świata — a korelacja Spearmana z K6
będzie wysoka **trywialnie**. K6 formalnie przeszłoby, nie mierząc tego, co ma mierzyć.

To nie jest defekt kodu — to cecha architektury. Ale jest **luką interpretacyjną**, którą
trzeba raportować.

---

## Zmiana 6 — T7 w tabeli Threats to Interpretation (§3 PC-001)

| # | Mechanizm trywialny | Dlaczego daje spadek PE | Która kontrola go odróżnia |
|---|---|---|---|
| **T7** | **Predykcja z gałęzi awaryjnej (średnia krocząca wejścia)** | `predict()` przy braku pasujących rekordów zwraca średnią z ostatnich `prediction_depth` wejść → predykcja silnie skorelowana z inputem, **bez modelu generatywnego** | **K4** (separacja — średnia krocząca zredukuje PE także w czystym szumie), **K5** (ablacja — spadek powinien zniknąć), **K7** (pomiar raportowany) |

---

## Zmiana 7 — K7: pomiar raportowany (NIE warunek decyzyjny)

**Charakter:** pomiar diagnostyczny, **poza regułą decyzyjną §6.** Nie może spowodować ani wsparcia,
ani odrzucenia hipotezy. Służy wyłącznie interpretacji K6.

### Procedura

Dla każdego przebiegu **oszacować** odsetek ticków, w których `predict()` użył gałęzi awaryjnej,
przez porównanie zapisanej `prediction(t)` ze średnią z ostatnich `prediction_depth` zapisanych
wartości `input`.

### Ograniczenia metody — istotne, zapisane przed wykonaniem

Wcześniejsza ocena audytora („policzalny post-hoc, zero kosztu") była **zbyt pewna.**
Metoda ma trzy realne ograniczenia:

1. **Wymaga `prediction_depth` per genom** — parametru, którego `Snapshot` **nie niesie**.
   Musi być dołączony z danych genomowych (`clos_curriculum/laboratory/population.py`,
   `genome/presets.py`). Jeśli dołączenie okaże się niemożliwe dla części genomów, K7 jest dla
   nich **nieobliczalny** i musi być tak raportowany, nie pomijany.
2. **Wymaga tolerancji zmiennoprzecinkowej** — dopasowanie nie jest dokładną równością.
   Przyjęta tolerancja: `1e-9` względna. Wartość arbitralna, zapisana z góry.
3. **Jest heurystyką, nie pewnością** — gałąź pamięciowa może przypadkowo wyprodukować wartość
   równą średniej kroczącej. Prawdopodobieństwo małe, ale **niezerowe**. K7 daje **oszacowanie
   dolne** odsetka gałęzi awaryjnej, nie liczbę dokładną.

**Konsekwencja:** K7 jest raportowany jako **„szacowany odsetek (metoda heurystyczna, oszacowanie
dolne)"**, nigdy jako wartość dokładna. To rozróżnienie musi zostać w raporcie i publikacji.

### Raportowanie

W raporcie końcowym, w **osobnej sekcji** (nie łącznie z K6):
- **mediana** szacowanego odsetka ticków w gałęzi awaryjnej — przez genomy i przez środowiska,
- **rozkład**: min, Q1, Q3, max,
- **liczba genomów, dla których K7 był nieobliczalny** (jeśli dotyczy).

### Interpretacja (progi z decyzji CTO)

| Szacowany odsetek | Interpretacja K6 |
|---|---|
| **< 20%** | K6 wiarygodny — predykcja pochodzi głównie z modelu pamięciowego |
| **20–50%** | strefa niejednoznaczna — wymaga jawnego omówienia w interpretacji |
| **> 50%** | **K6 potencjalnie mylący** — predykcja może być w znacznej części średnią kroczącą. **Musi być jawnie zaznaczone w interpretacji, także gdy K6 formalnie przechodzi** |

**Progi 20% / 50% są konwencją przyjętą z góry**, nie wartościami z literatury — analogicznie do
progu 20% w Primary Endpoint (Aneks 1, Zmiana 4). Ich wartością jest niezmienność.

### Dlaczego K7 nie jest warunkiem decyzyjnym

1. **K4 i K5 częściowo pokrywają T7** — jeśli spadek PE wynika ze średniej kroczącej, to
   w `pure_noise_world` redukcja będzie podobna (separacja z K4 nie wyjdzie), a ablacja do stałej
   0.5 powinna spadek usunąć (K5).
2. **Dodanie dziesiątego warunku byłoby zawężeniem bez proporcjonalnego zysku** — ryzykowałoby
   odrzucenie hipotezy z powodu cechy architektury, nie błędu metodologicznego.
3. **Raportowanie daje transparentność bez zaostrzania reguły** — czytelnik dostaje liczbę
   i może sam ocenić wiarygodność K6.

---

## Reguła decyzyjna — BEZ ZMIAN

Reguła pozostaje **9-warunkowa** (PC-001 §6 + Aneks 1). **K7 nie wchodzi do niej.**
Kategoria INCONCLUSIVE (D-007 pkt 2) obowiązuje bez zmian.

---

## Uzupełnienie wymagań technicznych

| # | Wymaganie | Podstawa |
|---|---|---|
| 9 | Kod analizy (B3) musi obliczać K7 z zapisanych trajektorii `prediction`/`input` **oraz** dołączonego `prediction_depth` per genom | Aneks 2, Zmiana 7 |
| 10 | Jeśli `prediction_depth` niedostępny dla części genomów — K7 raportowany jako **nieobliczalny** dla nich, nie pomijany milczeniem | Aneks 2, ograniczenie 1 |

---

## Zamknięcie fazy projektowania protokołu

Po zamrożeniu tego aneksu **faza projektowania PC-001 jest zamknięta.** Dalsze etapy to wyłącznie
implementacja i wykonanie:

| Etap | Zawartość |
|---|---|
| **B3** | kod analizy (testy dla 9 warunków + K7), walidowany przeciw `scipy` (zgodność do 1e-6) |
| **B4** | analiza mocy → `publications/power_analysis_PC_001.json` |
| **B5** | `PC_001_BASELINE` policzony jako **ostatni** krok, gdy cały pipeline istnieje |
| **B6** | bramka audytora → start eksperymentu |

**Żadne dalsze zmiany metodologiczne nie są dopuszczalne** — wyłącznie przez nową prerejestrację
(PC-002), zgodnie z D-007 pkt 3.

---

## Zamrożenie

Po zatwierdzeniu aneks zostaje zamrożony jako
`publications/preregistration_PC_001_ANEKS_2_2026-07-28.{md,json}` (oba formaty; markdown
kanoniczny) i **dodany do `CRITICAL_FILES_PC_001`** — tak jak PC-001 i Aneks 1.

---

*Znalezisko zweryfikowane w kodzie na klonie `df436b2`: `clos_brain/runtime/prediction.py`,
gałąź `else` przy braku pasujących rekordów — „Użyj średniej z ostatnich wejść jako prostej
heurystyki". Ograniczenia metody K7 ustalone przez inspekcję `Snapshot` (brak `prediction_depth`).*

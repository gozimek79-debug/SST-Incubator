# ANALIZA WARIANCJI PILOTA B4a-2 — odtworzenie przesłanki dla Pilota Final

**Od:** audytor niezależny · **Dla:** CTO
**Data:** 2026-08-03 · świeży klon `v0.7.2-scientific-integrity` @ `0e57905`
**Przedmiot (G-005):** METODOLOGIA
**Podstawa:** D-032, D-033 pkt 3 (odtworzenie analizy na istniejących danych pilota) ·
znalezisko §6.4 Specyfikacji Kanonicznej

**Status:** PROJEKT do decyzji CTO. **Zawiera znalezisko sprzeczne z dokumentem przekazania
kontekstu** — patrz §3.

---

## 0. Dopuszczalność — sprawdzona przed wykonaniem

Analiza operuje **wyłącznie na `W_early_red`** — jedynej wielkości zapisanej przez pilota.
`NOTATKA_B4` §2 dopuszcza to wprost: pilot dostarcza **parametrów uciążliwych** (rozkład,
wariancja), nigdy wielkości efektu. Rozkład `W_early_red` nie niesie informacji o tym,
**czy** błąd predykcji spada.

**Skażenie: brak.** Nie liczono `W_late`, trajektorii, nachylenia ani redukcji. Analiza czyta
zamrożony artefakt pilota; nic nie uruchamiano.

---

## 1. Wariant B potwierdzony — dane surowe istnieją

`reports/pilot/pilot_W_early_red_noise_world.json` zawiera **pełne dane per przebieg**:
sto piętnaście rekordów, każdy z identyfikatorem genomu, seedem, wartością `W_early_red`
i statusem. Wszystkie VALID; zero FLOOR_LIMITED, zero INSUFFICIENT_DATA.

> **Odtworzenie analizy jest wykonalne bez uruchamiania czegokolwiek.** D-034 (jawny dokument
> decyzji przy braku danych) **nie ma zastosowania**.

---

## 2. Rozkład składowych wariancji

Model losowy jednoczynnikowy, liczony osobno względem genomu i względem seeda.

| Czynnik grupujący | Grup | Na grupę | Średni kwadrat wewnątrz | Średni kwadrat między | Stosunek |
|---|---|---|---|---|---|
| **genom** | 23 | 5 | `2.375e-04` | `2.510e-05` | **0.11** |
| **seed** | 5 | 23 | `3.610e-05` | `4.607e-03` | **127.6** |

Rozrzut średnich: **między seedami `0.0356`**, między genomami `0.0077` — blisko pięciokrotnie
większy dla seeda.

### Wniosek

> **Składowa wariancji między genomami jest nieodróżnialna od zera.** Średni kwadrat między
> genomami jest **niższy** niż wewnątrz nich, więc estymator składowej wychodzi ujemny
> i zostaje obcięty do zera.
>
> **Zmienność `W_early_red` pochodzi niemal w całości z seeda, nie z genomu.**

To jest **ta sama obserwacja, którą zgłoszono dla pilota B4a** — „rozkład `W_early` grupował się
w klastry odpowiadające seedom, nie w wartości genomowe; seed dominował nad genomem".
Zjawisko **utrzymało się po przejściu na W2**, mimo zmiany mierzonej wielkości i środowiska.

---

## 3. Sprzeczność z dokumentem przekazania kontekstu — do rozstrzygnięcia

Dokument przekazania opisuje plan B4b tak: *„Wariancja **dwupoziomowa**
(within/between = 47×) — pooling zaniżyłby szum i zawyżył moc."*

**Żadna część tego zdania nie odtwarza się z danych pilota.**

| Twierdzenie | Co pokazują dane |
|---|---|
| stosunek `47×` | nie odtwarza się w żadnym z liczonych ujęć |
| składowa **between** istnieje | **nieodróżnialna od zera** dla genomu |
| pooling **zaniżyłby** szum | jeśli składowa między genomami wynosi zero, pooling nie zaniża niczego — genomy są w tej wielkości wymienne |

**Nie twierdzę, że tamto zdanie było błędne.** Twierdzę, że **nie ma w repozytorium artefaktu,
z którego by wynikało**, a odtworzenie z zachowanych danych daje inny obraz. Możliwe, że
liczba `47×` pochodzi z ujęcia, którego nie odgadłem — i wtedy właściwą reakcją jest wskazanie
tego ujęcia, nie dopasowywanie mojej analizy do oczekiwanej liczby.

> **Świadomie nie szukałem sposobu liczenia, który dałby `47×`.** Godzinę wcześniej w tej samej
> sesji popełniłem dokładnie ten błąd przy liczbie wystąpień progu — dostroiłem wzorzec do
> oczekiwanego wyniku, a wykonawca to wychwycił. Powtórzenie go tutaj byłoby gorsze,
> bo dotyczyłoby przesłanki dla projektu eksperymentu.

---

## 4. Precyzja oszacowania wariancji — podstawa doboru liczby seedów

Wielkości standardowe, niezależne od danych, wynikające wyłącznie z liczby obserwacji na grupę.

| Seedów na genom | Szerokość 95% przedziału ufności dla odchylenia | Względny błąd standardowy wariancji |
|---|---|---|
| **5** (pilot B4a-2) | **228%** wartości oszacowania | **71%** |
| **15** (proponowany Pilot Final) | **84%** wartości oszacowania | **38%** |

Przejście z pięciu na piętnaście seedów **zawęża przedział blisko trzykrotnie** i **redukuje
względny błąd oszacowania wariancji o niemal połowę**.

**Uwaga o wartościach z dokumentu przekazania.** Podano tam *„CI 60% > próg 50%"*. Moje liczby
to `228%` i `84%` — **nie odtwarzam ani wartości, ani progu**. Nie próbowałem dobrać miary tak,
żeby wyszło sześćdziesiąt; podaję wielkości standardowe i nazywam je wprost.

**Kierunek wniosku pozostaje ten sam:** przy pięciu seedach oszacowanie wariancji jest zbyt
nieprecyzyjne, by oprzeć na nim symulację mocy; przy piętnastu jest istotnie lepsze.
**Konkretna liczba piętnaście nie wynika z tych obliczeń** — wynika z nich, że pięć to za mało.

---

## 5. Co z tego wynika dla B4b — zgłaszam, nie rozstrzygam

Jeśli składowa wariancji między genomami jest zerowa, to **projekt symulacji mocy oparty na
wariancji dwupoziomowej opisuje strukturę, której w danych nie widać.** Możliwe reakcje:

| Wariant | Konsekwencja |
|---|---|
| utrzymać model dwupoziomowy | konserwatywny; przy zerowej składowej sprowadza się do jednopoziomowego, więc nie szkodzi — ale uzasadnienie „pooling zaniżyłby szum" trzeba wycofać |
| przejść na jednopoziomowy | zgodny z danymi; wymaga zapisania, że genomy są w `W_early_red` wymienne |
| **zbadać, czy seed jest właściwą jednostką stratyfikacji** | zmienność pochodzi z seeda — to może mieć konsekwencje dla projektu symulacji szersze niż sam dobór `n` |

**Trzeci wiersz jest tym, który uważam za istotny**, i którego nie rozstrzygam: jeśli seed
wyjaśnia niemal całą zmienność `W_early_red`, to pytanie „ile seedów na genom" może być gorzej
postawione niż „ile seedów łącznie".

---

## 6. Do decyzji CTO

1. Czy wskazujesz ujęcie, z którego pochodzi `47×` i wartości `60%`/`50%` — czy przyjmujemy,
   że nie mają zachowanego źródła?
2. Czy ta analiza, po ewentualnych poprawkach, wchodzi do repozytorium jako artefakt zamykający
   §6.4 — i czy do rejestru plików krytycznych?
3. Czy liczba seedów Pilota Final zostaje piętnaście — z uzasadnieniem opartym na precyzji
   z §4, a **nie** na nieodtwarzalnym `47×`?
4. Czy obserwacja o zerowej składowej między genomami (§2, §5) wymaga rewizji projektu B4b
   **przed** Pilotem Final, czy jest zapisem do uwzględnienia przy B4b?

**Rekomendacja audytora do pkt 3:** tak, piętnaście — ale z jawnym zapisem, że z obliczeń
wynika „pięć to za mało", a nie „dokładnie piętnaście". Liczba piętnaście jest wtedy
**konwencją przyjętą z góry**, tak samo jak próg Warunku B — i jej wartością jest niezmienność,
nie optymalność. To jest uczciwsze niż dorabianie do niej wyprowadzenia.

---

*Wszystkie liczby z uruchomionych obliczeń na zamrożonym artefakcie pilota, klon `0e57905`.
Nie uruchamiano żadnego przebiegu. Nie liczono żadnej wielkości niosącej informację o efekcie.*

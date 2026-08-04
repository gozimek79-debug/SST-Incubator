# BEZPIECZEŃSTWO METODOLOGICZNE POMIARU — `recovery_i` i korelacja `prediction ↔ input`

**Od:** audytor niezależny · **Dla:** CTO
**Data:** 2026-07-28 · **Status:** PROJEKT (D-022 pkt 5)
**Zadanie:** wykazać, że pomiar tych wielkości w pilocie **nie ujawnia informacji o końcowym
efekcie eksperymentu** — albo wykazać, że ujawnia, i wskazać konsekwencje.

> **Wniosek z góry:** dla `recovery_i` **nie da się** tego wykazać w formie wymaganej przez K3b.
> Dla Spearmana **da się**, pod jednym warunkiem. Uzasadnienie poniżej.

---

## 1. Kryterium bezpieczeństwa

Wielkość jest **bezpieczna** dla pilota, jeśli spełnia oba warunki:

1. **Jest parametrem uciążliwym** — niesie informację o *zmienności*, nie o *kierunku efektu*.
2. **Jej znajomość nie pozwala przewidzieć wyniku żadnego z 9 warunków reguły decyzyjnej.**

Wielkość niespełniająca któregokolwiek jest **częściowym wynikiem eksperymentu** i jej pomiar
w pilocie skaziłby konfirmację — niezależnie od deklaracji, że „nie będziemy patrzeć".

---

## 2. `recovery_i` — NIEBEZPIECZNA w formie wymaganej przez K3b

### 2.1 Definicja z Aneksu 1

> `recovery_i` = liczba ticków od wstrząsu `i` do momentu, w którym PE wraca poniżej średniej
> z okna `[shock_i − 20, shock_i − 1]`
>
> **K3b-1:** Kendall tau na ciągu `recovery_i` — wymaga **wszystkich** wstrząsów
> **K3b-2:** mediana `recovery` w drugiej połowie wstrząsów ≥20% krótsza niż w pierwszej

### 2.2 Dlaczego pomiar w pilocie skaża konfirmację

**Ciąg `recovery_i` JEST wynikiem K3b.** Nie jest parametrem opisującym zmienność — jest
dokładnie tą wielkością, na której liczony jest warunek 6 reguły decyzyjnej.

Zmierzenie go w pilocie oznacza **zobaczenie wyniku K3b przed eksperymentem**. Nawet gdyby nikt
nie policzył tau jawnie, sam ciąg (`recovery_1, recovery_2, …, recovery_7`) pozwala odczytać
kierunek okiem.

**To jest różnica jakościowa wobec `W_early_red`:** tam mierzyliśmy **początek** przebiegu, a efekt
dotyczy **zmiany między początkiem a końcem** — więc informacja o efekcie była konstrukcyjnie
niedostępna. Tutaj **całość wielkości jest wynikiem.**

### 2.3 Czy da się zmierzyć „bezpieczną część"?

Rozważyłem propozycję z poprzedniego zlecenia: mierzyć **tylko `recovery_1`** (pierwszy wstrząs).

| | |
|---|---|
| **Bezpieczeństwo** | ✅ pojedyncza wartość nie ujawnia trendu — analogicznie do `W_early` |
| **Przydatność do analizy mocy** | ❌ **niewystarczająca** |

**Powód odrzucenia:** moc testu Kendalla tau na ciągu 7 punktów zależy od **wariancji ciągu**
i **siły trendu**, a nie od wariancji pojedynczej wartości. `recovery_1` nie pozwala oszacować
ani jednego, ani drugiego. Symulacja Monte Carlo oparta na `var(recovery_1)` dałaby moc
**niezwiązaną z rzeczywistą mocą K3b** — czyli gorzej niż brak oszacowania, bo stwarzałaby
pozór wykonanej analizy.

### 2.4 Konsekwencja: K3b nie może mieć analizy mocy opartej na pilocie

**To nie jest usterka do obejścia — to strukturalna właściwość K3b.**

Dopuszczalne drogi (kolejność z **D-008 pkt 4**, wiążąca):

1. **Analiza mocy K3b z założeń teoretycznych, nie z pilota.** Moc Kendalla tau dla `n = 7`
   punktów jest **policzalna analitycznie** dla zadanej siły trendu — rozkład tau przy `H₀` jest
   znany i dyskretny. Nie wymaga danych. **← droga rekomendowana**
2. Jeśli moc przy 7 punktach okaże się niedostateczna: **przeprojektowanie** (krótszy `interval`
   → więcej wstrząsów na przebieg). Wymaga aneksu **przed** uruchomieniem.
3. Ostateczność: przeniesienie K3b do PC-002.

**Droga 1 nie wymaga żadnych danych** — a więc nie wymaga rozszerzania pilota. To jest odpowiedź
zgodna z D-022: problem był implementacyjno-analityczny, nie pilotażowy.

---

## 3. Korelacja `prediction ↔ input` (K6) — BEZPIECZNA pod jednym warunkiem

### 3.1 Analiza

K6 wymaga korelacji Spearmana po **całym mierzalnym oknie**. Pomiar tej wielkości w pilocie
byłby zobaczeniem wyniku warunku 9.

**Ale pomiar w oknie WCZESNYM `[0,60)` jest bezpieczny**, i to z powodu strukturalnego:

| | Okno wczesne `[0,60)` | Całe okno `[0,300)` |
|---|---|---|
| Co mierzy | sprzężenie predykcji z wejściem **na starcie** | sprzężenie **przez cały przebieg** = wynik K6 |
| Czy niesie efekt | ❌ nie — to stan początkowy | ✅ tak — to wynik |

Analogia jest ścisła: **`Spearman[0,60)` ma się do K6 tak, jak `W_early_red` do Primary Endpoint.**
Oba są pomiarem **stanu początkowego**, oba są parametrami uciążliwymi.

### 3.2 Warunek bezpieczeństwa

> **Wolno zmierzyć `Spearman(prediction, input)` wyłącznie w oknie `[0,60)`.**
> Zapis obejmuje wyłącznie tę jedną wartość na przebieg. Zabroniony jest zapis korelacji
> w oknie późnym, w całym oknie, ani różnicy między oknami.

Ta sama gwarancja mechaniczna co dla `W_early_red`: **czego nie ma w pliku, tego nie da się
podejrzeć.**

### 3.3 Czy wystarcza do analizy mocy K6?

**Tak.** Moc testu Spearmana zależy od **liczby punktów** (300 ticków — znana z góry) i od
**wariancji korelacji między przebiegami** — a tę można oszacować z `Spearman[0,60)`, bo jest to
ta sama wielkość mierzona na krótszym oknie. Oszacowanie jest **konserwatywne** (krótsze okno →
większa wariancja), co jest bezpieczne: da `n` z zapasem, nie za małe.

---

## 4. Podsumowanie i konsekwencje dla Etapu I / Etapu II

| Wielkość | Bezpieczna w pilocie? | Sposób uzyskania mocy |
|---|---|---|
| `W_early_red` | ✅ tak (już zmierzona) | pilot, seedy 1–15 |
| `Spearman[0,60)` (K6) | ✅ tak, **tylko okno wczesne** | pilot, ta sama seria |
| **`recovery_i` (K3b)** | ❌ **NIE — jest wynikiem** | **analitycznie, bez danych** (§2.4 droga 1) |
| Warunek A (trend `β`) | — (brak kodu, nie brak danych) | Etap I: implementacja + moc z wariancji `W_early_red` |
| K4 (separacja) | ✅ tak — `W_early_red` w `pure_noise_world` | pilot, po zamrożeniu podłogi tego środowiska |

### Wpływ na zakres Etapu I (D-022 pkt 4)

| Element | Status |
|---|---|
| test istotności trendu regresji | **implementacja** (brak kodu) |
| `floor` dla `pure_noise_world` | **wyznaczenie numeryczne + zamrożenie** (analityczne zawyżone o ~86%) |
| `floor` dla `recurring_shock_world` | **niepotrzebne**, jeśli K3b idzie drogą analityczną — patrz §2.4 |
| moc K3b | **wyprowadzenie analityczne** (rozkład tau dla `n=7`), nie implementacja pomiaru |
| `Spearman[0,60)` | **implementacja pomiaru** w runnerze pilota, z gwarancją okna |

**Etap I nie wymaga `recovery_i` ani podłogi dla `recurring_shock_world`** — to redukuje zakres
wobec mojej poprzedniej propozycji.

### Zakres Pilota Final (Etap II)

Jeden przebieg, seedy **1–15**, dwa środowiska (`noise_world`, `pure_noise_world`),
mierzone: `W_early_red` + `Spearman[0,60)`. Nic więcej.

---

## 5. Rekomendacja

**Nie dodawać `recovery_i` do pilota — ani teraz, ani później.** Nie jest to kwestia projektu
pomiaru, tylko właściwości samej wielkości: **jest wynikiem, nie parametrem.**

Moc K3b wyprowadzić **analitycznie z rozkładu tau dla `n = 7`** — co jest wykonalne bez danych
i rozstrzyga, czy K3b w ogóle jest wykonalne przy obecnym `interval = 40`.

**To jest przewidywalnie wąskie gardło.** Jeśli analiza pokaże niedostateczną moc, uruchamia się
D-008 pkt 4: przeprojektowanie (więcej wstrząsów), nie osłabienie kryterium.

---

*Definicje odczytane z `preregistration_PC_001_ANEKS_1_2026-07-28.md` (K3b, K6)
oraz `clos_world/scenarios.py:54` (`recurring_shock_world`, `interval = 40`).*

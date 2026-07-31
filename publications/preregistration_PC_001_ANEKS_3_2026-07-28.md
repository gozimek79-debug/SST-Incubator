# ANEKS 3 do PREREJESTRACJI PC-001 — zgodność hipotezy z operacjonalizacją

**Od:** audytor niezależny
**Dla:** CTO
**Data:** 2026-07-28
**Status:** PROJEKT do zatwierdzenia · **Hard Halt pozostaje w mocy**
**Podstawa:** DECYZJA CTO D-010 · wynik pilota B4a

> **ZADANIE (D-010 pkt 4):** nie wybór okna pomiarowego, lecz **analiza zgodności między hipotezą
> badawczą a operacyjną definicją Primary Endpoint.** Aneks przedstawia warianty i uzasadnia wybór.

---

## 1. Korekta językowa poprzedniego zgłoszenia

Audytor stwierdził wcześniej, że *„Primary Endpoint jest niemożliwy dla dowolnego genomu"*.
**To było przecenienie siły dowodu** — wykazano strukturę środowiska, nie własność wszystkich
możliwych predyktorów. Poniżej argument formalny; dopóki nie zostanie przyjęty, obowiązuje
sformułowanie ostrożniejsze.

### 1.1 Argument formalny dla `shock_world`

Środowisko (`clos_world/scenarios.py:30`):

```
tick <  shock_tick :  0.2                                    (stała)
tick == shock_tick :  shock_magnitude                        (skok)
tick >  shock_tick :  shock_magnitude·0.8 + N(0, 0.02)       (nowy poziom + szum)
```

**Faza przedwstrząsowa:** świat jest stały. Dla dowolnego predyktora zwracającego wartość
w pobliżu 0.2 błąd dąży do zera. Gałąź awaryjna `predict()` (średnia krocząca wejść) daje
dokładnie 0.2. **`E[PE_pre] → 0` niezależnie od genomu.**

**Faza powstrząsowa:** najlepszy możliwy predyktor zwraca `shock_magnitude·0.8` (średnią rozkładu).
Błąd rezydualny to `E|N(0, 0.02)| = σ·√(2/π) ≈ 0.141·0.798 ≈ **0.113**`.
**Żaden predyktor nie zejdzie poniżej tej wartości** — to nieredukowalna podłoga szumu.

**Wniosek:** `W_late ≥ 0.113` (podłoga), `W_early → 0` (gdy okno w całości przedwstrząsowe).
Redukcja `(W_early − W_late)/W_early` jest wtedy **ujemna albo nieokreślona** — nigdy `≥ 20%`.

Dla `shock_tick < 60` okno `W_early` jest mieszanką faz, ale nierówność `W_early < W_late`
utrzymuje się, bo część przedwstrząsowa ciągnie `W_early` w dół, a `W_late` jest w całości
powstrząsowe.

**Status twierdzenia:** dowiedzione dla klasy predyktorów zwracających wartość ograniczoną
zakresem sygnału (a taka jest cała rodzina implementowana w `prediction.py`). Formalnie
**nie jest to dowód dla dowolnego wyobrażalnego predyktora** — ale jest dowodem dla systemu,
który faktycznie badamy.

---

## 2. Sedno: to jest problem trafności konstrukcyjnej (construct validity)

**Hipoteza badawcza PC-001:** *system uczy się przewidywać strukturę swojego świata.*

**Co mierzy obecna operacjonalizacja w `shock_world`:** *jak bardzo świat stał się trudniejszy
w trakcie przebiegu.*

To nie są te same wielkości. Redukcja PE mierzy uczenie **tylko wtedy, gdy trudność świata
jest stała.** W `shock_world` trudność **rośnie z definicji** — więc pomiar odzwierciedla
zmianę środowiska, nie zmianę systemu.

To jest ta sama klasa błędu, którą projekt naprawiał w v0.11: `adaptation_tick` nie mierzył
adaptacji, tylko czas ustabilizowania entropii. **Nazwa i mechanizm się rozjechały.**

---

## 3. Odpowiedź na pytanie CTO: czy problem to `shock_world`, czy jeden endpoint dla różnych dynamik?

**To drugie — i to jest właściwa diagnoza.**

Redukcja PE ma sens **wyłącznie względem tego, co w danym świecie jest do nauczenia.**
Każde środowisko ma dwie składowe błędu:

| Składowa | Czym jest | Czy PC może ją zmniejszyć |
|---|---|---|
| **Redukowalna** | struktura świata (sinus, poziom, okresowość) | **tak** — o to chodzi w PC |
| **Nieredukowalna** | szum losowy | **nie** — podłoga fizyczna |

**Kluczowa obserwacja:** wszystkie środowiska CLOS są **czystymi funkcjami `(tick, seed) → float`
o znanym rozkładzie szumu.** Podłogę nieredukowalną można więc **policzyć analitycznie**, nie oszacować.

| Środowisko | Struktura (redukowalna) | Podłoga `E\|szum\|` |
|---|---|---|
| `stable_world` | czysty sinus | **0** (brak szumu) |
| `noise_world` | sinus + N(0, 0.05) | ≈ 0.178 |
| `shock_world` | stała → skok → poziom | 0 (przed), ≈ 0.113 (po) — **niestacjonarna** |
| `pure_noise_world` | **brak** | ≈ 0.252 |

> **KOREKTA 2026-07-28 (D-017/D-018):** wartości w tabeli powyżej są **oszacowaniem
> analitycznym** przy założeniu **nieobciętego** rozkładu normalnego. Założenie jest
> **fałszywe** — generator obcina do `[0,1]` (`generators.py:20`). Wyznaczenie
> numeryczne z rzeczywistego generatora dało dla `noise_world` `floor_env = 0.09589`,
> czyli ~53% wartości analitycznej. Tabela zachowana jako ślad rozumowania, **NIE**
> jako źródło wartości. Obowiązują wartości z `clos_world/floor_model.py`
> (procedura V-C, `publications/specyfikacja_W2_2026-07-28.md`).

**Wniosek:** jeden uniwersalny próg „redukcja ≥ 20% surowego PE" jest **niespójny między
środowiskami**, bo 20% znaczy co innego, gdy podłoga wynosi 0, a co innego, gdy 0.25.
Problem nie jest wyłącznie w `shock_world` — ujawnił się tam najostrzej, bo podłoga **zmienia się
w trakcie przebiegu.**

---

## 4. Warianty definicji Primary Endpoint

### W1 — status quo: redukcja surowego PE ≥ 20%

- **Mierzy:** zmianę błędu bezwzględnego.
- **Wada zasadnicza:** miesza uczenie ze zmianą trudności świata; niespójne między środowiskami.
- **W `shock_world`:** systematycznie nieosiągalne (§1.1).
- **Ocena:** ❌ do wycofania.

### W2 — redukcja składowej REDUKOWALNEJ (normalizacja podłogą)

```
PE_reducible(t) = max(0, PE(t) − floor_env)
redukcja = (W_early_reducible − W_late_reducible) / W_early_reducible
```

- **Mierzy:** ile z tego, co **dało się** nauczyć, zostało nauczone.
- **Zaleta:** **porównywalne między środowiskami** — 20% znaczy to samo wszędzie.
- **Zaleta:** wprost odpowiada hipotezie („uczy się struktury"), bo szum jest z definicji wyłączony.
- **Warunek:** `floor_env` liczona **analitycznie** z definicji scenariusza, prerejestrowana
  przed przebiegiem, **nigdy szacowana z danych** (inaczej wraca moc retrospektywna).
- **Ryzyko:** przy `floor_env` bliskiej `PE` mianownik mały → niestabilność. Wymaga progu
  minimalnej wielkości mianownika, ustalonego z góry.
- **Ocena:** ✅ **rekomendowany**.

### W3 — osobne endpointy per klasa środowiska (propozycja CTO)

- **Mierzy:** różne aspekty przewidywania w środowiskach stacjonarnych vs niestacjonarnych.
- **Zaleta:** uczciwie przyznaje, że `shock_world` bada co innego niż `noise_world`.
- **Wada:** mnoży kryteria decyzyjne; utrudnia korektę FDR (różne endpointy = różne rodziny testów);
  zwiększa ryzyko, że wynik zostanie „poskładany" z korzystnych fragmentów.
- **Ocena:** ◐ **sensowny jako uzupełnienie W2, nie zamiast**. W2 daje jedną, porównywalną skalę;
  W3 dokłada interpretację per środowisko.

### W4 — okna względem `shock_tick`

- **Odrzucony przez CTO (D-010) i przez audytora:** przesuwa pytanie z „uczenia struktury"
  na „adaptację po zmianie reguł", co **pokrywa się z K3** — Primary i kontrola mierzyłyby to samo.
- **Ocena:** ❌.

---

## 5. Konsekwencja dla wyboru środowiska Primary

Przy W2 problem doboru środowiska **znika w dużej mierze**, bo miara jest porównywalna.
Ale pozostaje jedno rozstrzygnięcie:

**`shock_world` jest niestacjonarne — podłoga zmienia się w trakcie przebiegu** (0 przed
wstrząsem, 0.113 po). W2 wymaga wtedy podłogi **zależnej od ticka**, co jest policzalne
(znamy `shock_tick` z seeda), ale komplikuje interpretację: „ile nauczył" miesza dwa reżimy.

**Rekomendacja:** Primary w środowisku **stacjonarnym** (`noise_world`), gdzie podłoga jest stała
i pytanie „ile z redukowalnego błędu zredukował" ma jednoznaczną odpowiedź.
`shock_world` pozostaje **środowiskiem kontrolnym dla K3** (adaptacja po zmianie reguł) — do czego
jest dobrze zaprojektowane.

**Warunek techniczny do sprawdzenia przed decyzją:** czy lekcja L1.2 (300 ticków, `PERCEIVE`
nigdy pomijany) może działać w `noise_world` bez utraty sensu. L1.2 to „shock recovery" —
uruchomienie jej bez wstrząsu może być semantycznie puste. Jeśli tak, potrzebna **nowa
konfiguracja lekcji**: długi przebieg w środowisku stacjonarnym.

---

## 6. Czego ten aneks NIE rozstrzyga

- **Nie wybiera okien pomiarowych** — to wynika z wyboru wariantu, nie odwrotnie (D-010 pkt 5).
- **Nie zmienia progu 20%** — pozostaje konwencją, tylko stosowaną do innej wielkości.
- **Nie modyfikuje rozkładu `shock_tick`** ani stratyfikacji (zakaz z D-010 pkt 5).
- **Nie unieważnia K1–K7** — kontrole pozostają, ale ich operacjonalizacja wymaga przeliczenia
  pod W2 (osobne zadanie po zatwierdzeniu wariantu).

---

## 7. Pytania do rozstrzygnięcia przez CTO

1. **Czy przyjmujemy W2** (redukcja składowej redukowalnej, normalizacja analityczną podłogą)
   jako nową definicję Primary Endpoint?
2. **Czy W3** (osobne interpretacje per klasa środowiska) wchodzi jako **uzupełnienie** W2,
   czy odkładamy do PC-002?
3. **Czy Primary przenosimy do środowiska stacjonarnego** (`noise_world` / nowa konfiguracja
   długiego przebiegu), zostawiając `shock_world` wyłącznie dla K3?
4. **Czy `floor_env` liczona analitycznie** z definicji scenariusza jest akceptowalna jako
   wielkość prerejestrowana — mimo że wymaga dopisania kodu, który wejdzie do baseline'u?

---

## 8. Status procesu

**Hard Halt pozostaje w mocy.** Kod pilota, testy gwarancyjne i wynik B4a zostają w repo jako
**udokumentowany negatywny wynik walidacyjny** (D-010 pkt 2) — jest to część historii
metodologicznej, nie porażka.

Po zatwierdzeniu wariantu: aneks operacyjny z nowymi oknami → ponowny pilot → B4b.

---

*Podłogi nieredukowalne policzone z definicji scenariuszy: `E|N(0,σ²)| = σ√(2/π)`.
`noise_world` σ²=0.05 → 0.178; `shock_world` (po wstrząsie) σ²=0.02 → 0.113;
`pure_noise_world` σ²=0.1 → 0.252. Wartości do niezależnej weryfikacji przed zamrożeniem.*

*KOREKTA 2026-07-28 (D-017/D-018): powyższe są oszacowaniem analitycznym dla
nieobciętego rozkładu normalnego — założenie fałszywe wobec obcięcia do `[0,1]`
w generatorze. Zweryfikowane numerycznie (procedura V-C): `noise_world`
`floor_env = 0.09589` (~53% wartości analitycznej 0.178). Obowiązują wyłącznie
wartości numeryczne z `clos_world/floor_model.py`.*

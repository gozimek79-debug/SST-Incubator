# Raport końcowy — Sprint v0.8.5 (CLOS Studio: Panel Badacza)

Branch: `v0.7.2-scientific-integrity`. Zakres: `10470e8..HEAD` (5 commitów,
w tym jeden auto-commit CI). Status projektu: nadal **Research Grade
Infrastructure** — ten sprint dodaje warstwę prezentacji (Studio), nie
zmienia zawartości naukowej z v0.8.4.

---

## 1. Lista commitów sprintu

| Commit | Priorytet | Opis (jedno zdanie) |
|---|---|---|
| `bb31eec` | P1 | Szkielet Panelu Badacza (`clos_studio/panel/`: `index.html`+`panel.css`+`panel.js`) — 7 sekcji, nawigacja z RWD, a11y, stany load/empty/error, zero danych. |
| `31e4539` | P2 | Loader danych na żywo (`fetch()` z repo) + render wszystkich 7 sekcji wyłącznie z pobranego JSON; licznik kompetencji liczony z danych, nie wpisany. |
| `96cdbc3` | P3 | `reports/status.json` generowany w CI po zielonym pytest+walidatorach; `scripts/validate_panel.py` (CI gate przeciw wklejonym metrykom) z testem negatywnym. |
| `03c32d3` | (auto, CI) | `ci: aktualizacja reports/status.json [skip ci]` — automatyczny commit z pierwszego zielonego przebiegu CI po P3. |
| `ac49020` | P4 | `.github/workflows/pages.yml` (GitHub Pages) + degradacja panelu przy limicie GitHub API (dane z `raw.githubusercontent.com` działają niezależnie). |

Commit dla P5 (dokumentacja + ten raport) jeszcze nie istnieje w momencie
pisania tego pliku — zostanie utworzony po zatwierdzeniu przez użytkownika.

---

## 2. Status priorytetów

### P1 — Szkielet panelu
**Dostarczono:** `clos_studio/panel/index.html`, `panel.css`, `panel.js` — górny pasek, nawigacja boczna (7 sekcji, pozioma na `<820px`), `:focus-visible`, `prefers-reduced-motion`, stany `state-loading/empty/error`. Zero danych na tym etapie.

### P2 — Loader danych + render sekcji
**Dostarczono:** `fetch()` z KONTRAKTU DANYCH (`reports/academy/L1_1_pattern_echo.json`, `publications/competency_profile.json`, `publications/L1_1_pattern_echo/metadata.json`, `publications/preregistration_L1_1.json`, dynamiczne odkrywanie `publications/EXP-*/metadata.json` przez GitHub API — nie hardkodowana lista nazw). Wykres MSE±CI95 jako inline SVG. **Znaleziony i naprawiony w trakcie:** wyścig, w którym błąd jednego pliku był nadpisywany cichym częściowym renderem przy sukcesie drugiego — naprawione tak, że błąd i częściowe dane współistnieją.

### P3 — Źródło statusu testów/CI + walidator
**Dostarczono:** opcja (a) — `scripts/write_status.py` generuje `reports/status.json` w CI wyłącznie po zielonym `pytest` + 3 walidatorach; krok w `ci.yml` commituje go z powrotem do repo (`[skip ci]`, ograniczone do `github.ref == 'refs/heads/v0.7.2-scientific-integrity'` po doprecyzowaniu). `scripts/validate_panel.py` skanuje `panel.js` pod kątem wklejonych floatów (≥4 miejsca po przecinku), długich ciągów hex i literału `"263"`, ignorując URL-e/ścieżki. **Przetestowane negatywnie** (wklejona liczba → exit 1, cofnięte, exit 0).

### P4 — Hosting GitHub Pages
**Dostarczono:** `.github/workflows/pages.yml` + odporność na limit GitHub API (patrz sekcja 4 niżej — to była najdłuższa i najbardziej pouczająca część sprintu).

### P5 — Dokumentacja
**Dostarczono:** sekcja „Panel Badacza” w `README.md` (URL, co pokazuje, jak się odświeża, znane ograniczenie API), wpis `v0.8.5` w `ROADMAP.md`, ten raport.

---

## 3. Wyniki

- **Testy:** `263 passed` (`pytest -q`).
- **Walidatory:** `validate_publication.py` OK (5 bundli), `validate_artifacts.py` OK (1 raport), `validate_panel.py` OK (brak wklejonych metryk w `panel.js`).
- **CI:** zielone na `v0.7.2-scientific-integrity` dla wszystkich czterech commitów P1–P4 (zweryfikowane przez GitHub API, `conclusion: success` per-commit).
- **Panel live:** [https://gozimek79-debug.github.io/SST-Incubator/](https://gozimek79-debug.github.io/SST-Incubator/) — zweryfikowany zdalnie (poprawny `<title>`, wszystkie 7 pozycji nawigacji obecne w serwowanym HTML).

---

## 4. Uczciwa ocena — co poszło gładko, co nie, i czego NIE zweryfikowano

### Odyseja P4 (GitHub Pages) — nie było to "dodaj plik yml"

Pierwszy deploy `pages.yml` failował natychmiast (puste `steps[]`, ~1s).
Rzeczywista sekwencja przyczyn, w kolejności odkrywania:

1. **Pages nie było jeszcze realnie aktywne**, mimo że ustawienie Source w
   Settings wizualnie wyglądało na poprawne — sam dropdown bez pełnego
   zapisu/aktywacji nie wystarczał.
2. Próba naprawy przez GitHub UI (przeglądanie Settings → Pages) **dodała
   dwa konkurencyjne, auto-wygenerowane workflowy bezpośrednio na `main`**
   (`jekyll-gh-pages.yml`, `static.yml`) — efekt uboczny przycisku
   "Configure" w UI, nieplanowany przez nas. To faktycznie aktywowało Pages
   (potwierdzone: `Deploy Jekyll...` na `main` zakończyło się `success`),
   ale zostawiło dwa martwe pliki dzielące ten sam
   `concurrency: group: "pages"` co nasz workflow — w logach już widać było
   `static.yml` anulowany przez ten konflikt. Usunięte commitem
   `e3cce4c` na `main` (poza zakresem tego brancha — jedyna zmiana w tym
   sprincie wykonana na `main`, bo pliki tam właśnie wylądowały).
3. **Prawdziwa, ostateczna przyczyna:** środowisko `github-pages` miało
   regułę `custom_branch_policies` dopuszczającą **wyłącznie branch
   `main`** (potwierdzone przez `GET /repos/.../environments/github-pages/deployment-branch-policies`
   → dokładnie jeden wpis: `"main"`). Nasz workflow działa na
   `v0.7.2-scientific-integrity`, więc był odrzucany na starcie, zanim
   jakikolwiek krok się wykonał. Naprawione ręcznie przez użytkownika
   (dodanie reguły dla tego brancha w Settings → Environments).
4. Dopiero **7. próba** (`run_attempt: 7`) zakończyła się sukcesem.

Wniosek: `pages.yml` sam w sobie był poprawny od P4 commit `ac49020` —
problem był w konfiguracji repo (Settings), nie w kodzie. To rozróżnienie
jest ważne, bo bez logowania tej sekwencji ktoś mógłby błędnie wrócić do
edycji `pages.yml` szukając bugu, którego tam nie ma.

### Ograniczenie API rate-limit — świadomie zaakceptowane, nie wyeliminowane

Panel dalej używa nieautoryzowanego GitHub API dla dwóch rzeczy: historii
commitów (Przegląd) i listy legacy bundli (Prowenancja) — bo statyczny
panel bez backendu nie ma gdzie bezpiecznie trzymać tokena. Limit 60
zapytań/h na IP jest realny przy wielu odwiedzających z jednego zakresu
adresów. **Nie rozwiązaliśmy tego** (rozwiązaniem docelowym byłby backend
proxy albo generowanie tych list w CI, tak jak `status.json`) — tylko
ograniczyliśmy szkodę: `apiHttpError()`/`apiErrorHtml()` wykrywają 403 /
`x-ratelimit-remaining: 0` i pokazują czytelny komunikat wyłącznie w
dotkniętej karcie, podczas gdy reszta sekcji (dane z
`raw.githubusercontent.com`, w tym `status.json`) renderuje się normalnie.
Zweryfikowane lokalnie przez symulację (zepsuty `API_BASE`) — reszta
Przeglądu i cała karta prowenancji bundla L1.1 działały bez przerwy.

### Czego NIE zweryfikowano narzędziami

- **Render wykonany przez `panel.js` w prawdziwej przeglądarce na
  hostowanym Pages nie był sprawdzony narzędziem end-to-end.** Zweryfikowano
  osobno: (a) że `panel.js` poprawnie renderuje dane w lokalnym serwerze
  podglądu z tymi samymi artefaktami (wielokrotnie, przez `preview_eval`),
  oraz (b) że sam hostowany plik `index.html` jest serwowany poprawnie
  (właściwy `<title>`, wszystkie 7 pozycji nawigacji w statycznym HTML).
  Nie zweryfikowano bezpośrednio, że na `https://gozimek79-debug.github.io/SST-Incubator/`
  JS faktycznie wykonuje się i renderuje dane tak samo — `WebFetch` pobiera
  surowy HTML bez wykonania JavaScriptu, więc nie jest w stanie tego
  potwierdzić. Ryzyko jest niskie (identyczne pliki, identyczna logika
  `fetch()` z tym samym publicznym `raw.githubusercontent.com`, zero
  różnic specyficznych dla Pages poza ścieżkami — sprawdzonymi jako
  względne), ale to założenie, nie zmierzony fakt.
- Rzeczywisty ruch/liczba odwiedzających i to, czy limit API faktycznie
  kiedykolwiek zostanie osiągnięty w praktyce — nieznane, bo panel dopiero
  co poszedł live.

---

## 5. Status projektu

Nadal **Research Grade Infrastructure**. Ten sprint nie zmienia oceny
naukowej z `RAPORT_KONCOWY_v0.8.4.md` (6/13 kompetencji zmierzonych, 4/13 z
ważnym CI95, jedna lekcja) — dodaje wyłącznie warstwę prezentacji tych
samych, niezmienionych danych. Panel jest odzwierciedleniem stanu repo, nie
nowym źródłem twierdzeń.

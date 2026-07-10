# SPRINT v0.8.5 — CLOS Studio: Panel Badacza (repo-native, hostowany)

Wykonywalna specyfikacja. Gałąź: `v0.7.2-scientific-integrity`. Po każdym
priorytecie uruchom testy/walidatory; na końcu push i potwierdzenie stanu zdalnego.

Cel: jedno okno w przeglądarce pod stałym URL, pokazujące WSZYSTKIE wyniki i
raporty — czytane na żywo z artefaktów repo, bez uruchamiania czegokolwiek.

---

## ZASADY NADRZĘDNE (nie łam)

1. **CORE FROZEN.** Zero zmian w `clos_brain/`, `clos_kernel/`, `genome/`, `birth/`.
   Panel to warstwa prezentacji — nie dotyka nauki.
2. **ŻADNEJ LICZBY NA SZTYWNO.** Każda wartość w panelu (MSE, CI95, n_eff, hash,
   liczba testów, status kompetencji) MUSI pochodzić z pobranego pliku JSON.
   Zakaz wklejania metryk do kodu panelu. To jest twardy wymóg integralności —
   panel z wklejonymi liczbami rozjedzie się z danymi, dokładnie to zwalczamy.
3. **Panel odzwierciedla dane, nie upiększa.** Jeśli JSON mówi
   `status: insufficient_data` — panel pokazuje lukę. Jeśli `ci95_valid: false` —
   pokazuje flagę. Nie chowaj braków. 6/13 ma być widoczne jako 6/13.
4. **Bez kroku budowania (no build step).** Statyczne pliki (HTML/CSS/JS),
   działające po otwarciu i na GitHub Pages bez `npm`/node. Wykresy jako inline
   SVG (nie biblioteki wymagające bundlingu).
5. **Weryfikacja, nie deklaracja.** `pytest -q` (263) i oba walidatory muszą
   zostać zielone; CI ma przejść na zdalnym repo.

Zakazane: build z node/bundlerem, framework wymagający kompilacji, backend,
jakiekolwiek zmiany w Core.

---

## KONTEKST

Istnieje prototyp wyglądu: `clos-studio-panel.jsx` (dostarczony osobno) —
konsola instrumentu laboratoryjnego, nawigacja boczna, 7 sekcji, element-sygnatura
= instrument kompetencji z jawnymi lukami. Odtwórz TEN język wizualny, ale jako
statyczne pliki czytające dane na żywo. Prototyp jest referencją designu, nie
źródłem danych.

## KONTRAKT DANYCH (co panel czyta)

Panel pobiera (fetch) wyłącznie te artefakty z repo:
- `reports/academy/L1_1_pattern_echo.json` — wyniki lekcji, staty per genom.
- `publications/competency_profile.json` — 13 pojęć: status, wartości per genom,
  cohens_d, n_effective, ci95_valid.
- `publications/L1_1_pattern_echo/metadata.json` — prowenancja (git_commit,
  config_hash, manifest_hash, timestamp, experiment_id, reproducible, total_runs).
- `publications/preregistration_L1_1.json` — hipoteza, endpointy, kryteria.
- `publications/EXP-*/metadata.json` — lista legacy (provenance="legacy-pre-0.7.2").

Ścieżka bazowa (BASE) konfigurowalna na górze pliku JS; domyślnie
`https://raw.githubusercontent.com/gozimek79-debug/SST-Incubator/v0.7.2-scientific-integrity/`
(raw.githubusercontent ma CORS `*`, więc panel działa z Pages, z Vercela i lokalnie).

---

## PRIORYTET 1 — Szkielet panelu (statyczny)

`clos_studio/panel/`: `index.html`, `panel.css`, `panel.js`.
- Górny pasek: marka „CLOS STUDIO · Panel Badacza", pill statusu, gałąź@commit.
- Nawigacja boczna (7 sekcji): Przegląd, Lekcje i wyniki, Profil kompetencji,
  Porównanie genomów, Prowenancja, Testy i CI, Raporty. Przełączanie w miejscu
  (jedno okno). Responsywny (na wąskim ekranie nawigacja u góry).
- Jakość podłogi: focus klawiatury, `prefers-reduced-motion`, sensowne stany
  pustki/ładowania/błędu (komunikat mówi CO poszło nie tak i JAK czytać dane).
- Zero danych na tym etapie — same sekcje i loader-stub.

## PRIORYTET 2 — Loader danych + render sekcji

- `panel.js` pobiera artefakty z KONTRAKTU DANYCH (async, z obsługą błędu per plik).
- Render każdej sekcji WYŁĄCZNIE z pobranego JSON:
  - Przegląd: status, liczba testów (z gdzie? — patrz niżej), CI, Core frozen,
    licznik kompetencji (policzony z competency_profile.json, nie wpisany),
    oś czasu commitów (opcjonalnie z GitHub API `/commits`).
  - Lekcje: L1.1 z prerejestracji + raportu; wykres MSE@50 ± CI95 jako inline SVG.
  - Profil kompetencji: 13 wierszy z competency_profile.json; stany valid/
    degenerate/insufficient rozróżnione wizualnie; licznik „zmierzone X/13,
    ważne CI95 Y/13" policzony z danych.
  - Porównanie genomów: tabela z pojęć `valid`; cohens_d z danych.
  - Prowenancja: 5 pól z metadata.json + lista legacy.
  - Testy i CI: patrz P3 (źródło liczby testów i statusu CI).
  - Raporty: lista plików z linkami do repo (GitHub blob URL).
- „Świeżość danych": pokaż `timestamp` z metadata.json w stopce.

## PRIORYTET 3 — Źródła statusu (testy/CI) + egzekwowanie integralności

- Liczba testów i status CI NIE mogą być wpisane. Dwie opcje (wybierz jedną,
  udokumentuj):
  (a) generowany artefakt `reports/status.json` tworzony w CI po `pytest`
      (liczba passed) i po walidatorach — panel go czyta; albo
  (b) GitHub API `/actions/runs` (conclusion) dla statusu CI.
- Dodaj `scripts/validate_panel.py`: skanuje `clos_studio/panel/panel.js` i
  FAILUJE (exit≠0), jeśli znajdzie wklejone metryki (np. liczby zmiennoprzecinkowe
  z ≥4 miejscami po przecinku, znane hashe, „263"). Panel ma czytać, nie zawierać.
  Dodaj do `.github/workflows/ci.yml`. Zrób test negatywny (wklej liczbę → exit≠0).

## PRIORYTET 4 — Hosting (GitHub Pages)

- `.github/workflows/pages.yml`: publikuje panel na GitHub Pages
  (źródło: `clos_studio/panel/` lub `/docs`). Stały URL.
- Jeśli Pages wymaga artefaktów w publikowanym katalogu — użyj BASE = raw
  URL (kontrakt danych), żeby nie duplikować JSON-ów.
- Alternatywa Vercel: dopisz krótką instrukcję w README, nie konfiguruj obu.

## PRIORYTET 5 — Dokumentacja

- README sekcja „Panel Badacza": URL, co pokazuje, że aktualizuje się z artefaktów
  (świeżość = ostatni run + push), jak odświeżyć.
- ROADMAP: dopisz panel jako narzędzie warstwy Studio (read-only).

---

## PRODUKT KOŃCOWY

`clos_studio/panel/` (index.html+css+js) czytający dane na żywo; `validate_panel.py`
w CI; workflow Pages ze stałym URL; sekcja w README; `RAPORT_v0.8.5.md` z listą zmian
i uczciwą oceną (co działa, czego jeszcze nie — np. czy licznik commitów jest z API
czy statyczny, czy CI-status jest live).

## DYSCYPLINA GITA

- Jeden logiczny commit na priorytet; `pytest -q` + walidatory zielone przed commitem.
- Komunikat commita = realny stan (liczba testów faktyczna).
- Na końcu `git push origin v0.7.2-scientific-integrity`; `git status` = „up to date".
- Nie commituj śmieci ze `storage/` (jest `.gitignore`).
- Po pushu potwierdź, że workflow Pages zbudował URL i panel się otwiera.

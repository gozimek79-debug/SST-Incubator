# CLOS Cognitive Ontology (v0.8.4)

Jedna obowiązująca definicja pojęć poznawczych używanych w CLOS Cognitive
Academy. Każda przyszła metryka, lekcja i oś Competency Profile odnosi się
do definicji z tego dokumentu — nie tworzymy równoległych, nieformalnych
znaczeń tych samych słów w raportach.

Zasada uczciwości (SPRINT_v0.8.4.md): pole (c) mówi, czy dane pojęcie jest
faktycznie **zmierzone przez istniejącą lekcję**, czy tylko **zaimplementowane
jako mechanizm w Brain Runtime** bez lekcji, która by je testowała. Mechanizm
bez lekcji nie jest dowodem zdolności poznawczej — jest tylko kodem.

Obecnie istnieje jedna lekcja: **L1.1 "Pattern Echo"**
([clos_academy/lesson_L1_1.py](../clos_academy/lesson_L1_1.py)), z hipotezą
o Working Memory jako primary endpoint oraz kilkoma metrykami pobocznymi
(secondary endpoints) liczonymi przy okazji tego samego przebiegu.

---

## Perception

**(a) Opis poznawczy:** Zdolność do przyjęcia surowego bodźca ze świata
i zarejestrowania go jako aktualnego stanu wejściowego, dostępnego dla
dalszych procesów (predykcji, pamięci).

**(b) Mierzalny korelat/metryka:** `BrainTissue.last_input`,
`BrainTissue.sensory_buffer` — ustawiane przez
`perceive()` ([clos_brain/runtime/perception.py](../clos_brain/runtime/perception.py)).
Metryka wprost testująca wierność percepcji (np. zgodność
`last_input` z bodźcem świata w warunkach szumu) nie istnieje.

**(c) Lekcja:** not yet measured — mechanizm jest używany jako substrat
wewnątrz L1.1 (każdy tick fazy stymulacji wywołuje `perceive()`), ale żadna
lekcja nie stawia hipotezy o samej percepcji ani jej nie izoluje jako
primary/secondary endpoint.

---

## Attention

**(a) Opis poznawczy:** Selektywne filtrowanie, które ślady pamięciowe (lub
bodźce) są brane pod uwagę przy generowaniu predykcji, zamiast uśredniania
po całej pamięci.

**(b) Mierzalny korelat/metryka:** `BrainTissue.attention_threshold` — próg
odległości `stimulus_hash`, używany w
`predict()` ([clos_brain/runtime/prediction.py:29](../clos_brain/runtime/prediction.py))
do wyboru `matching_records`. Możliwa metryka (niezaimplementowana): odsetek
rekordów pamięci przechodzących filtr względem danego wejścia.

**(c) Lekcja:** not yet measured — parametr istnieje i wpływa na wynik L1.1
pośrednio (przez dobór rekordów do predykcji), ale żadna lekcja nie mierzy
ani nie manipuluje `attention_threshold` jako zmienną niezależną.

---

## Pattern Recognition

**(a) Opis poznawczy:** Zdolność do rozpoznania bieżącego bodźca jako
pasującego do wcześniej zaobserwowanego wzorca (dopasowanie
stimulus → istniejący ślad pamięciowy), odzwierciedlona w trafności
predykcji w trakcie prezentacji bodźca.

**(b) Mierzalny korelat/metryka:** `mse_stimulus_phase` — średni błąd
(`|prediction - pattern_signal|`) liczony w fazie stymulacji (tick < 100),
zwracany w `run_pattern_echo()`
([clos_academy/lesson_L1_1.py](../clos_academy/lesson_L1_1.py)).

**(c) Lekcja:** L1.1 (secondary endpoint: `mse_stimulus_phase`).

---

## Pattern Retention

**(a) Opis poznawczy:** Zdolność śladu pamięciowego do utrzymania niskiego
błędu (nieosłabiania się) w czasie, mimo naturalnego zaniku (decay).

**(b) Mierzalny korelat/metryka:** `memory_decay_rate` = `(mse_silence_phase
- mse_stimulus_phase) / silence_ticks`, liczone w `run_pattern_echo()`; u
podstaw mechanizm `apply_decay()`
([clos_brain/runtime/plasticity.py:67](../clos_brain/runtime/plasticity.py))
zwiększający `error` w rekordach pamięci co tick ciszy.

**(c) Lekcja:** L1.1 (secondary endpoint: `memory_decay_rate`).

---

## Working Memory

**(a) Opis poznawczy:** Zdolność do utrzymania wewnętrznej reprezentacji
wzorca **po usunięciu bodźca** (faza ciszy), bez dalszej stymulacji — czyli
odtworzenia wzorca "z pamięci", nie z bieżącego sygnału świata.

**(b) Mierzalny korelat/metryka:** primary endpoint
`mse_vs_pattern_after_stimulus_removal` @ tick 50 (`mse_at_tick_50`) —
średni błąd predykcji względem `pattern_signal` w oknie ciszy od
`stimulus_ticks + 50` do końca przebiegu, przy zamrożonym buforze
sensorycznym (`silent_step()`,
[clos_academy/echo_runtime.py](../clos_academy/echo_runtime.py)).
PASS gdy `mse_at_tick_50 < 0.5`.

**(c) Lekcja:** L1.1 (primary endpoint) —
patrz [publications/preregistration_L1_1.json](../publications/preregistration_L1_1.json).

---

## Long-term Memory

**(a) Opis poznawczy:** Odrębny od Working Memory magazyn, konsolidujący
wzorce na skalę czasową wykraczającą poza pojedynczy przebieg/epizod
(np. transfer między sesjami, odporność na reset stanu).

**(b) Mierzalny korelat/metryka:** brak. `BrainTissue.memory` to pojedyncza,
jednolita struktura z jednym mechanizmem zaniku (`decay_rate`) — kod nie
rozróżnia pamięci roboczej od długoterminowej ani nie implementuje
konsolidacji/transferu między przebiegami.

**(c) Lekcja:** not yet measured — brak mechanizmu i brak lekcji.

---

## Prediction

**(a) Opis poznawczy:** Generowanie oczekiwanej wartości bieżącego (lub
przyszłego) bodźca na podstawie zapamiętanych wzorców, ważonej pewnością
(błędem) poszczególnych śladów.

**(b) Mierzalny korelat/metryka:** `BrainTissue.last_prediction`, ustawiane
przez `predict()`
([clos_brain/runtime/prediction.py](../clos_brain/runtime/prediction.py))
jako średnia ważona `matching_records` po odwrotności ich błędu.

**(c) Lekcja:** L1.1 (pośrednio — `last_prediction` jest składnikiem każdej
metryki MSE w tej lekcji), ale żadna lekcja nie testuje predykcji "w przód"
(przewidywania bodźca, który jeszcze nie wystąpił) jako osobnej hipotezy —
w tym węższym sensie: not yet measured.

---

## Adaptation

**(a) Opis poznawczy:** Tempo, w jakim system osiąga stabilny stan
(energetyczny/entropijny) po zmianie warunków — jak szybko "dostraja się"
do nowego reżimu bodźców.

**(b) Mierzalny korelat/metryka:** `adaptation_tick` = wynik
`detect_phases()`
([clos_scientist/analyzer.py](../clos_scientist/analyzer.py)),
`_find_adaptation_end()` — tick, w którym energia stabilizuje się w oknie
10 kroków poniżej progu zmienności.

**(c) Lekcja:** L1.1 (secondary endpoint: `adaptation_tick`).

---

## Exploration

**(a) Opis poznawczy:** Aktywne różnicowanie działań/próbkowania w celu
zdobycia nowej informacji (kompromis eksploracja–eksploatacja), a nie tylko
bierne odtwarzanie ostatniego bodźca.

**(b) Mierzalny korelat/metryka:** brak. `act()`
([clos_brain/runtime/action.py](../clos_brain/runtime/action.py)) w wersji
v0.1 to czysty "echo input" (`return brain.last_input`) — nie ma żadnego
mechanizmu wyboru działania, więc nie ma czego mierzyć.

**(c) Lekcja:** not yet measured — brak mechanizmu i brak lekcji.

---

## Generalization

**(a) Opis poznawczy:** Zdolność do przenoszenia wzorca/reprezentacji
nauczonej w jednym scenariuszu (np. `noise_world`) na nowy, wcześniej
niewidziany scenariusz lub warunki, bez ponownego uczenia od zera.

**(b) Mierzalny korelat/metryka:** brak. Żadna lekcja nie trenuje na jednym
scenariuszu i nie testuje na innym w tym samym przebiegu.

**(c) Lekcja:** not yet measured.

---

## Planning

**(a) Opis poznawczy:** Wybór sekwencji działań w oparciu o przewidywane,
przyszłe stany (multi-step lookahead), a nie tylko reakcja na bieżący
bodziec.

**(b) Mierzalny korelat/metryka:** brak. Warstwa akcji (`act()`) nie ma
pojęcia sekwencji ani horyzontu czasowego dłuższego niż bieżący tick.

**(c) Lekcja:** not yet measured — brak mechanizmu i brak lekcji.

---

## Stability

**(a) Opis poznawczy:** Odporność stanu wewnętrznego (entropia, błąd
predykcji) na fluktuacje w czasie — niska zmienność przy braku zewnętrznych
wstrząsów.

**(b) Mierzalny korelat/metryka:** `stability_score`, liczony przez
`stability_index()`
([clos_scientist/metrics.py:8](../clos_scientist/metrics.py)) jako
`1 / (std(entropy) + std(error) + 1e-6)` na snapshotach przebiegu, zwracany
w `ExperimentReport` ([clos_scientist/experiment.py](../clos_scientist/experiment.py)).

**(c) Lekcja:** L1.1 (secondary endpoint: `stability_score`;
`pass_conditions.stability_score_min = 0.3` w prerejestracji).

---

## Energy Efficiency

**(a) Opis poznawczy:** Koszt energetyczny utrzymania funkcji poznawczych w
czasie — ile "budżetu" (energii) system zużywa na jednostkę działania lub
czasu, w tym koszt dodatkowy stanu stresu.

**(b) Mierzalny korelat/metryka:** `final_energy` (`BrainTissue.energy` na
koniec przebiegu, wyjście `run_pattern_echo()`); u podstaw
`regulate()` ([clos_brain/runtime/homeostasis.py](../clos_brain/runtime/homeostasis.py)),
stały koszt `energy_decay = 0.001`/tick + dodatkowy koszt stresu przy
`entropy > 0.7`. Osobno: `energy_drift()`
([clos_scientist/metrics.py:46](../clos_scientist/metrics.py)).
**Zastrzeżenie:** mierzymy zużycie energii, nie efektywność względem
zadania — nie ma znormalizowanego wskaźnika koszt/korzyść (np. energia na
jednostkę poprawnie odtworzonego wzorca).

**(c) Lekcja:** L1.1 (secondary endpoint: `final_energy`), w węższym sensie
"efektywności" (koszt/korzyść): not yet measured.

# CLOS Cognitive Ontology v0.8

## Perception
Zdolnosc do odbioru i rejestracji bodzca zmyslowego. Mierzona jako zmiana
entropii w odpowiedzi na pierwszy bodziec. Primary endpoint: entropy_volatility
w pierwszych 20 tickach.

## Attention
Zdolnosc do odroznienia sygnalu od szumu. Mierzona jako stosunek
entropy_volatility w noise_world vs stable_world. Im wyzszy wskaznik,
tym lepsza filtracja szumu.

## Pattern Recognition
Zdolnosc do wykrycia powtarzalnego wzorca w strumieniu bodzcow.
Mierzona jako spadek MSE w stable_world po 100 tickach.

## Pattern Retention
Zdolnosc do zapamietania wykrytego wzorca. Mierzona jako MSE po usunieciu
bodzca (Pattern Echo). Primary endpoint L1.1.

## Working Memory
Utrzymywanie reprezentacji wzorca przez 20-100 tickow po zakonczeniu
stymulacji. Badane w Lesson L1.1.

## Short-term Memory
Utrzymywanie reprezentacji przez 5-20 tickow.

## Long-term Memory
Utrzymywanie reprezentacji przez >100 tickow.

## Prediction
Zdolnosc do przewidywania przyszlych bodzcow na podstawie historii.
Mierzona jako MSE = (prediction - actual)^2.

## Adaptation
Zdolnosc do dostosowania sie do zmian srodowiska. Mierzona jako
adaptation_tick – tick rozpoczecia stabilizacji po szoku.

## Exploration
Zdolnosc do testowania nowych strategii. Mierzona jako entropy_volatility
w nowym srodowisku. Wyzsza entropia = wiecej eksploracji.

## Generalization
Zdolnosc do zastosowania wyuczonego wzorca w nowym kontekscie.
Mierzona jako MSE w drift_world / MSE w stable_world.

## Planning
Zdolnosc do dzialania z wyprzedzeniem. Nie mierzona w v0.8.

## Stability
Zdolnosc do utrzymania homeostazy. Mierzona jako stability_score.

## Energy Efficiency
Zdolnosc do minimalizacji kosztu energetycznego. Mierzona jako
energy_drift na tick.

## Recovery
Zdolnosc do powrotu do stabilnosci po szoku. Mierzona jako
liczba tickow od STABILITY_DROP do powrotu stability > 1.0.

Kazda definicja jest obowiazujaca dla wszystkich modulow CLOS od v0.8.

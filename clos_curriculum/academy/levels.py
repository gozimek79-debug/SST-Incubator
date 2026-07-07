"""Level Definitions – ontogeneza sztucznego mózgu.

Każdy poziom to zestaw lekcji i egzamin.
Poziom zaliczony tylko po zdaniu egzaminu.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from .lesson import LessonManifest


@dataclass
class Level:
    """Poziom rozwoju poznawczego."""

    level_id: int
    name: str
    description: str
    lessons: List[LessonManifest] = field(default_factory=list)
    exam: List[LessonManifest] = field(default_factory=list)
    required_pass_rate: float = 0.8  # 80% lekcji musi być zaliczonych

    def total_lessons(self) -> int:
        return len(self.lessons)

    def total_exam_lessons(self) -> int:
        return len(self.exam)

    def summary(self) -> str:
        lines = [
            f"Level {self.level_id}: {self.name}",
            f"  {self.description}",
            f"  Lessons: {self.total_lessons()}",
            f"  Exam: {self.total_exam_lessons()} lessons",
            f"  Pass rate: {self.required_pass_rate*100:.0f}%",
        ]
        return "\n".join(lines)


def create_level_0() -> Level:
    """LEVEL 0: Narodziny – podstawowe reakcje sensoryczne."""
    return Level(
        level_id=0,
        name="Birth & Sensory Reaction",
        description="Brain rodzi się i uczy podstawowej homeostazy oraz reakcji na bodźce.",
        lessons=[
            LessonManifest(
                lesson_id="L0.1", level=0,
                name="First Breath – Homeostasis",
                description="Brain uczy się utrzymywać homeostazę w stabilnym środowisku.",
                hypothesis="Brain osiągnie stability_score > 1.0 w stable_world.",
                research_question="Czy nowo narodzony Brain potrafi utrzymać homeostazę?",
                genome_presets=["default"],
                scenarios=["stable_world"],
                seeds=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                ticks=300,
                primary_endpoint="stability_score",
                pass_conditions={"stability_score_min": 1.0},
                fail_conditions={"stability_score_max": 0.5},
                tags=["birth", "homeostasis", "basic"],
            ),
            LessonManifest(
                lesson_id="L0.2", level=0,
                name="First Light – Sensory Response",
                description="Brain uczy się reagować na zmienne bodźce.",
                hypothesis="Brain zareaguje zmianą entropii na bodziec.",
                research_question="Czy Brain wykrywa zmiany w środowisku?",
                genome_presets=["default"],
                scenarios=["stable_world", "noise_world"],
                seeds=list(range(1, 11)),
                ticks=300,
                primary_endpoint="entropy_volatility",
                pass_conditions={"entropy_volatility_min": 0.01},
                tags=["sensory", "response", "basic"],
            ),
        ],
        exam=[
            LessonManifest(
                lesson_id="EXAM0", level=0,
                name="Level 0 Exam – Basic Survival",
                description="Brain musi przetrwać w 4 scenariuszach.",
                hypothesis="Brain zaliczy minimum 3/4 scenariuszy.",
                research_question="Czy Brain posiada podstawowe kompetencje przetrwania?",
                genome_presets=["default"],
                scenarios=["stable_world", "noise_world", "drift_world", "shock_world"],
                seeds=list(range(1, 21)),
                ticks=500,
                primary_endpoint="stability_score",
                min_seeds=20,
                min_ticks=500,
                pass_conditions={"stability_score_min": 0.5},
                tags=["exam", "level0", "survival"],
            ),
        ],
    )


def create_level_1() -> Level:
    """LEVEL 1: Pattern Retention & Short Memory."""
    return Level(
        level_id=1,
        name="Pattern Retention & Memory",
        description="Brain uczy się zapamiętywać wzorce i przewidywać.",
        lessons=[
            LessonManifest(
                lesson_id="L1.1", level=1,
                name="Pattern Recognition",
                description="Brain uczy się rozpoznawać powtarzalne wzorce.",
                hypothesis="Brain zmniejszy MSE poniżej 0.5 po 500 tickach.",
                research_question="Czy Brain uczy się wzorców?",
                genome_presets=["default", "highly_plastic"],
                scenarios=["stable_world"],
                seeds=list(range(1, 11)),
                ticks=500,
                primary_endpoint="mse",
                pass_conditions={"mse_max": 0.5},
                tags=["pattern", "memory", "learning"],
            ),
        ],
        exam=[
            LessonManifest(
                lesson_id="EXAM1", level=1,
                name="Level 1 Exam – Pattern Mastery",
                description="Brain musi wykazać zdolność predykcji.",
                hypothesis="Brain osiągnie MSE < 0.3 w stable_world.",
                research_question="Czy Brain opanował przewidywanie?",
                genome_presets=["default", "highly_plastic"],
                scenarios=["stable_world", "noise_world"],
                seeds=list(range(1, 21)),
                ticks=500,
                primary_endpoint="mse",
                min_seeds=20,
                pass_conditions={"mse_max": 0.3},
                tags=["exam", "level1", "prediction"],
            ),
        ],
    )


def create_level_2() -> Level:
    """LEVEL 2: Plasticity & Shock Adaptation."""
    return Level(
        level_id=2,
        name="Plasticity & Adaptation",
        description="Brain uczy się adaptować do szoków i zmiennych warunków.",
        lessons=[
            LessonManifest(
                lesson_id="L2.1", level=2,
                name="Shock Response",
                description="Brain uczy się reagować na nagłe zmiany.",
                hypothesis="Brain wykryje anomalię w shock_world.",
                research_question="Czy Brain adaptuje się po szoku?",
                genome_presets=["default", "highly_plastic"],
                scenarios=["shock_world"],
                seeds=list(range(1, 11)),
                ticks=500,
                primary_endpoint="adaptation_tick",
                pass_conditions={"adaptation_tick_max": 100},
                tags=["shock", "adaptation", "plasticity"],
            ),
        ],
        exam=[
            LessonManifest(
                lesson_id="EXAM2", level=2,
                name="Level 2 Exam – Resilience",
                description="Brain musi przetrwać wielokrotne szoki.",
                hypothesis="Brain zachowa stability > 0.3 po serii szoków.",
                research_question="Czy Brain jest odporny na perturbacje?",
                genome_presets=["default", "highly_plastic"],
                scenarios=["shock_world", "noise_world"],
                seeds=list(range(1, 21)),
                ticks=500,
                primary_endpoint="stability_score",
                min_seeds=20,
                pass_conditions={"stability_score_min": 0.3},
                tags=["exam", "level2", "resilience"],
            ),
        ],
    )


ALL_LEVELS = {
    0: create_level_0(),
    1: create_level_1(),
    2: create_level_2(),
}


def get_level(level_id: int) -> Level:
    if level_id not in ALL_LEVELS:
        raise ValueError(f"Level {level_id} not defined. Available: {list(ALL_LEVELS.keys())}")
    return ALL_LEVELS[level_id]


def list_levels() -> List[int]:
    return sorted(ALL_LEVELS.keys())

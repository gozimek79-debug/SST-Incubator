"""Wspólne typy dla Scientist."""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any


@dataclass
class PhaseResult:
    """Wynik detekcji fazy."""
    name: str
    start_tick: int
    end_tick: int
    duration: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "duration": self.duration
        }


@dataclass
class ExperimentReport:
    """Raport z eksperymentu."""
    run_id: str
    metrics: Dict[str, float] = field(default_factory=dict)
    phases: Dict[str, int] = field(default_factory=dict)
    anomalies: List[int] = field(default_factory=list)
    stability_score: float = 0.0
    mse: float = 0.0
    adaptation_speed_ticks: int = 0
    raw_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "stability_score": round(self.stability_score, 4),
            "mse": round(self.mse, 4),
            "phases": self.phases,
            "anomalies": self.anomalies,
            "metrics": self.metrics,
            "adaptation_speed_ticks": self.adaptation_speed_ticks,
            "raw_summary": self.raw_summary
        }


@dataclass
class ExperimentResult:
    """Pełny wynik eksperymentu."""
    report: ExperimentReport
    snapshots_count: int
    events_count: int
    duration_ticks: int

"""Observation Engine v0.7.3 – eksport zdarzen do events.jsonl."""

import json, os
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class ObservationEvent:
    tick: int
    run_id: str
    event_type: str
    value: float
    threshold: float
    metadata: Dict[str, Any]

    def to_dict(self): return asdict(self)


OBSERVATION_RULES = [
    {"type":"ENTROPY_SPIKE","field":"entropy","threshold":0.5,"compare":"gt"},
    {"type":"STABILITY_DROP","field":"stability_score","threshold":1.0,"compare":"lt"},
    {"type":"ENERGY_CRISIS","field":"final_energy","threshold":0.5,"compare":"lt"},
    {"type":"ADAPTATION_START","field":"adaptation_tick","threshold":100,"compare":"lt"},
    {"type":"MEMORY_EXPANSION","field":"memory_size","threshold":50,"compare":"gt"},
]


def detect_events(run_result: Dict[str, Any], run_id: str) -> List[ObservationEvent]:
    events = []
    for rule in OBSERVATION_RULES:
        field = rule["field"]
        if field in run_result:
            value = run_result[field]
            triggered = False
            if rule["compare"] == "gt" and value > rule["threshold"]:
                triggered = True
            elif rule["compare"] == "lt" and value < rule["threshold"]:
                triggered = True
            if triggered:
                events.append(ObservationEvent(
                    tick=run_result.get("ticks", 0),
                    run_id=run_id,
                    event_type=rule["type"],
                    value=value,
                    threshold=rule["threshold"],
                    metadata={"field":field, "compare":rule["compare"]},
                ))
    return events


def export_events(events: List[ObservationEvent], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "a", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")


def export_events_batch(run_results: List[Dict[str, Any]], experiment_id: str, output_dir: str = "observations"):
    path = f"{output_dir}/{experiment_id}/events.jsonl"
    all_events = []
    for r in run_results:
        run_id = r.get("run_id", "unknown")
        events = detect_events(r, run_id)
        all_events.extend(events)
        export_events(events, path)
    return path, len(all_events)

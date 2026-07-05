"""Reporter – generowanie raportów JSON i tekstowych."""

import json
from pathlib import Path
from typing import List, Dict
from clos_kernel.snapshot_engine import Snapshot
from .types import ExperimentReport
from .metrics import compute_all_metrics, stability_index, mse as compute_mse
from .analyzer import detect_phases, detect_anomalies, compute_adaptation_speed


def generate_report(
    run_id: str,
    snapshots: List[Snapshot],
    output_dir: str = "reports"
) -> ExperimentReport:
    """Generuje raport z eksperymentu."""
    metrics = compute_all_metrics(snapshots)
    phases = detect_phases(snapshots)
    anomalies = detect_anomalies(snapshots)
    stability = stability_index(snapshots)
    mse_val = compute_mse(snapshots)
    adaptation_tick = compute_adaptation_speed(snapshots)

    report = ExperimentReport(
        run_id=run_id,
        metrics=metrics,
        phases=phases,
        anomalies=anomalies,
        stability_score=round(stability, 4),
        mse=round(mse_val, 4),
        adaptation_speed_ticks=adaptation_tick,
        raw_summary={
            "snapshots_count": len(snapshots),
            "first_tick": snapshots[0].tick if snapshots else 0,
            "last_tick": snapshots[-1].tick if snapshots else 0,
            "detected_anomalies_count": len(anomalies)
        }
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / f"{run_id}_report.json"

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    return report


def format_text_report(report: ExperimentReport) -> str:
    """Formatuje raport jako czytelny tekst (tylko ASCII)."""
    lines = [
        "=" * 60,
        f"EXPERIMENT REPORT: {report.run_id}",
        "=" * 60,
        "",
        "--- METRICS ---",
        f"  Stability Score:      {report.stability_score:.4f}",
        f"  MSE:                  {report.mse:.4f}",
        f"  Entropy Volatility:   {report.metrics.get('entropy_volatility', 0):.4f}",
        f"  Energy Drift:         {report.metrics.get('energy_drift', 0):.4f}",
        f"  Memory Growth Rate:   {report.metrics.get('memory_growth_rate', 0):.4f}",
        "",
        "--- PHASES ---",
        f"  Initial Chaos:   tick {report.phases.get('initial_chaos', 0)}",
        f"  Adaptation:      tick {report.phases.get('adaptation', 0)}",
        f"  Convergence:     tick {report.phases.get('convergence', 0)}",
        "",
        f"  Adaptation Speed: {report.adaptation_speed_ticks} ticks",
        "",
        f"--- ANOMALIES ({len(report.anomalies)}) ---",
    ]

    if report.anomalies:
        anomalies_str = ", ".join(str(a) for a in report.anomalies[:20])
        if len(report.anomalies) > 20:
            anomalies_str += f"... (+{len(report.anomalies) - 20} more)"
        lines.append(f"  Ticks: {anomalies_str}")
    else:
        lines.append("  No anomalies detected.")

    lines.extend([
        "",
        "--- RAW SUMMARY ---",
        f"  Snapshots: {report.raw_summary.get('snapshots_count', 0)}",
        f"  Tick Range: {report.raw_summary.get('first_tick', 0)} -> {report.raw_summary.get('last_tick', 0)}",
        f"  Anomalies Count: {report.raw_summary.get('detected_anomalies_count', 0)}",
        "",
        "=" * 60
    ])

    return "\n".join(lines)

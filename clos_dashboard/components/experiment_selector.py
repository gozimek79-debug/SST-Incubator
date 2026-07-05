"""Komponenty Dashboardu – experiment selector i metadata (tylko ASCII)."""

from typing import Dict, List, Any


def render_experiment_selector(experiments: List[Dict[str, Any]]) -> str:
    """Renderuje listę eksperymentów jako tekst."""
    if not experiments:
        return "No experiments in registry."

    lines = ["EXPERIMENTS IN REGISTRY", "-" * 40]
    for exp in experiments:
        lines.append(
            f"  {exp['run_id']}  |  "
            f"Ticks: {exp['ticks']}  |  "
            f"Stability: {exp['stability_score']:.3f}  |  "
            f"MSE: {exp['mse']:.4f}  |  "
            f"Anomalies: {exp['anomalies_count']}"
        )
    return "\n".join(lines)


def render_metadata_panel(report_dict: Dict[str, Any]) -> str:
    """Renderuje panel metadanych."""
    lines = [
        "METADATA",
        "-" * 40,
        f"  Run ID:           {report_dict.get('run_id', 'N/A')}",
        f"  Stability Score:  {report_dict.get('stability_score', 'N/A')}",
        f"  MSE:              {report_dict.get('mse', 'N/A')}",
        f"  Adaptation Tick:  {report_dict.get('adaptation_speed_ticks', 'N/A')}",
        "",
        "PHASES",
        "-" * 40,
    ]
    phases = report_dict.get("phases", {})
    for phase_name, tick in phases.items():
        lines.append(f"  {phase_name}: tick {tick}")

    anomalies = report_dict.get("anomalies", [])
    lines.append("")
    lines.append(f"ANOMALIES: {len(anomalies)} detected")
    if anomalies:
        lines.append(f"  Ticks: {anomalies[:10]}{'...' if len(anomalies) > 10 else ''}")

    return "\n".join(lines)


def render_phase_overlay(report_dict: Dict[str, Any], max_tick: int) -> str:
    """Renderuje overlay faz na osi czasu (tylko ASCII)."""
    phases = report_dict.get("phases", {})
    lines = ["PHASE TIMELINE", "-" * 40]

    bar_width = min(max_tick + 1, 60)
    timeline = ["-"] * bar_width

    for phase_name, tick in phases.items():
        if tick >= 0 and max_tick > 0:
            pos = int(tick / max_tick * (bar_width - 1))
            if 0 <= pos < bar_width:
                timeline[pos] = "|"

    lines.append("".join(timeline))
    lines.append("")

    for phase_name, tick in phases.items():
        lines.append(f"  | {phase_name}: tick {tick}")

    return "\n".join(lines)

"""Komponenty Dashboardu – metadata panel."""

from typing import Dict, Any


def render_metadata(report_dict: Dict[str, Any]) -> str:
    """Renderuje pełny panel metadanych.

    Args:
        report_dict: Raport w formacie dict.

    Returns:
        Sformatowany tekst.
    """
    lines = [
        "=" * 50,
        "EXPERIMENT METADATA",
        "=" * 50,
        f"Run ID:        {report_dict.get('run_id', 'N/A')}",
        f"Stability:     {report_dict.get('stability_score', 'N/A')}",
        f"MSE:           {report_dict.get('mse', 'N/A')}",
        f"Adaptation:    tick {report_dict.get('adaptation_speed_ticks', 'N/A')}",
        "",
        "PHASES:",
    ]

    phases = report_dict.get("phases", {})
    for name, tick in phases.items():
        lines.append(f"  {name}: {tick}")

    anomalies = report_dict.get("anomalies", [])
    lines.append(f"\nANOMALIES: {len(anomalies)}")
    lines.append("=" * 50)
    return "\n".join(lines)

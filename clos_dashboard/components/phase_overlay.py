"""Komponenty Dashboardu – phase overlay."""

from typing import Dict, Any


def render_phase_overlay_component(report_dict: Dict[str, Any], max_tick: int) -> str:
    """Renderuje overlay faz na wykresie.

    Args:
        report_dict: Raport Scientist.
        max_tick: Maksymalny tick.

    Returns:
        Sformatowany tekst.
    """
    phases = report_dict.get("phases", {})
    lines = ["PHASE OVERLAY", "─" * 40]

    for name, tick in phases.items():
        lines.append(f"  │ tick {tick}: {name}")

    if max_tick > 0:
        lines.append(f"  └─ Total: {max_tick} ticks")
    return "\n".join(lines)

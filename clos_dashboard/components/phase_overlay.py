"""Komponenty Dashboardu – phase overlay (ASCII)."""

from typing import Dict, Any


def render_phase_overlay_component(report_dict: Dict[str, Any], max_tick: int) -> str:
    """Renderuje overlay faz na wykresie."""
    phases = report_dict.get("phases", {})
    lines = ["PHASE OVERLAY", "-" * 40]

    for name, tick in phases.items():
        lines.append(f"  | tick {tick}: {name}")

    if max_tick > 0:
        lines.append(f"  +-- Total: {max_tick} ticks")
    return "\n".join(lines)

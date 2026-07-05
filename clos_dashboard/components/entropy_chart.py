"""Komponenty Dashboardu – wykresy (tekstowe, tylko ASCII)."""

from typing import List, Dict


def render_entropy_chart(ticks: List[int], entropy: List[float], width: int = 60, height: int = 15) -> str:
    return _render_chart(ticks, entropy, "ENTROPY", width, height)


def render_energy_chart(ticks: List[int], energy: List[float], width: int = 60, height: int = 15) -> str:
    return _render_chart(ticks, energy, "ENERGY", width, height)


def render_memory_chart(ticks: List[int], memory: List[int], width: int = 60, height: int = 15) -> str:
    return _render_chart(ticks, [float(m) for m in memory], "MEMORY SIZE", width, height)


def _render_chart(ticks: List[int], values: List[float], title: str, width: int, height: int) -> str:
    if not values:
        return f"{title}\nNo data"

    lines = [f"{title} ({len(values)} points)", "-" * width]

    if len(values) <= 1:
        lines.append("Not enough data")
        return "\n".join(lines)

    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val if max_val != min_val else 1.0

    sampled = values
    if len(values) > width:
        step = len(values) // width
        sampled = values[::step][:width]

    chart = [[" "] * width for _ in range(height)]

    for i, v in enumerate(sampled):
        if i >= width:
            break
        row = int((v - min_val) / val_range * (height - 1))
        row = max(0, min(height - 1, row))
        chart[height - 1 - row][i] = "#"

    for row in chart:
        lines.append("".join(row))

    lines.append(f"Range: [{min_val:.3f} - {max_val:.3f}]")
    return "\n".join(lines)

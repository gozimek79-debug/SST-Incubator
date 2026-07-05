"""Komponenty Dashboardu – replay slider."""

from typing import Optional
from clos_kernel.snapshot_engine import Snapshot


def render_replay_slider(snapshot: Optional[Snapshot], min_tick: int, max_tick: int) -> str:
    """Renderuje informację o aktualnym ticku.

    Args:
        snapshot: Aktualny snapshot.
        min_tick: Minimalny tick.
        max_tick: Maksymalny tick.

    Returns:
        Sformatowany tekst.
    """
    if snapshot is None:
        return "REPLAY: No snapshot loaded"

    position = (snapshot.tick - min_tick) / max(1, max_tick - min_tick)
    bar_width = 50
    pos = int(position * bar_width)

    bar = "[" + "─" * pos + "●" + "─" * (bar_width - pos - 1) + "]"

    lines = [
        f"REPLAY – Tick {snapshot.tick} / {max_tick}",
        bar,
        f"  Entropy: {snapshot.entropy:.4f}",
        f"  Energy:  {snapshot.energy:.4f}",
        f"  Status:  {snapshot.brain_status}",
    ]
    return "\n".join(lines)

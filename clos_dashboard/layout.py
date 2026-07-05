"""Layout Dashboardu – kompozycja wszystkich paneli."""

from typing import Dict, List, Any
from clos_dashboard.components.experiment_selector import render_experiment_selector, render_metadata_panel, render_phase_overlay
from clos_dashboard.components.entropy_chart import render_entropy_chart, render_energy_chart, render_memory_chart
from clos_dashboard.components.comparison_panel import render_comparison_panel, render_report_panel
from clos_dashboard.components.replay_slider import render_replay_slider
from clos_dashboard.data_adapter import adapt_snapshots_to_chart


def render_full_dashboard(
    experiments: List[Dict[str, Any]],
    selected_report: Dict[str, Any] = None,
    chart_data: Dict[str, List[float]] = None,
    replay_snapshot=None,
    replay_min_tick: int = 0,
    replay_max_tick: int = 0,
    comparison_text: str = "",
) -> str:
    """Renderuje pełny dashboard jako tekst.

    Args:
        experiments: Lista eksperymentów.
        selected_report: Wybrany raport (dict).
        chart_data: Dane wykresów.
        replay_snapshot: Aktualny snapshot replay.
        replay_min_tick: Min tick.
        replay_max_tick: Max tick.
        comparison_text: Tekst porównania.

    Returns:
        Pełny dashboard jako string.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("SST INCUBATOR CLOS v0.1 – LIVE MONITOR")
    lines.append("=" * 70)
    lines.append("")

    # Panel 1: Experiment Selector
    lines.append(render_experiment_selector(experiments))
    lines.append("")

    if selected_report:
        # Panel 2: Metadata
        lines.append(render_metadata_panel(selected_report))
        lines.append("")

        # Panel 3: Wykresy
        if chart_data:
            lines.append(render_entropy_chart(
                chart_data.get("ticks", []),
                chart_data.get("entropy", [])
            ))
            lines.append("")
            lines.append(render_energy_chart(
                chart_data.get("ticks", []),
                chart_data.get("energy", [])
            ))
            lines.append("")
            lines.append(render_memory_chart(
                chart_data.get("ticks", []),
                chart_data.get("step_counter", [])
            ))
            lines.append("")

        # Phase Overlay
        max_tick = selected_report.get("raw_summary", {}).get("last_tick", 0)
        lines.append(render_phase_overlay(selected_report, max_tick))
        lines.append("")

        # Replay
        lines.append(render_replay_slider(replay_snapshot, replay_min_tick, replay_max_tick))
        lines.append("")

    # Comparison
    if comparison_text:
        lines.append(render_comparison_panel(comparison_text))
        lines.append("")

    # Report
    if selected_report:
        lines.append(render_report_panel(selected_report))
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)

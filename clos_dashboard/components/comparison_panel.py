"""Komponenty Dashboardu – panel porównawczy i raportu."""

from typing import Dict, Any


def render_comparison_panel(comparison_text: str) -> str:
    """Renderuje wynik porównania z Registry.compare().

    Args:
        comparison_text: Tekst z Registry.compare().

    Returns:
        Sformatowany tekst.
    """
    return comparison_text


def render_report_panel(report_dict: Dict[str, Any]) -> str:
    """Renderuje panel raportu Scientist.

    Args:
        report_dict: Raport w formacie dict.

    Returns:
        Sformatowany tekst.
    """
    import json
    lines = [
        "=" * 50,
        "SCIENTIST REPORT (JSON)",
        "=" * 50,
        json.dumps(report_dict, indent=2, ensure_ascii=False),
        "=" * 50,
    ]
    return "\n".join(lines)

"""Konfiguracja Dashboardu."""

from dataclasses import dataclass

@dataclass
class DashboardConfig:
    title: str = "SST Incubator CLOS – Live Monitor v0.1"
    theme: str = "dark"
    max_ticks_display: int = 1000
    default_sampling: int = 1

DASHBOARD_CONFIG = DashboardConfig()

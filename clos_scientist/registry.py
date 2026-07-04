"""Registry – historia eksperymentów (read-only index)."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from .types import ExperimentReport


class ExperimentRegistry:
    """Rejestr eksperymentów.

    Przechowuje raporty i umożliwia porównywanie.
    """

    def __init__(self, storage_path: str = "storage/registry.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._reports: Dict[str, ExperimentReport] = {}
        self._load()

    def register_experiment(self, report: ExperimentReport) -> None:
        """Zarejestruj nowy eksperyment.

        Args:
            report: Raport z eksperymentu.
        """
        self._reports[report.run_id] = report
        self._save()

    def get_experiment(self, run_id: str) -> Optional[ExperimentReport]:
        """Pobierz raport po ID.

        Args:
            run_id: ID eksperymentu.

        Returns:
            Raport lub None.
        """
        return self._reports.get(run_id)

    def list_experiments(self) -> List[str]:
        """Lista wszystkich ID eksperymentów.

        Returns:
            Lista stringów z ID.
        """
        return list(self._reports.keys())

    def compare(self, run_a: str, run_b: str) -> str:
        """Porównaj dwa eksperymenty.

        Args:
            run_a: ID pierwszego eksperymentu.
            run_b: ID drugiego eksperymentu.

        Returns:
            Sformatowany tekst porównania.

        Raises:
            KeyError: Jeśli któryś eksperyment nie istnieje.
        """
        if run_a not in self._reports:
            raise KeyError(f"Eksperyment {run_a} nie istnieje w rejestrze.")
        if run_b not in self._reports:
            raise KeyError(f"Eksperyment {run_b} nie istnieje w rejestrze.")

        rep_a = self._reports[run_a]
        rep_b = self._reports[run_b]

        def _better(a_val, b_val, lower_is_better=True):
            if lower_is_better:
                if a_val < b_val:
                    return "A", a_val, b_val
                elif b_val < a_val:
                    return "B", b_val, a_val
                else:
                    return "=", a_val, b_val
            else:
                if a_val > b_val:
                    return "A", a_val, b_val
                elif b_val > a_val:
                    return "B", b_val, a_val
                else:
                    return "=", a_val, b_val

        stab_winner, stab_a, stab_b = _better(rep_a.stability_score, rep_b.stability_score, lower_is_better=False)
        mse_winner, mse_a, mse_b = _better(rep_a.mse, rep_b.mse, lower_is_better=True)

        lines = [
            f"COMPARISON: {run_a} vs {run_b}",
            "=" * 50,
            "",
            f"{'Metric':<25} {'Run A':>10} {'Run B':>10} {'Winner':>6}",
            "-" * 51,
            f"{'Stability Score':<25} {stab_a:>10.4f} {stab_b:>10.4f} {stab_winner:>6}",
            f"{'MSE':<25} {mse_a:>10.4f} {mse_b:>10.4f} {mse_winner:>6}",
            f"{'Entropy Volatility':<25} {rep_a.metrics.get('entropy_volatility',0):>10.4f} {rep_b.metrics.get('entropy_volatility',0):>10.4f}",
            f"{'Energy Drift':<25} {rep_a.metrics.get('energy_drift',0):>10.4f} {rep_b.metrics.get('energy_drift',0):>10.4f}",
            f"{'Memory Growth Rate':<25} {rep_a.metrics.get('memory_growth_rate',0):>10.4f} {rep_b.metrics.get('memory_growth_rate',0):>10.4f}",
            "",
            "--- PHASES ---",
            f"{'Phase':<20} {'Run A':>8} {'Run B':>8}",
            "-" * 36,
            f"{'Initial Chaos':<20} {rep_a.phases.get('initial_chaos',0):>8} {rep_b.phases.get('initial_chaos',0):>8}",
            f"{'Adaptation':<20} {rep_a.phases.get('adaptation',0):>8} {rep_b.phases.get('adaptation',0):>8}",
            f"{'Convergence':<20} {rep_a.phases.get('convergence',0):>8} {rep_b.phases.get('convergence',0):>8}",
            "",
            f"--- ANOMALIES ---",
            f"  Run A: {len(rep_a.anomalies)}",
            f"  Run B: {len(rep_b.anomalies)}",
        ]

        # Sprawdź divergence tick (pierwszy tick gdzie fazy się różnią)
        for phase_key in ["initial_chaos", "adaptation", "convergence"]:
            if rep_a.phases.get(phase_key) != rep_b.phases.get(phase_key):
                lines.append(f"  Phase divergence at '{phase_key}'")
                break

        return "\n".join(lines)

    def _save(self) -> None:
        """Zapisz rejestr do pliku JSON."""
        data = {rid: report.to_dict() for rid, report in self._reports.items()}
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load(self) -> None:
        """Wczytaj rejestr z pliku JSON."""
        if not self.storage_path.exists():
            return
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for rid, report_dict in data.items():
            report = ExperimentReport(
                run_id=report_dict["run_id"],
                metrics=report_dict.get("metrics", {}),
                phases=report_dict.get("phases", {}),
                anomalies=report_dict.get("anomalies", []),
                stability_score=report_dict.get("stability_score", 0.0),
                mse=report_dict.get("mse", 0.0),
                adaptation_speed_ticks=report_dict.get("adaptation_speed_ticks", 0),
                raw_summary=report_dict.get("raw_summary", {})
            )
            self._reports[rid] = report

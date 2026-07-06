"""Executor – uruchamia runy przez CLI subprocess."""

import subprocess
import sys
import os
from typing import Dict, Any
from clos_studio.execution.queue import ExecutionQueue


class ExperimentExecutor:
    """Wykonawca eksperymentów – deleguje do CLI."""

    def __init__(self, queue: ExecutionQueue):
        self.queue = queue
        self.results = []

    def run_all(self) -> list:
        """Wykonaj wszystkie runy w kolejce.

        Returns:
            Lista wyników (dict per run).
        """
        while not self.queue.is_complete:
            run_config = self.queue.get_next()
            run_index = self.queue.current_run - 1
            run_id = self.queue.get_run_id(run_index)

            result = self._execute_single_run(run_id, run_config)
            result["run_id"] = run_id
            result["run_config"] = run_config
            self.results.append(result)

        return self.results

    def _execute_single_run(self, run_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje pojedynczy run przez CLI.

        Args:
            run_id: ID runu.
            config: Konfiguracja (genome, scenario, seed, ticks).

        Returns:
            Wynik wykonania.
        """
        project_root = os.getcwd()

        # Używamy demo z parametrami (tymczasowo – w v0.3 dla uproszczenia)
        cmd = [
            sys.executable, "-m", "clos_cli", "demo",
            "--seed", str(config["seed"]),
            "--ticks", str(config["ticks"]),
        ]

        env = os.environ.copy()
        env["PYTHONPATH"] = project_root

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                env=env,
                timeout=300,
            )
            return {
                "status": "COMPLETE" if process.returncode == 0 else "FAILED",
                "returncode": process.returncode,
                "stdout": process.stdout[-500:] if process.stdout else "",
                "stderr": process.stderr[-200:] if process.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "returncode": -1,
                "stdout": "",
                "stderr": "Execution timeout (300s)",
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
            }

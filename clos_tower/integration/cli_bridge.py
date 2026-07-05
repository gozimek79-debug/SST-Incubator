"""CLI Bridge – uruchamia CLI przez subprocess, przechwytuje JSONL stream."""

import subprocess
import sys
import os
import json
from typing import Iterator, Dict, Any


def _get_project_root() -> str:
    """Zwraca ścieżkę do katalogu projektu."""
    return os.getcwd()


def run_demo_stream(seed: int = 42, ticks: int = 200) -> Iterator[Dict[str, Any]]:
    """Uruchom demo w trybie stream i zwracaj ticki jako słowniki."""
    project_root = _get_project_root()
    cmd = [
        sys.executable, "-m", "clos_cli", "demo",
        "--seed", str(seed),
        "--ticks", str(ticks),
        "--stream"
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = project_root

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=project_root,
        env=env
    )

    for line in process.stdout:
        line = line.strip()
        if line:
            try:
                tick_data = json.loads(line)
                yield tick_data
            except json.JSONDecodeError:
                pass

    process.wait()


def run_demo_full(seed: int = 42, ticks: int = 200) -> str:
    """Uruchom demo w trybie normalnym i zwróć pełny output."""
    project_root = _get_project_root()
    cmd = [
        sys.executable, "-m", "clos_cli", "demo",
        "--seed", str(seed),
        "--ticks", str(ticks),
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = project_root

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env
    )
    return result.stdout

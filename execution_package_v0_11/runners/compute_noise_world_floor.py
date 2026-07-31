"""PC-001 W2 (D-018): jednorazowe obliczenie floor(t) dla noise_world (Primary
Environment) produkcyjnym N=100_000 na pelnym 300-tickowym oknie L1.2, plus
wynik testu waznosci V-C. NIE wchodzi do CRITICAL_FILES_PC_001 (skrypt
raportujacy, nie kod decyzyjny - analogicznie do
execution_package_v0_11/runners/pilot_power_analysis.py).

Dotyka WYLACZNIE generatora srodowiska (clos_world.scenarios.noise_world) - zero
Brain/genomu/eksperymentu. Zgodne z Hard Halt (blokuje wylacznie pilota i
eksperyment konfirmacyjny, nie charakterystyke generatora - specyfikacja_W2
§2.1a: "sprawdzenie wykonywane na samym generatorze srodowiska, przed
eksperymentem, bez zadnych danych z mozgu").
"""

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from clos_world.scenarios import noise_world
from clos_world.floor_model import floor_profile, DEFAULT_N
from clos_scientist.w2_endpoint import select_floor_model, MEASURABLE_WINDOW_TICKS


def main():
    t0 = time.time()
    result = select_floor_model(noise_world)
    elapsed = time.time() - t0

    out = {
        "environment": "noise_world",
        "N": DEFAULT_N,
        "n_ticks": len(MEASURABLE_WINDOW_TICKS),
        "elapsed_seconds": round(elapsed, 1),
        "floor_model": result["floor_model"],
        "floor_env": result["floor_env"],
        "bias_early": result["bias_early"],
        "bias_late": result["bias_late"],
        "bias_roznicowy": result["bias_roznicowy"],
        "floor_bias_tolerance": result["floor_bias_tolerance"],
        "warning": result["warning"],
        "floor_profile_sample": (
            None if result["floor_profile"] is None else
            {t: result["floor_profile"][t] for t in [0, 30, 60, 150, 240, 270, 299]}
        ),
    }

    out_path = REPO_ROOT / "reports" / "pilot" / "floor_noise_world_2026-07-28.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Written to {out_path}")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

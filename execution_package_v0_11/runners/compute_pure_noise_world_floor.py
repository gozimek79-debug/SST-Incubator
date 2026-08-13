"""PC-001 Pilot Final, przygotowanie (PF-01/PF-02, zgloszenie audytora 2026-08-12):
jednorazowe obliczenie floor(t) dla pure_noise_world (srodowisko K4), lustro
execution_package_v0_11/runners/compute_noise_world_floor.py - ta sama funkcja
generyczna (select_floor_model), ten sam N=100_000, ten sam zakres seedow
(DEFAULT_SEED_START=500_000, clos_world/floor_model.py) - CELOWO NIEZMIENIony,
zeby podloga obu srodowisk byla wyznaczona tym samym rygorem. NIE wchodzi do
CRITICAL_FILES_PC_001 (skrypt raportujacy/jednorazowy, nie kod decyzyjny -
dokladnie ten sam scoping co compute_noise_world_floor.py, zatwierdzone CTO).

WAZNE (PF-02, decyzja CTO): floor_model dla pure_noise_world NIE jest zalozony
z gory jako "constant" (to co wyszlo dla noise_world) - select_floor_model()
nie ma parametru pozwalajacego wymusic wynik, wiec ten skrypt tylko zapisuje,
co faktycznie wyszlo z testu waznosci V-C (specyfikacja_W2 §2.1a), mechanicznie.

Dotyka WYLACZNIE generatora srodowiska (clos_world.scenarios.pure_noise_world) -
zero Brain/genomu/eksperymentu, ten sam zakres co jego odpowiednik dla
noise_world (Hard Halt: blokuje wylacznie pilota i eksperyment konfirmacyjny,
nie charakterystyke generatora).
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from clos_world.scenarios import pure_noise_world
from clos_world.floor_model import DEFAULT_N, DEFAULT_SEED_START
from clos_scientist.w2_endpoint import select_floor_model, MEASURABLE_WINDOW_TICKS


def main():
    t0 = time.time()
    result = select_floor_model(pure_noise_world)
    elapsed = time.time() - t0

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": "pure_noise_world",
        "N": DEFAULT_N,
        "seed_start": DEFAULT_SEED_START,
        "seed_range": f"{DEFAULT_SEED_START}-{DEFAULT_SEED_START + DEFAULT_N - 1}",
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

    out_path = REPO_ROOT / "reports" / "pilot" / f"floor_pure_noise_world_{datetime.now(timezone.utc).date().isoformat()}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Written to {out_path}")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""CLOS Control Center v0.8."""

import argparse, sys
from .commands import route_command

def main():
    parser = argparse.ArgumentParser(description="CLOS Control Center v0.8")
    subparsers = parser.add_subparsers(dest="command", help="Komendy")
    subparsers.add_parser("academy", help="Uruchom Cognitive Academy – Lesson L1.1")
    subparsers.add_parser("school")
    p_run = subparsers.add_parser("run"); p_run.add_argument("manifest")
    p_matrix = subparsers.add_parser("run-matrix"); p_matrix.add_argument("manifest")
    p_demo = subparsers.add_parser("demo")
    p_demo.add_argument("--seed", type=int, default=42)
    p_demo.add_argument("--ticks", type=int, default=200)
    p_demo.add_argument("--stream", action="store_true")
    p_demo.add_argument("--genome", default="default")
    p_demo.add_argument("--scenario", default="shock_world")
    p_demo.add_argument("--telemetry", type=int, default=0)
    p_comp = subparsers.add_parser("compare"); p_comp.add_argument("--seed", type=int, default=42); p_comp.add_argument("--ticks", type=int, default=300)
    p_bench = subparsers.add_parser("benchmark"); p_bench.add_argument("--seed", type=int, default=42); p_bench.add_argument("--ticks", type=int, default=200)
    p_dash = subparsers.add_parser("dashboard"); p_dash.add_argument("--seed", type=int, default=42); p_dash.add_argument("--ticks", type=int, default=100)
    args = parser.parse_args()
    if args.command is None: parser.print_help(); sys.exit(1)
    stream_mode = getattr(args, "stream", False)
    genome_val = getattr(args, "genome", "default")
    scenario_val = getattr(args, "scenario", "shock_world")
    telemetry_val = getattr(args, "telemetry", 0)
    if args.command in ("run", "run-matrix"): route_command(args.command, 0, 0, manifest=getattr(args, "manifest", ""))
    elif args.command in ("school", "academy"): route_command(args.command, 0, 0)
    else: route_command(args.command, getattr(args, "seed", 42), getattr(args, "ticks", 200), stream_mode, genome=genome_val, scenario=scenario_val, telemetry=telemetry_val)

if __name__ == "__main__": main()

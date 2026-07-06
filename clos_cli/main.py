"""CLOS Control Center – Unified Runtime Interface."""

import argparse
import sys
from .commands import route_command


def main():
    parser = argparse.ArgumentParser(
        description="CLOS Control Center – deterministyczne laboratorium poznawcze"
    )
    subparsers = parser.add_subparsers(dest="command", help="Komendy")

    # Run (Experiment Studio)
    parser_run = subparsers.add_parser("run", help="Uruchom eksperyment z manifestu")
    parser_run.add_argument("manifest", help="Ścieżka do manifestu (.yaml/.json)")

    # Run-Matrix (Research Matrix Core)
    parser_matrix = subparsers.add_parser("run-matrix", help="Uruchom macierz eksperymentów")
    parser_matrix.add_argument("manifest", help="Ścieżka do manifestu macierzy (.yaml)")

    # Verify
    parser_verify = subparsers.add_parser("verify-matrix", help="Zweryfikuj eksperyment")
    parser_verify.add_argument("experiment_id", help="ID eksperymentu")

    # Demo
    parser_demo = subparsers.add_parser("demo", help="Demonstracja")
    parser_demo.add_argument("--seed", type=int, default=42)
    parser_demo.add_argument("--ticks", type=int, default=200)
    parser_demo.add_argument("--stream", action="store_true")

    # Compare, Benchmark, Dashboard
    parser_compare = subparsers.add_parser("compare")
    parser_compare.add_argument("--seed", type=int, default=42)
    parser_compare.add_argument("--ticks", type=int, default=300)

    parser_bench = subparsers.add_parser("benchmark")
    parser_bench.add_argument("--seed", type=int, default=42)
    parser_bench.add_argument("--ticks", type=int, default=200)

    parser_dash = subparsers.add_parser("dashboard")
    parser_dash.add_argument("--seed", type=int, default=42)
    parser_dash.add_argument("--ticks", type=int, default=100)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    stream_mode = getattr(args, "stream", False)

    if args.command in ("run", "run-matrix"):
        manifest_path = getattr(args, "manifest", "")
        route_command(args.command, 0, 0, manifest=manifest_path)
    else:
        route_command(args.command, getattr(args, "seed", 42), getattr(args, "ticks", 200), stream_mode)


if __name__ == "__main__":
    main()

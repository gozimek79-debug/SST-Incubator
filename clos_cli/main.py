"""CLOS Control Center – Unified Runtime Interface v0.1.1."""

import argparse
import sys
from .commands import route_command


def main():
    parser = argparse.ArgumentParser(
        description="CLOS Control Center – deterministyczne laboratorium poznawcze"
    )
    subparsers = parser.add_subparsers(dest="command", help="Komendy")

    # Run (nowa komenda – Experiment Studio)
    parser_run = subparsers.add_parser("run", help="Uruchom eksperyment z manifestu")
    parser_run.add_argument("manifest", help="Ścieżka do pliku manifestu (.yaml lub .json)")

    # Demo
    parser_demo = subparsers.add_parser("demo", help="Uruchom demonstrację")
    parser_demo.add_argument("--seed", type=int, default=42)
    parser_demo.add_argument("--ticks", type=int, default=200)
    parser_demo.add_argument("--stream", action="store_true")

    # Compare
    parser_compare = subparsers.add_parser("compare", help="Porównaj scenariusze")
    parser_compare.add_argument("--seed", type=int, default=42)
    parser_compare.add_argument("--ticks", type=int, default=300)

    # Benchmark
    parser_bench = subparsers.add_parser("benchmark", help="Uruchom benchmark")
    parser_bench.add_argument("--seed", type=int, default=42)
    parser_bench.add_argument("--ticks", type=int, default=200)

    # Dashboard
    parser_dash = subparsers.add_parser("dashboard", help="Dashboard")
    parser_dash.add_argument("--seed", type=int, default=42)
    parser_dash.add_argument("--ticks", type=int, default=100)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    stream_mode = getattr(args, "stream", False)

    if args.command == "run":
        route_command("run", 0, 0, manifest=getattr(args, "manifest", ""))
    else:
        route_command(args.command, args.seed, args.ticks, stream_mode)


if __name__ == "__main__":
    main()

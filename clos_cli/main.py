"""CLOS Control Center – Unified Runtime Interface v0.1.1."""

import argparse
import sys
from .commands import route_command


def main():
    parser = argparse.ArgumentParser(
        description="CLOS Control Center – deterministyczne laboratorium poznawcze"
    )
    subparsers = parser.add_subparsers(dest="command", help="Komendy")

    # Demo
    parser_demo = subparsers.add_parser("demo", help="Uruchom demonstrację pojedynczego eksperymentu")
    parser_demo.add_argument("--seed", type=int, default=42, help="Ziarno losowości (domyślnie 42)")
    parser_demo.add_argument("--ticks", type=int, default=200, help="Liczba ticków (domyślnie 200)")
    parser_demo.add_argument("--stream", action="store_true", help="Emituj ticki jako JSONL na stdout")

    # Compare
    parser_compare = subparsers.add_parser("compare", help="Porównaj scenariusze STABLE vs SHOCK")
    parser_compare.add_argument("--seed", type=int, default=42, help="Ziarno losowości (domyślnie 42)")
    parser_compare.add_argument("--ticks", type=int, default=300, help="Liczba ticków (domyślnie 300)")

    # Benchmark
    parser_bench = subparsers.add_parser("benchmark", help="Uruchom pełny benchmark")
    parser_bench.add_argument("--seed", type=int, default=42, help="Ziarno losowości (domyślnie 42)")
    parser_bench.add_argument("--ticks", type=int, default=200, help="Liczba ticków na run (domyślnie 200)")

    # Dashboard
    parser_dash = subparsers.add_parser("dashboard", help="Wyświetl dashboard")
    parser_dash.add_argument("--seed", type=int, default=42, help="Ziarno losowości (domyślnie 42)")
    parser_dash.add_argument("--ticks", type=int, default=100, help="Liczba ticków dla demo (domyślnie 100)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    stream_mode = getattr(args, "stream", False)
    route_command(args.command, args.seed, args.ticks, stream_mode)


if __name__ == "__main__":
    main()

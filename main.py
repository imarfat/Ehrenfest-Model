import argparse
import random
import sys

from ehrenfest_app.ehrenfestModel import print_simulation_statistics


def run_gui():
    from ehrenfest_app.ui import EhrenfestApp
    import customtkinter as ctk

    ctk.set_appearance_mode('light')
    ctk.set_default_color_theme('dark-blue')

    root = ctk.CTk()
    root.geometry('1200x700')
    EhrenfestApp(root)
    root.protocol('WM_DELETE_WINDOW', root.quit)
    root.mainloop()


def run_stats(args):
    rng = random.Random(args.seed) if args.seed is not None else None
    try:
        print_simulation_statistics(
            N=args.N,
            M=args.M,
            initial=args.initial,
            rng=rng,
        )
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Ehrenfest model simulation (GUI or batch statistics).',
    )
    subparsers = parser.add_subparsers(dest='command')

    stats_parser = subparsers.add_parser(
        'stats',
        help='Run M iterations for N balls and print summary statistics.',
    )
    stats_parser.add_argument('N', type=int, help='Number of balls.')
    stats_parser.add_argument('M', type=int, help='Number of iterations.')
    stats_parser.add_argument(
        '--initial',
        type=int,
        default=None,
        help='Initial number of balls in box A (default: random).',
    )
    stats_parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducible runs.',
    )
    stats_parser.set_defaults(func=run_stats)

    args = parser.parse_args()
    if args.command is None:
        run_gui()
    else:
        args.func(args)


if __name__ == '__main__':
    main()

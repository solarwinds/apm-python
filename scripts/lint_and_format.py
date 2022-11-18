#!/usr/bin/env python3
import argparse
import subprocess
import sys


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Lint and format everything, autofixing if possible.")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--allowexitcodes", action="append", default=[0])
    parser.set_defaults(parser=parser)
    parser.set_defaults(func=lint_and_format)
    return parser.parse_args(args)


def lint_and_format(args):
    black_args = ("black", "--config", "pyproject.toml", "solarwinds_apm")
    if args.check_only:
        black_args += ("--diff", "--check")
    black_result = subprocess.run(black_args)
    if black_result is not None and black_result.returncode not in args.allowexitcodes:
        print(
            "'{}' failed with code {}".format("black", black_result.returncode),
            file=sys.stderr,
        )
        sys.exit(black_result.returncode)

    isort_args = ("isort", "--settings-path", ".isort.cfg", "solarwinds_apm")
    if args.check_only:
        isort_args += ("--diff", "--check")
    isort_result = subprocess.run(isort_args)
    if isort_result is not None and isort_result.returncode not in args.allowexitcodes:
        print(
            "'{}' failed with code {}".format("isort", isort_result.returncode),
            file=sys.stderr,
        )
        sys.exit(isort_result.returncode)

    flake_result = subprocess.run(("flake8", "--config", ".flake8", "solarwinds_apm"))
    if flake_result is not None and flake_result.returncode not in args.allowexitcodes:
        print(
            "'{}' failed with code {}".format("flake8", flake_result.returncode),
            file=sys.stderr,
        )
        sys.exit(flake_result.returncode)

    pylint_result = subprocess.run(("pylint", "--ignore", "solarwinds_apm/extension", "solarwinds_apm"))
    if pylint_result is not None and pylint_result.returncode not in args.allowexitcodes:
        print(
            "'{}' failed with code {}".format("pylint", pylint_result.returncode),
            file=sys.stderr,
        )
        sys.exit(pylint_result.returncode)

    print("Done.")


def main():
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

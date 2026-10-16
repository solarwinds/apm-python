#!/usr/bin/env python3

# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

import argparse
import subprocess
import sys


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Lint and format everything, autofixing if possible."
    )
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--allowexitcodes", action="append", default=[0])
    parser.set_defaults(parser=parser)
    parser.set_defaults(func=lint_and_format)
    return parser.parse_args(args)


def run_subprocess(args, allowexitcodes):
    """Helper to run process and sys exit if error"""
    result = subprocess.run(args)
    if result is not None and result.returncode not in allowexitcodes:
        print(
            f"'{args[0]}' failed with code {result.returncode}",
            file=sys.stderr,
        )
        sys.exit(result.returncode)


def lint_and_format(args):
    black_args = ("black", "--config", "pyproject.toml", "solarwinds_apm")
    if args.check_only:
        black_args += ("--diff", "--check")
    run_subprocess(black_args, args.allowexitcodes)

    isort_args = ("isort", "--settings-path", ".isort.cfg", "solarwinds_apm")
    if args.check_only:
        isort_args += ("--diff", "--check")
    run_subprocess(isort_args, args.allowexitcodes)

    run_subprocess(
        ("flake8", "--config", ".flake8", "solarwinds_apm"),
        args.allowexitcodes,
    )

    run_subprocess(
        ("pylint", "solarwinds_apm"),
        args.allowexitcodes,
    )

    print("Done.")


def main():
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

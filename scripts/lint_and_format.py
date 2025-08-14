#!/usr/bin/env python3

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

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
            "'{}' failed with code {}".format(args[0], result.returncode),
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

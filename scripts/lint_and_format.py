#!/usr/bin/env python3
import argparse

def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Lint and format everything, autofixing if possible.")
    parser.add_argument("--check-only", action="store_true")
    parser.set_defaults(parser=parser)
    parser.set_defaults(func=lint_and_format)
    return parser.parse_args(args)

def lint_and_format(args):
    # TODO call black subprocess

    # TODO call isort subprocess

    # TODO call flake8 subprocess

    # TODO call pylint subprocess

    print("Done lint_and_format.")
    return


def main():
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

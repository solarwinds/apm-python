#!/usr/bin/env python3

# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from pathlib import Path

EXPECTED_LINES = (
    "# Copyright SolarWinds Worldwide, LLC.\n",
    "# SPDX-License-Identifier: Apache-2.0\n",
)
EXPECTED_LINES_OTEL = (
    "# Copyright The OpenTelemetry Authors\n",
    "# SPDX-License-Identifier: Apache-2.0\n",
)
EXPECTED_LINES_MD = (
    "<!-- Copyright SolarWinds Worldwide, LLC. -->\n",
    "<!-- SPDX-License-Identifier: Apache-2.0 -->\n",
)

SKIP_SUFFIXES = (
    ".json",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "version.py",
)

SKIP_DIRS = (
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "dist",
    "venv",
)


def should_skip(relpath: str) -> bool:
    """Return whether a repository-relative path matches an exclusion.

    Args:
        relpath: Path relative to the repository root, using OS separators.

    Returns:
        True if a directory component is in SKIP_DIRS or the basename ends
        with a suffix in SKIP_SUFFIXES; otherwise False.
    """
    parts = relpath.split(os.sep)
    if any(d in parts for d in SKIP_DIRS):
        return True
    basename = os.path.basename(relpath)
    return any(basename.endswith(s) for s in SKIP_SUFFIXES)


def check_file(path: str | Path) -> bool:
    """Check for the exact two-line license header at the start of a file.

    Markdown uses HTML comments; other files use hash comments. A leading
    shebang and one following blank line are allowed before the header.
    Hash-comment headers may name SolarWinds Worldwide, LLC. or The
    OpenTelemetry Authors; both require the Apache-2.0 SPDX identifier.

    Args:
        path: File to read, as a path string or pathlib.Path.

    Returns:
        True if the header matches or the file is empty or whitespace-only;
        otherwise False.

    Raises:
        OSError: If the file cannot be opened or read.
        UnicodeError: If the file cannot be decoded using the default encoding.
    """
    with open(path) as f:
        lines = f.readlines()

    # Skip empty files (e.g. namespace __init__.py)
    if not lines or all(line.strip() == "" for line in lines):
        return True

    # If file starts with a shebang, check lines after it
    start = 0
    if lines[0].startswith("#!"):
        start = 1
        # Skip optional blank line after shebang
        if start < len(lines) and lines[start].strip() == "":
            start += 1

    if len(lines) < start + 2:
        return False

    expected_headers = (
        (EXPECTED_LINES_MD,)
        if Path(path).suffix == ".md"
        else (EXPECTED_LINES, EXPECTED_LINES_OTEL)
    )
    return tuple(lines[start : start + 2]) in expected_headers


def main() -> None:
    """Check selected repository files and print the license-header results.

    Check Python, Markdown, shell, and PowerShell files, Dockerfile variants,
    Docker Compose YAML, and GitHub Actions YAML. Skip configured exclusions,
    virtual environments marked by pyvenv.cfg, and hidden directories other
    than .github and .claude.

    Raises:
        SystemExit: With status 1 if any checked file has a missing or invalid
            license header.
    """
    root = str(Path(__file__).resolve().parents[1])
    failures = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip any arbitrarily-named Python virtual environment
        if "pyvenv.cfg" in filenames:
            dirnames[:] = []
            continue

        dirnames[:] = [
            d
            for d in dirnames
            if not d.startswith(".") or d in (".github", ".claude")
        ]

        for filename in filenames:
            path = os.path.join(dirpath, filename)
            relpath = os.path.relpath(path, root)
            is_selected_yaml = filename.endswith((".yml", ".yaml")) and (
                filename.startswith("docker-compose")
                or Path(relpath).parts[:2]
                in (
                    (".github", "workflows"),
                    (".github", "actions"),
                )
            )
            if not (
                filename.endswith((".py", ".md", ".sh", ".ps1"))
                or filename.startswith("Dockerfile")
                or is_selected_yaml
            ):
                continue
            if should_skip(relpath):
                continue
            if not check_file(path):
                failures.append(relpath)

    if failures:
        print("Files missing the SPDX license header:")
        print()
        print("  Expected first two lines for non-Markdown files:")
        for line in EXPECTED_LINES:
            print(f"    {line.rstrip()}")
        print("  Or:")
        for line in EXPECTED_LINES_OTEL:
            print(f"    {line.rstrip()}")
        print()
        print("  Expected first two lines for Markdown:")
        for line in EXPECTED_LINES_MD:
            print(f"    {line.rstrip()}")
        print()
        for f in sorted(failures):
            print(f"  {f}")
        sys.exit(1)

    print("All files have the correct license header.")


if __name__ == "__main__":
    main()

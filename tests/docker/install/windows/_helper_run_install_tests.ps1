# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

# Helper script to set up dependencies for the install tests on windows-latest runner, then runs the tests.

# Stop on error
$ErrorActionPreference = "Stop"

# Python version was installed by calling GH workflow
Write-Host "Installing test dependencies for Python $env:PYTHON_VERSION on Windows"

# Setup dependencies quietly
# Install required tools via pip
python -m pip install --upgrade pip | Out-Null

# Run tests using PowerShell
$env:PYTHONPATH = $env:APM_ROOT
& pwsh -NoProfile -NonInteractive -Command ".\install_tests.ps1 2>&1" 
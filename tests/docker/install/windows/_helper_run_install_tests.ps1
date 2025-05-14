# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

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
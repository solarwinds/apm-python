# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

$ErrorActionPreference = "Stop"

$TEST_MODES = @("local", "testpypi", "pypi")

if (-not $env:MODE) {
    Write-Host "WARNING: Did not provide MODE for check_sdist test."
    Write-Host "Defaulting to MODE=local"
    $env:MODE = "local"
}
if ($TEST_MODES -notcontains $env:MODE) {
    Write-Error "FAILED: Did not provide valid MODE for check_sdist test. Must be one of: testpypi (default), local, pypi."
    exit 1
}

if (-not $env:APM_ROOT) {
    Write-Error "FAILED: Did not provide valid APM_ROOT for check_sdist test."
    exit 1
}

function Get-Sdist {
    if ($env:MODE -eq "local") {
        # optionally test a previous version on local for debugging
        if (-not $env:SOLARWINDS_APM_VERSION) {
            # no SOLARWINDS_APM_VERSION provided, thus test version of current source code
            $version_file = Join-Path $env:APM_ROOT "solarwinds_apm\version.py"
            $version_content = Get-Content $version_file
            if ($version_content -match '__version__ = "(.*)"') {
                if ($matches -and $matches.Count -gt 1) {
                    $env:SOLARWINDS_APM_VERSION = $matches[1]
                }
                else {
                    Write-Error "FAILED: Version regex matched but did not capture expected group. Matches: $matches"
                    exit 1
                }
            }
            else {
                Write-Error "FAILED: Could not extract version from $version_file. File content: $version_content"
                exit 1
            }
            Write-Host "No SOLARWINDS_APM_VERSION provided, thus testing source code version ($env:SOLARWINDS_APM_VERSION)"
        }

        $sdist_tar = Join-Path $env:APM_ROOT "dist\solarwinds_apm-$env:SOLARWINDS_APM_VERSION.tar.gz"
        if (-not (Test-Path $sdist_tar)) {
            Write-Error "FAILED: Did not find sdist for version $env:SOLARWINDS_APM_VERSION. Please run 'python build' before running tests."
            exit 1
        }

        return $sdist_tar
    }
    else {
        $sdist_dir = Join-Path $PWD "tmp\sdist"
        if (Test-Path $sdist_dir) { Remove-Item -Recurse -Force $sdist_dir }
        New-Item -ItemType Directory -Force -Path $sdist_dir | Out-Null

        $pip_cmd = "pip download --no-binary solarwinds-apm --dest `"$sdist_dir`""
        if ($env:MODE -eq "testpypi") {
            $pip_cmd += " --extra-index-url https://test.pypi.org/simple/"
        }

        if ($env:SOLARWINDS_APM_VERSION) {
            $pip_cmd += " solarwinds-apm==$env:SOLARWINDS_APM_VERSION"
        }
        else {
            $pip_cmd += " solarwinds-apm"
        }

        Invoke-Expression $pip_cmd | Out-Null
        $sdist_tar = Get-ChildItem -Path $sdist_dir -Filter "solarwinds_apm-*.tar.gz" | Select-Object -First 1
        return $sdist_tar.FullName
    }
}

function Check-Sdist {
    param($sdist_path)
    
    if (-not $env:PIP_INSTALL) {
        Write-Host "PIP_INSTALL not specified."
        Write-Host "Source distribution verified successfully.`n"
        exit 0
    }
    else {
        Write-Host "Installing Python agent from source"
        pip install -I $sdist_path
    }
}

# start testing
Write-Host "#### Verifying Python agent source distribution ####"
$sdist_path = Get-Sdist
Check-Sdist $sdist_path
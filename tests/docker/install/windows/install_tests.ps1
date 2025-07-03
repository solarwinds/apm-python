# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# Stop on error
$ErrorActionPreference = "Stop"

# Test modes
$TEST_MODES = @("local", "testpypi", "pypi")

if (-not $env:MODE) {
    Write-Host "WARNING: Did not provide MODE for install test run."
    Write-Host "Defaulting to MODE=local"
    $env:MODE = "local"
}
if ($TEST_MODES -notcontains $env:MODE) {
    Write-Error "FAILED: Did not provide valid MODE. Must be one of: testpypi (default), local, pypi."
    exit 1
}
else {
    Write-Host "Using provided MODE=$($env:MODE)"
}

Write-Host "Python system information"
Write-Host "Python version: $(python --version)"
Write-Host "Pip version: $(pip --version)"


function Check-AgentStartup {
    # verify that installed agent starts up properly
    Write-Host "---- Verifying proper startup of installed agent ----"

    $env:SW_APM_DEBUG_LEVEL = "6"
    $env:SW_APM_SERVICE_KEY = "invalid-token-for-testing-1234567890:servicename"
    $env:SW_APM_COLLECTOR = "apm.collector.na-01.cloud.solarwinds.com"
  
    # return value we expect form solarwinds_apm.api.solarwinds_ready().
    # This should normally be True (ready), because the collector does not send
    # "invalid api token" response; it sends "ok" with soft disable settings.
    $expectedAgentReturn = "True"

    $TEST_EXP_LOG_MESSAGES = @(
        "SolarWinds APM Python $env:SOLARWINDS_APM_VERSION",
        "retrieving sampling settings from https://apm.collector.na-01.cloud.solarwinds.com/v1/settings/servicename/$env:COMPUTERNAME"
    )

    # unset stop on error so we can catch debug messages in case of failures
    $ErrorActionPreference = "Continue"

    $startupLog = Join-Path $PWD "startup.log"

    # Write Python code to temp file to avoid string escape issues and Python SyntaxError
    $tempScript = Join-Path $PWD "temp_startup_check.py"
    @"
from solarwinds_apm.api import solarwinds_ready
r = solarwinds_ready(wait_milliseconds=10000)
print(r)
"@ | Set-Content -Path $tempScript
    try {
        $result = & opentelemetry-instrument python $tempScript 2> $startupLog | Select-Object -Last 1
    }
    finally {
        # Clean up temp file
        Remove-Item -Path $tempScript -ErrorAction SilentlyContinue
    }

    if ($result -ne $expectedAgentReturn) {
        Write-Host "FAILED! Expected solarwinds_ready to return $expectedAgentReturn, but got: $result"
        Write-Host "-- startup.log content --"
        Get-Content $startupLog
        exit 1
    }

    $logsOk = $true
    $logContent = Get-Content $startupLog -Raw
    foreach ($expected in $TEST_EXP_LOG_MESSAGES) {
        if ($logContent -notmatch [regex]::Escape($expected)) {
            $logsOk = $false
            break
        }
    }
    if (-not $logsOk) {
        Write-Host "FAILED! Expected messages were not found in startup.log"
        Write-Host "-- startup.log content --"
        Get-Content $startupLog
        exit 1
    }

    # Restore stop on error
    $ErrorActionPreference = "Stop"

    Write-Host "Agent startup verified successfully.`n"
}


function Install-TestAppDependencies {
    pip install flask requests psutil
    opentelemetry-bootstrap --action=install
}


function Run-InstrumentedServerAndClient {
    param(
        [string]$Port,
        [string]$ServiceKey,
        [string]$Collector,
        [string]$Environment
    )

    Write-Host "OS: Windows $(Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object -ExpandProperty Caption)"
    Write-Host "Python version: $(python --version)"
    Write-Host "Pip version: $(pip --version)"
    Write-Host "Instrumenting Flask with solarwinds_apm Python from $($env:MODE)."

    # Set environment variables
    $flaskEnv = @{
        "FLASK_APP" = (Resolve-Path "..\app.py").Path
        "FLASK_RUN_HOST" = "0.0.0.0"
        "FLASK_RUN_PORT" = $Port
        "OTEL_PYTHON_DISABLED_INSTRUMENTATIONS" = "urllib3"
        "SW_APM_DEBUG_LEVEL" = "3"
        "SW_APM_SERVICE_KEY" = $ServiceKey
        "SW_APM_COLLECTOR" = $Collector
    }

    Write-Host "Testing trace export from Flask to $Environment..."

    try {
        # Start Flask server in background with environment variables in job context
        $serverJob = Start-Job -ScriptBlock {
            param($env)
            foreach ($key in $env.Keys) {
                [Environment]::SetEnvironmentVariable($key, $env[$key])
            }
            & opentelemetry-instrument flask run 2>&1 | Tee-Object -FilePath "flask.log"
        } -ArgumentList $flaskEnv

        # Wait a moment for Flask to start
        Start-Sleep -Seconds 2

        # Run client with same environment variables
        foreach ($key in $flaskEnv.Keys) {
            [Environment]::SetEnvironmentVariable($key, $flaskEnv[$key])
        }
        # Except this one to reach local server in serverJob
        [Environment]::SetEnvironmentVariable("FLASK_RUN_HOST", "127.0.0.1")
        python ..\client.py

    }
    finally {
        if ($serverJob) {
            Write-Host "Stopping and removing current Flask serverJob - this may take a moment"
            Stop-Job -Job $serverJob
            Remove-Job -Job $serverJob -Force
        }
    }
}

# START TESTING ===========================================
if (-not $env:APM_ROOT) {
    $env:APM_ROOT = "/code/python-solarwinds"
    Write-Host "Using default APM_ROOT: $env:APM_ROOT"
}
else {
    Write-Host "Using configured APM_ROOT: $env:APM_ROOT"
}

if ($env:MODE -eq "local") {
    Write-Host "Local mode: installing sdist and wheel locally"
    pip install build
    python -m build $env:APM_ROOT --sdist
    pip -v wheel $env:APM_ROOT -w $env:APM_ROOT\dist --no-deps
}

# Check sdist
$env:PIP_INSTALL = 1
. .\_helper_check_sdist.ps1
Check-AgentStartup
Write-Host "Source distribution verified successfully.`n"

# Check wheel
$env:PIP_INSTALL = 1
. .\_helper_check_wheel.ps1
Check-AgentStartup
Write-Host "Wheel distribution verified successfully.`n"

# Check startup and instrumentation
Install-TestAppDependencies
Run-InstrumentedServerAndClient `
    -Port "8001" `
    -ServiceKey "$env:SW_APM_SERVICE_KEY_STAGING-$env:COMPUTERNAME" `
    -Collector $env:SW_APM_COLLECTOR_STAGING `
    -Environment "NH Staging"
Run-InstrumentedServerAndClient `
    -Port "8002" `
    -ServiceKey "$env:SW_APM_SERVICE_KEY_PROD-$env:COMPUTERNAME" `
    -Collector $env:SW_APM_COLLECTOR_PROD `
    -Environment "NH Prod"

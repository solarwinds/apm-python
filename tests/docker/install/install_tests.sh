#!/usr/bin/env bash

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# stop on error
set -e

# get test mode
TEST_MODES=(
    "local"
    "testpypi"
    "packagecloud"
    "pypi"
)
if [ -z "$MODE" ]
then
  echo "WARNING: Did not provide MODE for install test run."
  echo "Defaulting to MODE=local"
  MODE=local
fi
if [[ ! " ${TEST_MODES[*]} " =~ ${MODE} ]]
then
  echo "FAILED: Did not provide valid MODE. Must be one of: testpypi (default), local, packagecloud, pypi."
  exit 1
else
  echo "Using provided MODE=$MODE"
fi

echo "Python system information"
echo "Python version: $(python --version 2>&1)"
echo "Pip version: $(pip --version)"


function check_installation(){
    echo "---- Verifying agent installation ----"

    EXPECTED_SWIG_FILES_INST="./VERSION
./__init__.py
./_oboe.*.so
./bson
./bson/bson.h
./bson/platform_hacks.h
./liboboe.so
./oboe.py"

    # agent has been installed already, we only need to find the installed location
    install_location=$(pip show solarwinds-apm | grep -Eio "location: .*" | cut -d ':' -f 2)
    # pushd is stubborn and complains about double quotes
    # https://inst.eecs.berkeley.edu/html/acl/doc/cl/pages/other/tpl-commands/pushd.htm
    # shellcheck disable=SC2086
    pushd ${install_location}/solarwinds_apm/extension >/dev/null
    found_swig_files_inst=$(find . -not -path '.' -a -not -name '*.pyc' -a -not -name '__pycache__' | LC_ALL=C sort)


    # in Python3.7, 3.8, 3.9 with https://bugs.python.org/issue21536, C-extensions are not linked 
    # to libpython anymore, this leads to ldd not finding the symbols defined libpython3.(7|8|9).so
    sad_pythons=(
        3.7
        3.8
        3.9
    )
    if [[ -f /etc/os-release && ! "$(cat /etc/os-release)" =~ "Alpine" || " ${sad_pythons[*]} " =~ $(python -V 2>&1) ]]; then
        found_oboe_ldd=$(ldd ./_oboe*.so)
    fi
    popd >/dev/null

    if [[ ! "$found_swig_files_inst" =~ $EXPECTED_SWIG_FILES_INST ]]; then
        echo "FAILED! Expected these files under the installed extension directory:"
        echo "$EXPECTED_SWIG_FILES_INST"
        echo "found:"
        echo "$found_swig_files_inst"
        exit 1
    fi

    if [[ "$found_oboe_ldd" =~ 'not found' ]]; then
        echo "FAILED! Expected ldd to find all _oboe.so dependencies, but got:"
        echo "$found_oboe_ldd"
        exit 1
    fi

    if [ "$MODE" == "local" ]
    then
        # verify that version of C-extension of installed agent is same as what we expect (i.e. as determined by VERSION)
        expected_oboe_version=$(cat "$APM_ROOT"/solarwinds_apm/extension/VERSION)
        export SW_APM_SERVICE_KEY=invalid-token-for-testing-1234567890:servicename
        result=$(python -c "from solarwinds_apm.extension.oboe import Config as l_config; r=l_config.getVersionString(); print(r)")

        if [ "$result"  != "$expected_oboe_version" ]; then
            echo "FAILED! Expected agent using Oboe extension version $expected_oboe_version but found version $result."
            exit 1
        fi
        echo -e "Agent is bundled with Oboe extension version $result.\n"
    fi

    echo -e "Agent installed under $install_location verified successfully.\n"
}

function check_agent_startup(){
    # verify that installed agent starts up properly
    echo "---- Verifying proper startup of installed agent ----"

    export SW_APM_DEBUG_LEVEL=6
    export SW_APM_SERVICE_KEY=invalid-token-for-testing-1234567890:servicename
    
    # return value we expect form solarwinds_apm.api.solarwinds_ready().
    # This should normally be 1 (ready), because the collector does not send
    # "invalid api token" response; it sends "ok" with soft disable settings.
    expected_agent_return=1

    TEST_EXP_LOG_MESSAGES=(
    ">> SSL Reporter using host='apm.collector.cloud.solarwinds.com' port='443' log='' clientid='inva...7890:servicename' buf=1000 maxTransactions='200' flushMaxWaitTime='5000' eventsFlushInterval='2' maxRequestSizeBytes='3000000' proxy=''"
    "Warning: There is an problem getting the API token authorized. Metrics and tracing for this agent are currently disabled. If you'd like to learn more about resolving this issue, please contact support (see https://support.solarwinds.com/working-with-support)."
    )

    # unset stop on error so we can catch debug messages in case of failures
    set +e

    result=$(opentelemetry-instrument python -c 'from solarwinds_apm.api import solarwinds_ready; r=solarwinds_ready(wait_milliseconds=10000, integer_response=True); print(r)' 2>startup.log)

    if [ "$result" != "$expected_agent_return" ]; then
        echo "FAILED! Expected solarwinds_ready to return $expected_agent_return, but got: $result"
        echo "-- startup.log content --"
        cat startup.log
        exit 1
    fi

    logs_ok=true
    for expected in "${TEST_EXP_LOG_MESSAGES[@]}"; do
        grep -F "$expected" startup.log || logs_ok=false
    done
    if [ $logs_ok == false ]; then
        echo "FAILED! Expected messages were not found in startup.log"
        echo "-- startup.log content --"
        cat startup.log
        exit 1
    fi

    # Restore stop on error
    set -e

    echo -e "Agent startup verified successfully.\n"
}

function install_test_app_dependencies(){
    pip install flask requests
    opentelemetry-bootstrap --action=install
}

function run_instrumented_server_and_client(){
    pretty_name=$(grep PRETTY_NAME /etc/os-release | sed 's/PRETTY_NAME="//' | sed 's/"//')
    echo "Distro: $pretty_name"
    echo "Python version: $(python --version 2>&1)"
    echo "Pip version: $(pip --version)"
    echo "Instrumenting Flask with solarwinds_apm Python from $MODE."

    export FLASK_RUN_HOST="0.0.0.0"
    export FLASK_RUN_PORT="$1"
    export OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="urllib3"
    export SW_APM_DEBUG_LEVEL="3"
    export SW_APM_SERVICE_KEY="$2"
    export SW_APM_COLLECTOR="$3"
    # Only set certificate trustedpath for AO prod
    if [ "$4" = "AO Prod" ]; then
        export SW_APM_TRUSTEDPATH="$PWD/ao_issuer_ca_public_cert.crt"
    fi
    echo "Testing trace export from Flask to $4..."
    nohup opentelemetry-instrument flask run > log.txt 2>&1 &
    python client.py
}


# START TESTING ===========================================
HOSTNAME=$(cat /etc/hostname)
# docker-compose-set root of local solarwinds_apm package
APM_ROOT='/code/python-solarwinds'

# Check sdist
# shellcheck disable=SC1091
PIP_INSTALL=1 source ./_helper_check_sdist.sh
check_installation
check_agent_startup
echo -e "Source distribution verified successfully.\n"

# Check wheel
# shellcheck disable=SC1091
PIP_INSTALL=1 source ./_helper_check_wheel.sh
check_installation
check_agent_startup

# Check startup and instrumentation
install_test_app_dependencies
run_instrumented_server_and_client "8001" "$SW_APM_SERVICE_KEY_STAGING-$HOSTNAME" "$SW_APM_COLLECTOR_STAGING" "NH Staging"
run_instrumented_server_and_client "8002" "$SW_APM_SERVICE_KEY_PROD-$HOSTNAME" "$SW_APM_COLLECTOR_PROD" "NH Prod"
run_instrumented_server_and_client "8003" "$SW_APM_SERVICE_KEY_AO_PROD-$HOSTNAME" "$SW_APM_COLLECTOR_AO_PROD" "AO Prod"
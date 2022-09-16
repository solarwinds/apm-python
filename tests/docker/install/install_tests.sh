#!/usr/bin/env bash

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

function check_extension_files(){
    # Verifies content in the extension directory solarwinds_apm/extension. The absolute path of the directory to be verified
    # needs to be passed in as the first argument of this function. As the second argument, a string containing the
    # files expected under solarwinds_apm/extension needs to be provided.
    echo "---- Check content of extension directory located at $1 ----"
    if [ -z "$2" ]; then
        echo "Failed! Files expected in the extension directory not provided."
        exit 1
    fi

    expected_files="$2"

    pushd "$1" >/dev/null
    found_swig_files=$(find . -not -path '.' | LC_ALL=C sort)
    popd >/dev/null

    if [[ ! "$found_swig_files" =~ $expected_files ]]; then
        echo "FAILED! expected these files under the extension directory:"
        echo "$expected_files"
        echo "found:"
        echo "$found_swig_files"
        exit 1
    fi

    echo -e "Content of extension directory checked successfully.\n"
}

function check_installation(){
    echo "---- Verifying agent installation ----"

    EXPECTED_SWIG_FILES_INST="./VERSION
./__init__.py
./_oboe.*.so
./bson
./bson/bson.h
./bson/platform_hacks.h
./liboboe-1.0.so.0
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
        expected_oboe_version=$(cat "$agent_root"/solarwinds_apm/extension/VERSION)
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
    
    TEST_EXP_LOG_MESSAGES=(
    "Set ApmConfig as"
    "Setting trace with BatchSpanProcessor using solarwinds_exporter"
    "Setting CompositePropagator with"
    )

    # unset stop on error so we can catch debug messages in case of failures
    set +e

    result=$(opentelemetry-instrument python -c 'from solarwinds_apm import version; print(version.__version__)' 2>startup.log)

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

    # TODO: Use solarwinds_ready() to check collector connection instead of above

    echo -e "Agent startup verified successfully.\n"
}

function get_sdist(){
    sdist_dir="$PWD/tmp/sdist"
    rm -rf sdist_dir

    if [ "$MODE" == "local" ]
    then
        # docker-compose-set root of local solarwinds_apm package
        agent_root='/code/python-solarwinds'
        # optionally test a previous version on local for debugging
        if [ -z "$SOLARWINDS_APM_VERSION" ]; then
            # no SOLARWINDS_APM_VERSION provided, thus test version of current source code
            version_file=$agent_root/solarwinds_apm/version.py
            AGENT_VERSION="$(sed -n 's/__version__ = "\(.*\)"/\1/p' $version_file)"
            echo "No SOLARWINDS_APM_VERSION provided, thus testing source code version ($AGENT_VERSION)"
        fi

        sdist_tar=$agent_root/dist/solarwinds_apm-${AGENT_VERSION}.tar.gz
        if [ ! -f "$sdist_tar" ]; then
            echo "FAILED: Did not find sdist for version $AGENT_VERSION. Please run 'make package' before running tests."
            echo "Aborting tests."
            exit 1
        fi
    else
        pip_options=(--no-binary solarwinds-apm --dest "$sdist_dir")
        if [ "$MODE" == "testpypi" ]
        then
            pip_options+=(--extra-index-url https://test.pypi.org/simple/)
        elif [ "$MODE" == "packagecloud" ]
        then
            curl -s https://packagecloud.io/install/repositories/solarwinds/solarwinds-apm-python/script.python.sh | bash
        fi

        if [ -z "$AGENT_VERSION" ]
        then
            pip_options+=(solarwinds-apm)
        else
            pip_options+=(solarwinds-apm=="$AGENT_VERSION")
        fi

        # shellcheck disable=SC2048
        # shellcheck disable=SC2086
        pip download ${pip_options[*]}
        sdist_tar=$(find "$sdist_dir"/* -name "solarwinds_apm-*.tar.gz")
    fi
}

function check_sdist(){
    unpack_directory="$PWD/unpack/sdist"
    rm -rf "$unpack_directory"
    mkdir -p "$unpack_directory"
    expected_files="./VERSION
./__init__.py
./bson
./bson/bson.h
./bson/platform_hacks.h
./liboboe-1.0-alpine-x86_64.so.0.0.0
./liboboe-1.0-lambda-x86_64.so.0.0.0
./liboboe-1.0-x86_64.so.0.0.0
./oboe.h
./oboe.py
./oboe_api.cpp
./oboe_api.hpp
./oboe_debug.h
./oboe_wrap.cxx"
    tar xzf "$1" --directory "$unpack_directory"
    unpack_agent=$(find "$unpack_directory"/* -type d -name "solarwinds_apm-*")
    check_extension_files "$unpack_agent/solarwinds_apm/extension" "$expected_files"
    echo "Installing Python agent from source"
    pip install -I "$1"
    check_installation
    check_agent_startup
    echo -e "Source distribution verified successfully.\n"
}

function get_and_check_sdist(){
    echo "#### Verifying Python agent source distribution ####"
    get_sdist
    check_sdist "$sdist_tar"
}

function get_wheel(){
    wheel_dir="$PWD/tmp/wheel"
    rm -rf "$wheel_dir"
    if [ "$MODE" == "local" ]
    then
        # we need to select the right wheel (there might be multiple wheel versions in the dist directory)
        pip download \
            --only-binary solarwinds_apm \
            --find-links "$agent_root"/dist \
            --no-index \
            --dest "$wheel_dir" \
            --no-deps \
            solarwinds_apm=="$AGENT_VERSION"
        tested_wheel=$(find "$wheel_dir"/* -name "solarwinds_apm-$AGENT_VERSION*.*.whl")
        if [ ! -f "$tested_wheel" ]; then
            echo "FAILED: Did not find wheel for version $AGENT_VERSION. Please run 'make package' before running tests."
            echo "Aborting tests."
            exit 1
        fi

    else
        pip_options=(--only-binary solarwinds-apm --dest "$wheel_dir")
        if [ "$MODE" == "testpypi" ]
        then
            pip_options+=(--extra-index-url https://test.pypi.org/simple/)
        elif [ "$MODE" == "packagecloud" ]
        then
            curl -s https://packagecloud.io/install/repositories/solarwinds/solarwinds-apm-python/script.python.sh | bash
        fi

        if [ -z "$AGENT_VERSION" ]
        then
            pip_options+=(solarwinds-apm)
        else
            pip_options+=(solarwinds-apm=="$AGENT_VERSION")
        fi

        # shellcheck disable=SC2048
        # shellcheck disable=SC2086
        pip download ${pip_options[*]}
        tested_wheel=$(find "$wheel_dir"/* -name "solarwinds_apm-*.*.whl")
    fi
}

function check_wheel(){
    unpack_directory="$PWD/unpack/wheel"
    rm -rf "$unpack_directory"
    mkdir -p "$unpack_directory"
    expected_files="./VERSION
./__init__.py
./_oboe.*.so
./bson
./bson/bson.h
./bson/platform_hacks.h
./liboboe-1.0.so.0
./oboe.py"
    unzip "$tested_wheel" -d "$unpack_directory"
    check_extension_files "$unpack_directory/solarwinds_apm/extension" "$expected_files"
    echo "Installing Python agent from wheel"
    pip install -I "$tested_wheel"
    check_installation
    check_agent_startup
    echo -e "Python wheel verified successfully.\n"
}

function get_and_check_wheel(){
    echo "#### Verifying Python agent wheel distribution ####"
    # Python wheels are not available under Alpine Linux
    if [[ -f /etc/os-release && "$(cat /etc/os-release)" =~ "Alpine" ]]; then
        echo "Wheels are not available on Alpine Linux, skip wheel tests."
    else
        get_wheel
        check_wheel "$tested_wheel"
    fi
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

# start testing
AGENT_VERSION=$SOLARWINDS_APM_VERSION
HOSTNAME=$(cat /etc/hostname)
get_and_check_sdist
get_and_check_wheel
install_test_app_dependencies
run_instrumented_server_and_client "8001" "$SW_APM_SERVICE_KEY_STAGING-$HOSTNAME" "$SW_APM_COLLECTOR_STAGING" "NH Staging"
run_instrumented_server_and_client "8002" "$SW_APM_SERVICE_KEY_PROD-$HOSTNAME" "$SW_APM_COLLECTOR_PROD" "NH Prod"
run_instrumented_server_and_client "8003" "$SW_APM_SERVICE_KEY_AO_PROD-$HOSTNAME" "$SW_APM_COLLECTOR_AO_PROD" "AO Prod"
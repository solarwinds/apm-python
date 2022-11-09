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
  echo "WARNING: Did not provide MODE for check_sdist test."
  echo "Defaulting to MODE=local"
  MODE=local
fi
if [[ ! " ${TEST_MODES[*]} " =~ ${MODE} ]]
then
  echo "FAILED: Did not provide valid MODE for check_sdist test. Must be one of: testpypi (default), local, packagecloud, pypi."
  exit 1
else
  echo "Using provided MODE=$MODE for check_sdist test."
fi

if [ -z "$APM_ROOT" ]
then
  echo "FAILED: Did not provide valid APM_ROOT for check_sdist test."
  exit 1
fi


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

function get_wheel(){
    wheel_dir="$PWD/tmp/wheel"
    rm -rf "$wheel_dir"
    if [ "$MODE" == "local" ]
    then
        if [ -z "$PIP_INSTALL" ]; then
            echo -e "PIP_INSTALL not specified."
            echo -e "Using APM_ROOT to use one existing cp38 x86_64 wheel"
            tested_wheel=$(find "$APM_ROOT"/dist/* -name "solarwinds_apm-$AGENT_VERSION-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl")
        else
            # we need to select the right wheel (there might be multiple wheel versions in the dist directory)
            pip download \
                --only-binary solarwinds_apm \
                --find-links "$APM_ROOT"/dist \
                --no-index \
                --dest "$wheel_dir" \
                --no-deps \
                solarwinds_apm=="$AGENT_VERSION"
            tested_wheel=$(find "$wheel_dir"/* -name "solarwinds_apm-$AGENT_VERSION*.*.whl")
        fi

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

    if [ -z "$PIP_INSTALL" ]; then
        echo -e "PIP_INSTALL not specified."
        echo -e "Python wheel verified successfully.\n"
        rm -rf "$unpack_directory"
        exit 0
    else
        echo "Installing Python agent from wheel"
        pip install -I "$tested_wheel"
    fi
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

# start testing
AGENT_VERSION=$SOLARWINDS_APM_VERSION
get_and_check_wheel
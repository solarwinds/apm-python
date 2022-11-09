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
  echo "FAILED: Did not provide valid MODE. Must be one of: testpypi (default), local, packagecloud, pypi."
  exit 1
else
  echo "Using provided MODE=$MODE for check_sdist test."
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

function get_and_check_sdist(){
    echo "#### Verifying Python agent source distribution ####"
    get_sdist
    check_sdist "$sdist_tar"
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
./oboe_api.h
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

# start testing
AGENT_VERSION=$SOLARWINDS_APM_VERSION
get_and_check_sdist
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

VALID_PLATFORMS=(
    "x86_64"
    "aarch64"
)
if [ -z "$PLATFORM" ]
then
  echo "FAILED: Did not provide valid PLATFORM for check_sdist test."
  exit 1
fi
if [[ ! " ${VALID_PLATFORMS[*]} " =~ ${PLATFORM} ]]
then
  echo "FAILED: Did not provide valid PLATFORM for check_sdist test. Must be one of: x86_64, aarch64."
  exit 1
else
  echo "Using provided PLATFORM=$PLATFORM for check_sdist test."
fi

function get_sdist(){
    sdist_dir="$PWD/tmp/sdist"
    rm -rf "$sdist_dir"

    if [ "$MODE" == "local" ]
    then
        # optionally test a previous version on local for debugging
        if [ -z "$SOLARWINDS_APM_VERSION" ]; then
            # no SOLARWINDS_APM_VERSION provided, thus test version of current source code
            version_file=$APM_ROOT/solarwinds_apm/version.py
            SOLARWINDS_APM_VERSION="$(sed -n 's/__version__ = "\(.*\)"/\1/p' "$version_file")"
            echo "No SOLARWINDS_APM_VERSION provided, thus testing source code version ($SOLARWINDS_APM_VERSION)"
        fi

        sdist_tar=$APM_ROOT/dist/solarwinds_apm-${SOLARWINDS_APM_VERSION}.tar.gz
        if [ ! -f "$sdist_tar" ]; then
            echo "FAILED: Did not find sdist for version $SOLARWINDS_APM_VERSION. Please run 'make package' before running tests."
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

        if [ -z "$SOLARWINDS_APM_VERSION" ]
        then
            pip_options+=(solarwinds-apm)
        else
            pip_options+=(solarwinds-apm=="$SOLARWINDS_APM_VERSION")
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
./liboboe-1.0-aarch64.so
./liboboe-1.0-alpine-aarch64.so
./liboboe-1.0-alpine-x86_64.so
./liboboe-1.0-lambda-aarch64.so
./liboboe-1.0-lambda-x86_64.so
./liboboe-1.0-x86_64.so
./oboe.h
./oboe.py
./oboe_api.cpp
./oboe_api.h
./oboe_debug.h
./oboe_wrap.cxx"

    tar xzf "$1" --directory "$unpack_directory"
    unpack_agent=$(find "$unpack_directory"/* -type d -name "solarwinds_apm-*")
    # shellcheck disable=SC1091
    source ./_helper_check_extension_files.sh "$unpack_agent/solarwinds_apm/extension" "$expected_files"

    if [ -z "$PIP_INSTALL" ]; then
        echo -e "PIP_INSTALL not specified."
        echo -e "Source distribution verified successfully.\n"
        rm -rf "$unpack_directory"
        exit 0
    else
        echo "Installing Python agent from source"
        pip install -I "$1"
    fi
}

function get_and_check_sdist(){
    echo "#### Verifying Python agent source distribution ####"
    get_sdist
    check_sdist "$sdist_tar"
}

# start testing
get_and_check_sdist
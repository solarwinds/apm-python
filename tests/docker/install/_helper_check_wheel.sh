#!/usr/bin/env bash

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# stop on error
set -e

hostname=$(cat /etc/hostname)

# get test mode
TEST_MODES=(
    "local"
    "testpypi"
    "pypi"
)
if [ -z "$MODE" ]
then
  echo "WARNING: Did not provide MODE for check_wheel test."
  echo "Defaulting to MODE=local"
  MODE=local
fi
if [[ ! " ${TEST_MODES[*]} " =~ ${MODE} ]]
then
  echo "FAILED: Did not provide valid MODE for check_wheel test. Must be one of: testpypi (default), local, pypi."
  exit 1
else
  echo "Using provided MODE=$MODE for check_wheel test."
fi

if [ -z "$APM_ROOT" ]
then
  echo "FAILED: Did not provide valid APM_ROOT for check_wheel test."
  exit 1
fi

VALID_PLATFORMS=(
    "x86_64"
    "aarch64"
)
PLATFORM=$(uname -m)
if [[ ! " ${VALID_PLATFORMS[*]} " =~ ${PLATFORM} ]]
then
  echo "FAILED: Invalid platform for check_wheel test. Must be run on one of: x86_64, aarch64."
  exit 1
fi

if [ "$PLATFORM" == "x86_64" ]
then
  WHEEL_FILENAME=manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
elif [ "$PLATFORM" == "aarch64" ]
then
  WHEEL_FILENAME=manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl
fi
echo "Set WHEEL_FILENAME=$WHEEL_FILENAME based on platform for check_wheel test."

function get_wheel(){
    wheel_dir="$PWD/tmp/wheel"
    rm -rf "$wheel_dir"
    if [ "$MODE" == "local" ]
    then
        # optionally test a previous version on local for debugging
        if [ -z "$SOLARWINDS_APM_VERSION" ]; then
            # no SOLARWINDS_APM_VERSION provided, thus test version of current source code
            version_file=$APM_ROOT/solarwinds_apm/version.py
            SOLARWINDS_APM_VERSION="$(sed -n 's/__version__ = "\(.*\)"/\1/p' "$version_file")"
            echo "No SOLARWINDS_APM_VERSION provided, thus testing source code version ($SOLARWINDS_APM_VERSION)"
        fi

        if [ -z "$PIP_INSTALL" ]; then
            echo -e "PIP_INSTALL not specified."
            echo -e "Only testing the cp38 ${PLATFORM} wheel under ${APM_ROOT}/dist"
            tested_wheel=$(find "$APM_ROOT"/dist/* -name "solarwinds_apm-$SOLARWINDS_APM_VERSION-cp38-cp38-$WHEEL_FILENAME")
        else
            # we need to select the right wheel (there might be multiple wheel versions in the dist directory)
            pip download \
                --only-binary solarwinds_apm \
                --find-links "$APM_ROOT"/dist \
                --no-index \
                --dest "$wheel_dir" \
                --no-deps \
                solarwinds_apm=="$SOLARWINDS_APM_VERSION"
            tested_wheel=$(find "$wheel_dir"/* -name "solarwinds_apm-$SOLARWINDS_APM_VERSION*.*.whl")
        fi

        if [ ! -f "$tested_wheel" ]; then
            echo "FAILED: Did not find wheel for version $SOLARWINDS_APM_VERSION. Please run 'make package' before running tests."
            echo "Aborting tests."
            exit 1
        fi
    else
        pip_options=(--only-binary solarwinds-apm --dest "$wheel_dir")
        if [ "$MODE" == "testpypi" ]
        then
            pip_options+=(--extra-index-url https://test.pypi.org/simple/)
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
./liboboe.so
./oboe.py"
    unzip "$tested_wheel" -d "$unpack_directory"
    # shellcheck disable=SC1091
    source ./_helper_check_extension_files.sh "$unpack_directory/solarwinds_apm/extension" "$expected_files"

    if [ -z "$PIP_INSTALL" ]; then
        echo -e "PIP_INSTALL not specified."
        echo -e "Python wheel verified successfully.\n"
        rm -rf "$unpack_directory"
        exit 0
    else
        echo "Installing Python agent from wheel"
        if [ "$hostname" = "py3.12-ubuntu24.04" ]; then
            # PEP 668: Python 3.12 packages installed on Ubuntu "externally managed"
            pip install --break-system-packages --no-cache-dir --use-deprecated=legacy-resolver -I "$tested_wheel"
        else
            pip install -I "$tested_wheel"
        fi
    fi
}

function get_and_check_wheel(){
    echo "#### Verifying Python agent wheel distribution ####"
    # Python wheels are not available under Alpine Linux
    if [[ -f /etc/os-release && "$(cat /etc/os-release)" =~ "Alpine" ]]; then
        echo "Wheels are not available on Alpine Linux, skip wheel tests."
    # Amazon Linux 2's glibc version is too old to use wheels built by manylinux_2_28
    elif [[ -f /etc/os-release && "$(cat /etc/os-release)" =~ "Amazon" ]]; then
        echo "Wheels are not available on Amazon Linux, skip wheel tests."
    else
        get_wheel
        check_wheel "$tested_wheel"
    fi
}

# start testing
get_and_check_wheel
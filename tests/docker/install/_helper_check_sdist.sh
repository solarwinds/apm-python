#!/usr/bin/env bash

# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

# stop on error
set -e

# get test mode
TEST_MODES=(
    "local"
    "testpypi"
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
  echo "FAILED: Did not provide valid MODE for check_sdist test. Must be one of: testpypi (default), local, pypi."
  exit 1
else
  echo "Using provided MODE=$MODE for check_sdist test."
fi

if [ -z "$APM_ROOT" ]
then
  echo "FAILED: Did not provide valid APM_ROOT for check_sdist test."
  exit 1
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
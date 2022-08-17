#!/usr/bin/env bash

# stop on error
set -e

echo "Python system information"
echo "Python version: $(python --version 2>&1)"
echo "Pip version: $(pip --version)"

# root of solarwinds_apm package
agent_root='/code/python-solarwinds'

# setup: check inputs and clean out previous run
if [ -z $SOLARWINDS_APM_VERSION ]; then
    # no SOLARWINDS_APM_VERSION provided, thus test version of current source code
    version_file=$agent_root/solarwinds_apm/version.py
    AGENT_VERSION="$(sed -n 's/__version__ = "\(.*\)"/\1/p' $version_file)"
    echo "No SOLARWINDS_APM_VERSION provided, thus testing source code version ($AGENT_VERSION)"
else
    AGENT_VERSION=$SOLARWINDS_APM_VERSION
fi

agent_distribution=$agent_root/dist/solarwinds_apm-${AGENT_VERSION}.tar.gz

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

    pushd $1 >/dev/null
    found_swig_files=$(find . -not -path '.' | LC_ALL=C sort)
    found_oboe_version=$(cat VERSION)
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
    install_location=$(pip show solarwinds-apm | egrep -io 'location: .*' | cut -d ':' -f 2)

    pushd ${install_location}/solarwinds_apm/extension >/dev/null
    found_swig_files_inst=$(find . -not -path '.' -a -not -name '*.pyc' -a -not -name '__pycache__' | LC_ALL=C sort)

    # in Python3.8 with https://bugs.python.org/issue21536, C-extensions are not linked to libpython anymore, this leads to
    # ldd not finding the symbols defined libpython3.8.so
    if [[ -f /etc/os-release && ! "$(cat /etc/os-release)" =~ "Alpine" || ! "$(python -V 2>&1)" =~ "3.8" ]]; then
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

    # verify that version of C-extension of installed agent is same as what we expect (i.e. as determined by VERSION)
    expected_oboe_version=$(cat $agent_root/solarwinds_apm/extension/VERSION)
    export SW_APM_SERVICE_KEY=invalid-token-for-testing-1234567890:servicename
    result=$(python -c "from solarwinds_apm.extension.oboe import Config as l_config; r=l_config.getVersionString(); print(r)")

    if [ $result  != $expected_oboe_version ]; then
        echo "FAILED! Expected agent using Oboe extension version $expected_oboe_version but found version $result."
        exit 1
    fi
    echo -e "Agent is bundled with Oboe extension version $result.\n"

    echo -e "Agent installed under $install_location verified successfully.\n"
}

function check_agent_startup(){
    # verify that installed agent starts up properly
    echo "---- Verifying proper startup of installed agent ----"

    export SW_APM_DEBUG_LEVEL=6
    export SW_APM_SERVICE_KEY=invalid-token-for-testing-1234567890:servicename

    expected_agent_return=1
    if [[ -f /etc/centos-release && "$(cat /etc/centos-release)" =~ "CentOS release 6" ]]; then
        # the agent will report an unknown error (0) if we try to run on a OS where the C-extension does not compile
        expected_agent_return=0
        TEST_EXP_LOG_MESSAGES=(
            "Missing extension library."
            "Tracing is disabled and will go into no-op mode."
        )
    else
        TEST_EXP_LOG_MESSAGES=(
        ">> SSL Reporter using host='collector.solarwinds.com' port='443' log='' clientid='inva...7890:servicename'"
        "Got 1 remote settings from the collector to update"
        )
    fi

    echo -e "Agent startup verified successfully.\n"
}

function check_sdist(){
    echo "#### Verifying Python agent source distribution ####"
    unpack_directory="$PWD/tmp/sdist"
    rm -rf $unpack_directory
    mkdir -p $unpack_directory
    if [ ! -f "$agent_distribution" ]; then
        echo "FAILED: Did not find sdist for version $AGENT_VERSION. Please run 'make package' before running tests."
        echo "Aborting tests."
        exit 1
    fi
    expected_files="./VERSION
./__init__.py
./_oboe.cpython-36m-x86_64-linux-gnu.so
./_oboe.cpython-39-x86_64-linux-gnu.so
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
    tar xzf $agent_distribution --directory $unpack_directory
    check_extension_files "$unpack_directory/solarwinds_apm-${AGENT_VERSION}/solarwinds_apm/extension" "$expected_files"
    echo "Installing Python agent from source"
    pip install -I $agent_distribution
    check_installation
    check_agent_startup
    echo -e "Source distribution verified successfully.\n"
}

function check_wheel(){
    echo "#### Verifying Python agent wheel distribution ####"
    # Python wheels are not available under Alpine Linux
    if [[ -f /etc/os-release && "$(cat /etc/os-release)" =~ "Alpine" ]]; then
        echo "Wheels are not available on Alpine Linux, skip wheel tests."
        exit 0
    fi
    if [ "$HOSTNAME" = "py3.6-centos6" ]; then
        echo "Wheels are not compatible with CentOS6, thus skipping wheel tests."
        exit 0
    fi

    # we need to select the right wheel (there might be multiple wheel versions in the dist directory)
    wheel_dir=$PWD/tmp
    rm -rf $wheel_dir
    pip download \
        --only-binary solarwinds_apm \
        --find-links $agent_root/dist \
        --no-index \
        --dest $wheel_dir \
        --no-deps \
        solarwinds_apm==$AGENT_VERSION
    tested_wheel=$(ls -d $wheel_dir/* | grep solarwinds_apm-$AGENT_VERSION.*.whl)
    if [ ! -f "$tested_wheel" ]; then
        echo "FAILED: Did not find wheel for version $AGENT_VERSION. Please run 'make package' before running tests."
        echo "Aborting tests."
        exit 1
    fi
    unpack_directory="$PWD/tmp/wheel"
    rm -rf $unpack_directory
    mkdir -p $unpack_directory
    expected_files="./VERSION
./__init__.py
./_oboe.*.so
./bson
./bson/bson.h
./bson/platform_hacks.h
./liboboe-1.0.so.0
./oboe.py"
    unzip $tested_wheel -d $unpack_directory
    check_extension_files "$unpack_directory/solarwinds_apm/extension" "$expected_files"
    echo "Installing Python agent from wheel"
    pip install -I $tested_wheel
    check_installation
    check_agent_startup
    echo -e "Python wheel verified successfully.\n"
}

# start testing
check_sdist
check_wheel
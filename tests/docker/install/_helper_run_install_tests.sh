#!/usr/bin/env sh

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# Helper script to set up dependencies for the install tests, then runs the tests.
# Accounts for:
#   * Alpine not having bash nor agent install deps
#   * Amazon Linux not having agent install deps
#   * CentOS 8 being at end-of-life and needing a mirror re-point
#   * Ubuntu not having agent install deps


# stop on error
set -e

if [[ "$OSTYPE" == "darwin"* ]] || [ -n "$PYTHON_VERSION" ];
then
    # On macOS or when PYTHON_VERSION is explicitly set, use environment variable
    python_version=$PYTHON_VERSION
    python_version_no_dot=$(echo "$python_version" | sed 's/\.//')
    if [[ "$OSTYPE" == "darwin"* ]]; then
        pretty_name="macOS $(sw_vers -productVersion)"
    else
        pretty_name=$(grep PRETTY_NAME /etc/os-release | sed 's/PRETTY_NAME="//' | sed 's/"//')
    fi
else
    # get Python version from container hostname, e.g. "3.10"
    python_version=$(grep -Eo 'py3.[0-9]+[0-9]*' /etc/hostname | grep -Eo '3.[0-9]+[0-9]*')
    # no-dot Python version, e.g. "310"
    python_version_no_dot=$(echo "$python_version" | sed 's/\.//')
    # get pretty name from linux release
    pretty_name=$(grep PRETTY_NAME /etc/os-release | sed 's/PRETTY_NAME="//' | sed 's/"//')
fi

echo "Installing test dependencies for Python $python_version on $pretty_name"
# setup dependencies quietly
{
    if grep Alpine /etc/os-release; then
        # test deps
        apk add bash
        # agent deps - we install psutil for this test, so Alpine needs more deps
        apk add python3 curl linux-headers gcc musl-dev

        pip install --upgrade pip >/dev/null
    
    elif grep Ubuntu /etc/os-release; then
        ubuntu_version=$(grep VERSION_ID /etc/os-release | sed 's/VERSION_ID="//' | sed 's/"//')
        if [ "$ubuntu_version" = "20.04" ] || [ "$ubuntu_version" = "22.04" ] || [ "$ubuntu_version" = "24.04" ]; then
            apt-get update -y
            TZ=America
            ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
            # distutils needed for pip installation from pypa
            apt-get install -y \
                "python$python_version" \
                "python$python_version-distutils" \
                unzip \
                wget \
                curl
            update-alternatives --install /usr/bin/python python "/usr/bin/python$python_version" 1

            # Make sure we don't install py3.6's pip on ubuntu
            # Official get-pip documentation:
            # https://pip.pypa.io/en/stable/installation/#get-pip-py
            wget https://bootstrap.pypa.io/get-pip.py
            python get-pip.py
            pip install --upgrade pip >/dev/null

        else
            echo "ERROR: Testing on Ubuntu <20.04 not supported."
            exit 1
        fi

    elif grep "Amazon Linux" /etc/os-release; then
        if grep "Amazon Linux 2023" /etc/os-release; then
            dnf update -y
            dnf install -y \
                python3 \
                python3-pip \
                unzip \
                findutils \
                tar \
                gzip \
                bash \
                chkconfig

            if command -v update-alternatives >/dev/null 2>&1; then
                update-alternatives --install /usr/bin/python python /usr/bin/python3 1
            else
                # For AWS Lambda images or other minimal images, use symlinks
                command -v python ||
                    ln -s /usr/bin/python3 /usr/local/bin/python
                command -v pip ||
                    ln -s /usr/bin/pip3 /usr/local/bin/pip
            fi
        elif grep "Amazon Linux 2" /etc/os-release; then
            yum update -y
            yum install -y \
                unzip \
                findutils \
                tar \
                gzip \
                bash \
                chkconfig

            # For AWS Lambda images, python3 and pip3 are already installed
            # Just ensure python and pip symlinks exist
            command -v python ||
                ln -s /usr/bin/python3 /usr/local/bin/python
            command -v pip ||
                ln -s /usr/bin/pip3 /usr/local/bin/pip
        else
            echo "ERROR: Testing on Amazon Linux <2 not supported."
            exit 1
        fi
    fi
} >/dev/null

# run tests using bash so we can use pipefail
bash -c "set -o pipefail && ./install_tests.sh 2>&1"
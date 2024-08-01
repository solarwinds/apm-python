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
#
# Note: centos8 can only install Python 3.8, 3.9

# stop on error
set -e

hostname=$(cat /etc/hostname)
# get Python version from container hostname, e.g. "3.10"
python_version=$(grep -Eo 'py3.[0-9]+[0-9]*' /etc/hostname | grep -Eo '3.[0-9]+[0-9]*')
# no-dot Python version, e.g. "310"
python_version_no_dot=$(echo "$python_version" | sed 's/\.//')

pretty_name=$(grep PRETTY_NAME /etc/os-release | sed 's/PRETTY_NAME="//' | sed 's/"//')
echo "Installing test dependencies for Python $python_version on $pretty_name"
# setup dependencies quietly
# {
    if grep Alpine /etc/os-release; then
        # test deps
        apk add bash
        # agent deps
        apk add python3-dev g++ make curl

        pip install --upgrade pip >/dev/null

    elif grep "CentOS Linux 8" /etc/os-release; then
        # fix centos8 metadata download failures for repo 'appstream'
        # https://stackoverflow.com/a/71077606
        sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
        sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
        # agent and test deps
        dnf install -y \
            "python$python_version_no_dot-devel" \
            gcc \
            gcc-c++ \
            unzip \
            findutils
        dnf install -y "python$python_version_no_dot-pip" "python$python_version_no_dot-setuptools"

        command -v python ||
            ln -s "/usr/bin/python$python_version" /usr/local/bin/python
        command -v pip ||
            ln -s /usr/bin/pip3 /usr/local/bin/pip
        
        pip install --upgrade pip >/dev/null
    
    elif grep Ubuntu /etc/os-release; then
        ubuntu_version=$(grep VERSION_ID /etc/os-release | sed 's/VERSION_ID="//' | sed 's/"//')
        if [ "$ubuntu_version" = "18.04" ] || [ "$ubuntu_version" = "20.04" ] || [ "$ubuntu_version" = "22.04" ] || [ "$ubuntu_version" = "24.04" ]; then
            apt-get update -y
            TZ=America
            ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

            if [ "$python_version" = "3.12" ]; then
	            apt-get install -y software-properties-common
                add-apt-repository ppa:deadsnakes/ppa -y

                # distuils was removed from Python 3.12
                # https://docs.python.org/3/whatsnew/3.12.html
                # pip is installed as apt-get package
                apt-get install -y \
                    python3.12-full \
                    build-essential \
                    unzip \
                    wget \
                    curl

                update-alternatives --install /usr/bin/python python "/usr/bin/python$python_version" 1

            else
                apt-get install -y \
                    "python$python_version" \
                    "python$python_version-distutils" \
                    "python$python_version-dev" \
                    python3-setuptools \
                    build-essential \
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
            fi

        else
            echo "ERROR: Testing on Ubuntu <18.04 not supported."
            exit 1
        fi

    elif grep "Amazon Linux" /etc/os-release; then
        yum update -y
        if grep "Amazon Linux 2023" /etc/os-release; then
            yum install -y \
                python3-devel \
                python3-pip \
                python3-setuptools \
                gcc \
                gcc-c++ \
                unzip \
                findutils \
                tar \
                gzip
            update-alternatives --install /usr/bin/python python /usr/bin/python3 1
            # cannot symlink/update-alternatives nor upgrade pip
        else
            echo "ERROR: Testing on Amazon <2023 not supported."
            exit 1
        fi
    fi
# } >/dev/null

# run tests using bash so we can use pipefail
bash -c "set -o pipefail && ./install_tests.sh 2>&1"
#!/usr/bin/env sh

# Helper script to set up dependencies for the install tests, then runs the tests.
# Accounts for:
#   * Alpine not having bash nor agent install deps
#   * Amazon Linux not having agent install deps
#   * CentOS 8 being at end-of-life and needing a mirror re-point
#   * Ubuntu not having agent install deps
#
# Note: centos8 can only install Python 3.6, 3.8, 3.9

# stop on error
set -e

# get Python version from container hostname, e.g. "3.6", "3.10"
python_version=$(grep -Eo 'py3.[0-9]+[0-9]*' /etc/hostname | grep -Eo '3.[0-9]+[0-9]*')
# no-dot Python version, e.g. "36", "310"
python_version_no_dot=$(echo "$python_version" | sed 's/\.//')

pretty_name=$(grep PRETTY_NAME /etc/os-release | sed 's/PRETTY_NAME="//' | sed 's/"//')
echo "Installing test dependencies for Python $python_version on $pretty_name"
# setup dependencies quietly
{
    if grep Alpine /etc/os-release; then
        # test deps
        apk add bash
        # agent deps
        apk add python3-dev g++ make

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
        if [ "$python_version" = "3.6" ]; then
            dnf install -y python3-pip python3-setuptools
        else
            dnf install -y "python$python_version_no_dot-pip" "python$python_version_no_dot-setuptools"
        fi
        command -v python ||
            ln -s "/usr/bin/python$python_version" /usr/local/bin/python
        command -v pip ||
            ln -s /usr/bin/pip3 /usr/local/bin/pip
    
    elif grep Ubuntu /etc/os-release; then
        ubuntu_version=$(grep VERSION_ID /etc/os-release | sed 's/VERSION_ID="//' | sed 's/"//')
        if [ "$ubuntu_version" = "18.04" ] || [ "$ubuntu_version" = "20.04" ]; then
            apt-get update -y
            if [ "$python_version" = "3.9" ]; then
                # This particular version asks for a geographic area for some reason
                TZ=America
                ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
            fi
            if [ "$python_version" = "3.10" ] || [ "$python_version" = "3.11" ]; then
                # py3.10,3.11 not currently on main apt repo so use deadsnakes
                apt-get install -y software-properties-common
                add-apt-repository ppa:deadsnakes/ppa
            fi
            apt-get install -y \
                "python$python_version" \
                "python$python_version-dev" \
                python3-pip \
                gcc \
                unzip
            update-alternatives --install /usr/bin/python python /usr/bin/python3 1
            update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
        else
            echo "ERROR: Testing on Ubuntu <18.04 not supported."
            exit 1
        fi
    
    elif grep "Amazon Linux" /etc/os-release; then
        yum update -y
        if grep "Amazon Linux 2" /etc/os-release; then
            # agent and test deps for py3.7
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
            update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1              
        else
            # agent and test deps
            yum install -y \
                "python$python_version_no_dot-devel" \
                "python$python_version_no_dot-pip" \
                "python$python_version_no_dot-setuptools" \
                gcc \
                gcc-c++ \
                unzip \
                findutils
            alternatives --set python "/usr/bin/python$python_version"
        fi
    fi
} >/dev/null

# Click requires unicode locale
# https://click.palletsprojects.com/en/8.1.x/unicode-support/
{
    if grep "Amazon Linux" /etc/os-release || grep "CentOS Linux" /etc/os-release; then
        export LC_ALL=en_CA.utf8
        export LANG=en_CA.utf8
    else
        export LC_ALL=C.UTF-8
        export LANG=C.UTF-8
    fi
} >/dev/null

# need at least pip 19.3 to find manylinux2014 wheels
pip install --upgrade pip >/dev/null

# run tests using bash so we can use pipefail
bash -c "set -o pipefail && ./install_tests.sh 2>&1"
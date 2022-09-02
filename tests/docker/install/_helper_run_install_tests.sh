#!/usr/bin/env bash

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

# Required to read hostname
if grep "Amazon Linux" /etc/os-release; then
    yum install -y net-tools
fi

# get Python version from container hostname, e.g. "3.6", "3.10"
python_version=$(echo "$(hostname)" | grep -Eo 'py3.[0-9]+[0-9]*' | grep -Eo '3.[0-9]+[0-9]*')
# no-dot Python version, e.g. "36", "310"
python_version_no_dot=$(echo "$python_version" | sed 's/\.//')

pretty_name=$(cat /etc/os-release | grep PRETTY_NAME | sed 's/PRETTY_NAME="//' | sed 's/"//')
echo "Installing test dependencies for Python $python_version on $pretty_name"
# setup dependencies quietly
# {
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
        if [ $python_version = "3.6" ]; then
            dnf install -y python3-pip python3-setuptools
        else
            dnf install -y "python$python_version_no_dot-pip" "python$python_version_no_dot-setuptools"
        fi
        command -v python ||
            ln -s "/usr/bin/python$python_version" /usr/local/bin/python
        command -v pip ||
            ln -s /usr/bin/pip3 /usr/local/bin/pip
    
    elif grep Ubuntu /etc/os-release; then
        ubuntu_version=$(cat /etc/os-release | grep VERSION_ID | sed 's/VERSION_ID="//' | sed 's/"//')
        if [ "$ubuntu_version" = "18.04" ] || [ "$ubuntu_version" = "20.04" ]; then
            # apt/other PPA provide Python for Ubuntu 18.04+
            # agent and test deps
            apt-get upgrade && apt-get update -y
            apt-get install -y \
                "python$python_version" \
                "python$python_version-dev" \
                python3-pip \
                gcc \
                unzip
            update-alternatives --install /usr/bin/python python /usr/bin/python3 1
            update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
        else
            # Older Ubuntu versions can't use apt/other PPA (e.g. deadsnakes) for Python
            # (libssl incompatibility?)
            # "Option 2" from https://phoenixnap.com/kb/how-to-install-python-3-ubuntu
            apt-get upgrade && apt-get update -y
            apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget make
            starting_dir=$PWD
            cd /tmp
            # Assuming 3.7.9, 3.8.9, 3.9.9 all exist
            # https://www.python.org/ftp/python/
            wget "https://www.python.org/ftp/python/$python_version.9/Python-$python_version.9.tgz"
            tar -xf "Python-$python_version.9.tgz"
            cd "Python-$python_version.9"
            ./configure --enable-optimizations
            make altinstall  # "This can take up to 30 minutes to complete"
            sudo make install
            cd $starting_dir
            apt-get install -y gcc unzip
            update-alternatives --install /usr/bin/python python /usr/local/bin/python3 1

            # TODO fix this
            update-alternatives --install /usr/bin/pip pip "/usr/local/bin/pip$python_version" 1
        fi
    
    elif grep "Amazon Linux" /etc/os-release; then
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
# } >/dev/null

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
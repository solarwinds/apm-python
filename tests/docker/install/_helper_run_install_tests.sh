#!/usr/bin/env bash

# Helper script to set up dependencies for the install tests, then runs the tests.
# Accounts for:
#   * Alpine not having bash nor agent install deps
#   * Amazon Linux not having agent install deps
#   * CentOS 8 being at end-of-life and needing a mirror re-point
#   * Ubuntu not having agent install deps

# stop on error
set -e

# get Python version from container hostname, e.g. "3.6", "3.10"
python_version=$(echo "$(hostname)" | grep -Eo 'py3.[0-9]+[0-9]*' | grep -Eo '3.[0-9]+[0-9]*')

# setup dependencies
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
        # agent deps
        dnf install -y python36-devel python3-pip gcc-c++
        # test deps
        dnf install -y unzip
        command -v python ||
            ln -s /usr/bin/python3 /usr/local/bin/python
        command -v pip ||
            ln -s /usr/bin/pip3 /usr/local/bin/pip
        # the installed python uses pip 9.0.3 by default, however we need at least pip 19.3 to find manylinux2014 wheels
        pip install --upgrade pip >/dev/null
    
    elif grep Ubuntu /etc/os-release; then
        apt-get update && apt-get upgrade -y
        # agent deps
        apt-get install -y "python$python_version"-dev python3-pip gcc unzip
        update-alternatives --install /usr/bin/python python /usr/bin/python3 1
        update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
        # need at least pip 19.3 to find manylinux2014 wheels
        pip install --upgrade pip >/dev/null
    
    elif grep "Amazon Linux" /etc/os-release; then
        echo "ERROR: Not implemented"
        exit 1
    fi
} >/dev/null

# Click with Python3.6 requires unicode locale
# https://click.palletsprojects.com/en/8.1.x/unicode-support/
{
    if [ $python_version = "3.6" ]; then
        export LC_ALL=C.UTF-8
        export LANG=C.UTF-8
    fi
} >/dev/null

# run tests using bash so we can use pipefail
bash -c "set -o pipefail && ./install_tests.sh 2>&1"
#!/usr/bin/env bash

# helper script to set up dependencies for the install tests, mainly to
# account for alpine not having bash or agent install deps, then run the tests.

# stop on error
set -e

# set log file
log_file=/code/python-solarwinds/tests/docker/install/logs/install-$(hostname).log

# clean up from previous run
rm -f "$log_file"

# setup dependencies
{
    if grep Alpine /etc/os-release; then
        # test deps
        apk add bash
        # agent deps
        apk add python3-dev g++ make
    elif [ "$(hostname)" = "py3.6-centos8" ]; then
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
    fi
} >/dev/null

# run tests using bash so we can use pipefail
bash -c "set -o pipefail && /code/python-solarwinds/tests/docker/install/install_tests.sh 2>&1 | tee -a $log_file"
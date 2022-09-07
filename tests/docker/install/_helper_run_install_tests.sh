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
            # Therefore we use pyenv here (further down).
            # We still use apt-get for other version combinations (e.g. above)
            # in case pyenv's build dependencies mask SW agent dependencies.
            # https://realpython.com/intro-to-pyenv/#build-dependencies

            # Install deps
            apt-get upgrade && apt-get update -y
            apt-get install -y \
                git \
                make \
                build-essential \
                zlib1g-dev \
                libbz2-dev \
                libreadline-dev \
                libsqlite3-dev \
                wget \
                curl \
                llvm \
                libncursesw5-dev \
                xz-utils \
                tk-dev \
                libxml2-dev \
                libxmlsec1-dev \
                libffi-dev \
                liblzma-dev \
                python-openssl \
                unzip
            # apt-get install libssl-dev does not install openssl headers
            # so we do it manually
            # https://help.dreamhost.com/hc/en-us/articles/360001435926-Installing-OpenSSL-locally-under-your-username
            # TODO Sept 2023 this openssl version won't be supported anymore
            # https://www.openssl.org/source/
            first_pwd=$PWD
            wget --no-check-certificate https://www.openssl.org/source/openssl-1.1.1q.tar.gz.sha256
            wget --no-check-certificate https://www.openssl.org/source/openssl-1.1.1q.tar.gz
            if [ ! $(cat ./openssl-1.1.1q.tar.gz.sha256) = $(echo "$(sha256sum ./openssl-1.1.1q.tar.gz)" | cut -d " " -f 1) ]; then
                echo "ERROR: Could not verify cert of OpenSSL 1.1.1q"
                exit 1
            fi
            tar zxvf ./openssl-1.1.1q.tar.gz
            cd ./openssl-1.1.1q
            ./config --prefix=/usr/lib/openssl --openssldir=/usr/lib/openssl no-ssl2
            make
            make test
            make install
            cd $first_pwd
            echo 'export PATH=/usr/lib/openssl/bin:$PATH' >> ~/.bash_profile
            echo 'export LD_LIBRARY_PATH=/usr/lib/openssl/lib' >> ~/.bash_profile
            echo 'export LC_ALL="C.UTF-8"' >> ~/.bash_profile
            echo 'export LDFLAGS="-L /usr/lib/openssl/lib -Wl,-rpath,/usr/lib/openssl/lib"' >> ~/.bash_profile
            echo 'export CPPFLAGS="-I/usr/lib/ssl/include"' >> ~/.bash_profile
            . ~/.bash_profile

            # Install pyenv
            # https://github.com/pyenv/pyenv-installer
            curl https://pyenv.run | bash
            echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bash_profile
            echo 'eval "$(pyenv init -)"' >> ~/.bash_profile
            echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bash_profile
            . ~/.bash_profile
            # pyenv git compatibility issue on older versions
            # https://github.com/pyenv/pyenv-update/issues/13
            # https://github.com/pyenv/pyenv-update/blob/master/bin/pyenv-update
            # Commenting out this check seems necessary :(
            sed -i 's/verify_repo "$1" &&/#verify_repo "$1" &&/' \
                /root/.pyenv/plugins/pyenv-update/bin/pyenv-update
            sed -i "s/git pull --tags --no-rebase --ff/git pull --tags/" \
                /root/.pyenv/plugins/pyenv-update/bin/pyenv-update
            pyenv update

            # Then, install python
            # Assumes 3.6.9, 3.7.9, 3.8.9, 3.9.9 all exist
            # https://www.python.org/ftp/python/
            # py3.7+ needs CONFIGURE_OPTS flag too
            # https://github.com/pyenv/pyenv/wiki/Common-build-problems
            LDFLAGS="-Wl,-rpath,/usr/lib/openssl/lib" \
                CONFIGURE_OPTS="--with-openssl=/usr/lib/openssl" \
                pyenv install -v "$python_version.9"
            pyenv global "$python_version.9"
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
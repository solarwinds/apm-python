# helper script to set up dependencies for the install tests, mainly to
# account for alpine not having bash or agent install deps, then run the tests.

# stop on error
set -e

# set log file
log_file=/code/python-solarwinds/tests/docker/install/logs/install-$(hostname).log

# clean up from previous run
rm -f $log_file

# setup dependencies
{
    if grep Alpine /etc/os-release; then
        # test deps
        apk add bash
        # agent deps
        apk add python-dev g++ make
    elif [[ "$HOSTNAME" == "py3.6-centos8" ]]; then
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
    elif [[ "$HOSTNAME" == "py3.6-centos6" ]]; then
        # CentOs 6 is EOL, and we need to update the mirror list for yum in order to make yum work again
        sed -i "s/mirror.centos.org/vault.centos.org/" /etc/yum.repos.d/CentOS-Base.repo
        sed -i "s/mirrorlist/#mirrorlist/" /etc/yum.repos.d/CentOS-Base.repo
        sed -i "s/#baseurl/baseurl/" /etc/yum.repos.d/CentOS-Base.repo
        # install dependency packages
        yum -y install gcc gcc-c++ openssl-devel bzip2-devel libffi-devel wget tar unzip

        # install Python 3.6
        pushd /usr/src
        wget https://www.python.org/ftp/python/3.6.11/Python-3.6.11.tgz \
            && tar xzf Python-3.6.11.tgz && cd Python-3.6.11 \
            && ./configure && make && make altinstall \
            && rm -f Python-3.6.11.tgz
        popd

        # link installed Python and pip version to system Python and pip version
        ln -s /usr/local/bin/python3.6 /usr/local/bin/python
        ln -s /usr/local/bin/pip3.6 /usr/local/bin/pip

        # yum is broken under Python3, thus make sure that yum uses Python2.6
        awk 'BEGIN{print "#!/usr/bin/python2.6"}{print}' /usr/bin/yum > /tmp/yum && cat /tmp/yum > /usr/bin/yum && rm -f /tmp/yum
    fi
} >/dev/null

# run tests using bash so we can use pipefail
bash -c "set -o pipefail && /code/python-solarwinds/tests/docker/install/install_tests.sh 2>&1 | tee -a $log_file"
# build development environment to locally build solarwinds_apm Python agent and publish RC versions
FROM quay.io/pypa/manylinux2014_x86_64

# install packages need to build Ruby and dependencies need to build agent locally
RUN yum install -y \
    curl \
    gpg \
    gcc \
    gcc-c++ \
    make \
    patch \
    autoconf \
    automake \
    bison \
    libffi-devel \
    libtool \
    patch \
    readline-devel \
    sqlite-devel \
    zlib-devel \
    openssl-devel \
    wget \
    jq \
    vim \
    less \
    zip \
    && yum clean all && rm -rf /var/cache/yum

# install:
#   boto3 for interaction with AWS
#   twine to upload to TestPyPi
#   tox for automated tests
RUN python3.8 -m pip install boto3 twine tox

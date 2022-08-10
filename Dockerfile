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

# install Ruby2.5 which is needed for package cloud cli
RUN gpg --keyserver hkps://keyserver.ubuntu.com --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3 \
        7D2BAF1CF37B13E2069D6956105BD0E739499BDB && \
    curl -sSL https://get.rvm.io | bash -s stable && source /etc/profile.d/rvm.sh && \
    /usr/local/rvm/bin/rvm install 2.5.1 --disable-binary

# install PackageCloud Cli
RUN /usr/local/rvm/bin/rvm 2.5.1 do gem install package_cloud

# install:
#   boto3 for interaction with AWS
#   twine to upload to TestPyPi
#   tox for automated tests
RUN python3.8 -m pip install boto3 twine tox

# build development environment to locally build solarwinds_apm Python agent and publish RC versions
FROM quay.io/pypa/manylinux_2_28_x86_64

# install:
#   boto3 for interaction with AWS
#   twine to upload to TestPyPi
#   tox for automated tests
RUN python3.8 -m pip install boto3 twine tox

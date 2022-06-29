#!/bin/bash
#
# to build the image:
# docker build -t dev-container .
#
# to run the image:
# ./run_docker_dev.sh

docker run -it \
    --net=host \
    --cap-add SYS_PTRACE \
    --workdir /code/solarwinds_apm \
    -v "$PWD":/code/solarwinds_apm \
    -v "$PWD"/../solarwinds-apm-liboboe/:/code/solarwinds-apm-liboboe \
    dev-container bash

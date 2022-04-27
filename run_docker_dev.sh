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
    --workdir /code/solarwinds_observability \
    -v "$PWD":/code/solarwinds_observability \
    -v "$PWD"/../oboe/:/code/oboe \
    -v `echo ~`:/home/developer \
    dev-container bash

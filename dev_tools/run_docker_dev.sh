#!/bin/bash
#
# to build the image:
# docker build -t dev-container .
#
# to run the image:
# ./run_docker_dev

docker run -it \
    --net=host \
    --cap-add SYS_PTRACE \
    --workdir /code/opentelemetry_distro_solarwinds \
    -v "$PWD"/..:/code/opentelemetry_distro_solarwinds \
    -v "$PWD"/../../otel-oboe/:/code/otel_oboe \
    -v `echo ~`:/home/developer \
    dev-container bash

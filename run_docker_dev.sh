#!/bin/bash
#
# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
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

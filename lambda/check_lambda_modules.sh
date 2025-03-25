#!/usr/bin/env bash

# © 2024 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# stop on error
set -e

pwd="$PWD"
base_dir="$1"
cd "$base_dir"
echo "Checking installed lambda files and modules"

if [ ! -f "python/otel_wrapper.py" ]; then
    echo "FAILED: Missing lambda otel_wrapper"
    exit 1
fi

if [ ! -f "solarwinds-apm/wrapper" ]; then
    echo "FAILED: Missing SolarWinds lambda wrapper"
    exit 1
fi

# expected_sw_extension_files="./python/solarwinds_apm/extension/VERSION
# ./python/solarwinds_apm/extension/__init__.py
# ./python/solarwinds_apm/extension/_oboe.*.so
# ./python/solarwinds_apm/extension/bson
# ./python/solarwinds_apm/extension/bson/bson.h
# ./python/solarwinds_apm/extension/bson/platform_hacks.h
# ./python/solarwinds_apm/extension/liboboe.so
# ./python/solarwinds_apm/extension/oboe.py"
# found_sw_extension_files=$(find ./python/solarwinds_apm/extension -not -path ./python/solarwinds_apm/extension | LC_ALL=C sort)
# if [[ ! "$found_sw_extension_files" =~ $expected_sw_extension_files ]]; then
#     echo "FAILED: Missing SolarWinds extension files"
#     exit 1
# fi

expected_upstream_ext_files="./python/charset_normalizer/md.*.so
./python/charset_normalizer/md__mypyc.*.so
./python/grpc/_cython/cygrpc.*.so
./python/wrapt/_wrappers.*.so"
found_upstream_ext_files=$(find ./python/charset_normalizer ./python/grpc/_cython ./python/wrapt -regextype sed -regex ".*/*.so")
if [[ ! "$found_upstream_ext_files" =~ $expected_upstream_ext_files ]]; then
    echo "FAILED: Missing upstream extension files"
    exit 1
fi

if [ ! -f "python/opentelemetry/instrumentation/aws_lambda/__init__.py" ]; then
    echo "FAILED: Missing AWS Lambda instrumentor"
    exit 1
fi

expected_otel_files="./python/opentelemetry/instrumentation/botocore/version.py
./python/opentelemetry/instrumentation/logging/version.py"
found_otel_files=$(find ./python/opentelemetry/instrumentation/botocore ./python/opentelemetry/instrumentation/logging -regextype sed -regex ".*/version.py" | sort -k1)
if [[ ! "$found_otel_files" =~ $expected_otel_files ]]; then
    echo "FAILED: Missing key OpenTelemetry instrumentor dependency files"
    exit 1
fi

# These packages also follow PEP 420 better
expected_otel_files_pep420="./python/opentelemetry/exporter/otlp/proto/common/version/__init__.py
./python/opentelemetry/exporter/otlp/proto/grpc/version/__init__.py
./python/opentelemetry/exporter/otlp/proto/http/version/__init__.py
./python/opentelemetry/exporter/otlp/version/__init__.py
./python/opentelemetry/sdk/version/__init__.py"
found_otel_files_pep420=$(find ./python/opentelemetry/exporter ./python/opentelemetry/sdk -regextype sed -regex ".*/version/__init__.py" | sort -k1)
if [[ ! "$found_otel_files_pep420" =~ $expected_otel_files_pep420 ]]; then
    echo "FAILED: Missing key OpenTelemetry SDK and/or exporter dependency files"
    exit 1
fi

cd "$pwd"
echo "Successfully verified lambda files and modules for layer archive"
exit 0

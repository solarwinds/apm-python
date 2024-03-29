#!/bin/bash

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# User input version for release (e.g. 1.0.0)
input_version="$1"
# Version in solarwinds_apm
py_version=$(grep __version__ ../../solarwinds_apm/version.py | cut -d= -f 2 | tr -d ' "')

if [ "$input_version" != "$py_version" ]; then
    echo "ERROR: The input version $input_version does not match the configured version $py_version. You may need to Create Release PR first."
    exit 1
fi

# Try to install agent matching input_version
NOT_FOUND_LOG_MESSAGES=(
"ERROR: Could not find a version that satisfies the requirement solarwinds_apm"
"ERROR: No matching distribution found for solarwinds_apm"
)
apt-get update -y
apt-get install -y python3-pip
pip3 install solarwinds_apm=="$input_version" > install.log 2>&1

# Error if input_version already exists on pypi
already_published=false
for expected_if_not_found in "${NOT_FOUND_LOG_MESSAGES[@]}"; do
    grep -F "$expected_if_not_found" install.log || already_published=true
done
if [ $already_published == true ]; then
    echo "ERROR: The input version $input_version has already been published on PyPI."
    exit 1
fi

echo "A new solarwinds_apm $input_version can be published."

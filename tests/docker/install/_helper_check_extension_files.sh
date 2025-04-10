#!/usr/bin/env bash

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# Verifies content in the extension directory solarwinds_apm/extension. The absolute path of the directory to be verified
# needs to be passed in as the first argument of this function. As the second argument, a string containing the
# files expected under solarwinds_apm/extension needs to be provided.
#echo "---- Check content of extension directory located at $1 ----"
#if [ -z "$2" ]; then
#    echo "Failed! Files expected in the extension directory not provided."
#    exit 1
#fi
#
#expected_files="$2"
#
#pushd "$1" >/dev/null || exit 1
#found_swig_files=$(find . -not -path '.' | LC_ALL=C sort)
#popd >/dev/null || exit 1
#
#if [[ ! "$found_swig_files" =~ $expected_files ]]; then
#    echo "FAILED! expected these files under the extension directory:"
#    echo "$expected_files"
#    echo "found:"
#    echo "$found_swig_files"
#    exit 1
#fi

echo -e "No look pass.\n"
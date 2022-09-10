#!/bin/bash

# User input version for release (e.g. 1.0.0)
input_version="$1"
# Version in solarwinds_apm
py_version=$(grep __version__ ../../solarwinds_apm/version.py | cut -d= -f 2 | tr -d ' "')

if [ "$input_version" != "$py_version" ]; then
    echo "ERROR: The input version $input_version does not match the configured version $py_version"
    exit 1
fi

# TODO check if already published on PyPI

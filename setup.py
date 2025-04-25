#!/usr/bin/env python

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# pylint: disable-msg=missing-module-docstring
import logging
import os
import platform
import sys

from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py


logger = logging.getLogger(__name__)

def is_alpine_distro():
    """Checks if current system is Alpine Linux."""
    if os.path.exists("/etc/alpine-release"):
        return True

    try:
        with open("/etc/os-release", 'r') as osr:
            releases = osr.readlines()
            releases = [l[:-1] for l in releases]
        if 'NAME="Alpine Linux"' in releases:
            return True
    except (FileNotFoundError, IsADirectoryError) as ecp:
        logger.info(
            "[SETUP] Could not find /etc/os-release file. "
            "Assuming distro not Alpine: {e}".format(e=ecp))
    except PermissionError as ecp:
        logger.info(
            "[SETUP] Permission denied for /etc/os-release. "
            "Assuming distro not Alpine: {e}".format(e=ecp))
    except (IOError, ValueError) as ecp:
        logger.info(
            "[SETUP] Could not open or read /etc/os-release file. "
            "Assuming distro not Alpine: {e}".format(e=ecp))
    except Exception as ecp:
        logger.info(
            "[SETUP] Something went wrong at is_alpine_distro. "
            "Assuming distro not Alpine:: {e}".format(e=ecp))

    return False

def python_version_supported():
    if sys.version_info[0] == 3 and sys.version_info[1] >= 7:
        return True
    return False

def os_supported():
    is_linux = sys.platform.startswith('linux')
    is_x86_64_or_aarch64 = platform.machine() in ["x86_64", "aarch64"]
    return is_linux and is_x86_64_or_aarch64

if not (python_version_supported() and os_supported()):
    logger.warning(
        "[SETUP] This package supports only Python 3.8 and above on Linux x86_64 or aarch64. "
        "Other platform or python versions may not work as expected.")

# Extra args in case old setuptools version
setup(
    name="solarwinds_apm",
    python_requires='>=3.8',
)

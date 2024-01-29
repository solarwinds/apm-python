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

from setuptools import (
    Extension,
    setup
)
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
    except Exception:
        pass

    return False

def python_version_supported():
    if sys.version_info[0] == 3 and sys.version_info[1] >= 7:
        return True
    return False

def os_supported():
    is_linux = sys.platform.startswith('linux')
    is_x86_64_or_aarch64 = platform.machine() in ["x86_64", "aarch64"]
    return is_linux and is_x86_64_or_aarch64

def link_oboe_lib(src_lib):
    """Set up the C-extension library.

    Creates a .so library symlink ('liboboe.so') needed when the
    solarwinds_apm package is built from source. This step is needed since Oboe library is platform specific.

    The src_lib parameter is the name of the library file under solarwinds_apm/extension the above mentioned symlink will
    point to. If a file with the provided name does not exist, no symlinks will be created."""

    logger.info("Create link to platform specific liboboe library file")
    link_dst = 'liboboe.so'
    cwd = os.getcwd()
    try:
        os.chdir('./solarwinds_apm/extension/')
        if not os.path.exists(src_lib):
            raise Exception("C-extension library file {} does not exist.".format(src_lib))
        if os.path.exists(link_dst):
            # if the destination library file exists already, it needs to be deleted, otherwise linking will fail
            os.remove(link_dst)
            logger.info("Removed %s" % link_dst)
        os.symlink(src_lib, link_dst)
        logger.info("Created new link at {} to {}".format(link_dst, src_lib))
    except Exception as ecp:
        logger.info("[SETUP] failed to set up link to C-extension library: {e}".format(e=ecp))
    finally:
        os.chdir(cwd)

class CustomBuild(build_py):
    def run(self):
        self.run_command('build_ext')
        build_py.run(self)

class CustomBuildExt(build_ext):
    def run(self):
        if sys.platform == 'darwin':
            return

        platform_m = platform.machine()
        oboe_lib = f"liboboe-1.0-"
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") and os.environ.get("LAMBDA_TASK_ROOT"):
            oboe_lib = f"{oboe_lib}lambda-"
        if is_alpine_distro():
            oboe_lib = f"{oboe_lib}alpine-"
        oboe_lib = f"{oboe_lib}{platform_m}.so"

        link_oboe_lib(oboe_lib)
        build_ext.run(self)


if not (python_version_supported() and os_supported()):
    logger.warning(
        "[SETUP] This package supports only Python 3.7 and above on Linux x86_64 or aarch64. "
        "Other platform or python versions may not work as expected.")

ext_modules = [
    Extension(
        name='solarwinds_apm.extension._oboe',
        sources=[
            'solarwinds_apm/extension/oboe_wrap.cxx',
            'solarwinds_apm/extension/oboe_api.cpp'
        ],
        depends=[
            'solarwinds_apm/extension/oboe_api.h',
        ],
        include_dirs=[
            'solarwinds_apm/certs',
            'solarwinds_apm/extension/bson',
            'solarwinds_apm'
        ],
        libraries=['oboe', 'rt'],
        library_dirs=['solarwinds_apm/extension'],
        extra_compile_args=["-std=c++14"],
        runtime_library_dirs=['$ORIGIN']
    ),
]

# Extra args in case old setuptools version
setup(
    name="solarwinds_apm",
    cmdclass={
        'build_ext': CustomBuildExt,
        'build_py': CustomBuild,
    },
    ext_modules=ext_modules,
    python_requires='>=3.7',
)

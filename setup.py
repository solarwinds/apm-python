#!/usr/bin/env python

#    Copyright 2022 SolarWinds, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable-msg=missing-module-docstring
import logging
import os
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
    if sys.version_info[0] == 3 and sys.version_info[1] >= 6:
        return True
    return False

def os_supported():
    return sys.platform.startswith('linux')

def link_oboe_lib(src_lib):
    """Set up the C-extension libraries.

    Create two .so library symlinks, namely 'liboboe-1.0.so' and 'liboboe-1.0.so.0 which are needed when the
    solarwinds_apm package is built from source. This step is needed since Oboe library is platform specific.

    The src_lib parameter is the name of the library file under solarwinds_apm/extension the above mentioned symlinks will
    point to. If a file with the provided name does not exist, no symlinks will be created."""

    logger.info("Create links to platform specific liboboe library file")
    link_dst = ('liboboe-1.0.so', 'liboboe-1.0.so.0')
    cwd = os.getcwd()
    try:
        os.chdir('./solarwinds_apm/extension/')
        if not os.path.exists(src_lib):
            raise Exception("C-extension library file {} does not exist.".format(src_lib))
        for dst in link_dst:
            if os.path.exists(dst):
                # if the destination library files exist already, they need to be deleted, otherwise linking will fail
                os.remove(dst)
                logger.info("Removed %s" % dst)
            os.symlink(src_lib, dst)
            logger.info("Created new link at {} to {}".format(dst, src_lib))
    except Exception as ecp:
        logger.info("[SETUP] failed to set up links to C-extension library: {e}".format(e=ecp))
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

        oboe_lib = "liboboe-1.0-alpine-x86_64.so.0.0.0" if is_alpine_distro() else "liboboe-1.0-x86_64.so.0.0.0"
        link_oboe_lib(oboe_lib)
        build_ext.run(self)

class CustomBuildExtLambda(build_ext):
    def run(self):
        link_oboe_lib("liboboe-1.0-lambda-x86_64.so.0.0.0")
        build_ext.run(self)


if not (python_version_supported() and os_supported()):
    logger.warn(
        "[SETUP] This package supports only Python 3.7 and above on Linux. "
        "Other platform or python versions may not work as expected.")

ext_modules = [
    Extension('solarwinds_apm.extension._oboe',
              sources=[
                  'solarwinds_apm/extension/oboe_wrap.cxx',
                  'solarwinds_apm/extension/oboe_api.cpp'
              ],
              depends=[
                  'solarwinds_apm/extension/oboe_api.hpp',
              ],
              include_dirs=[
                  'solarwinds_apm/extension',
                  'solarwinds_apm'
              ],
              libraries=['oboe-1.0', 'rt'],
              library_dirs=['solarwinds_apm/extension'],
              extra_compile_args=["-std=c++11"],
              runtime_library_dirs=['$ORIGIN']),
]

setup(
    cmdclass={
        'build_ext': CustomBuildExt,
        'build_ext_lambda': CustomBuildExtLambda,
        'build_py': CustomBuild,
    },
    ext_modules=ext_modules,
)

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
import io
import logging
import os
import sys

from setuptools import (
    Extension,
    setup
)
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py


BASE_DIR = os.path.dirname(__file__)
VERSION_FILENAME = os.path.join(
    BASE_DIR, "solarwinds_apm", "version.py"
)
PACKAGE_INFO = {}
with open(VERSION_FILENAME, encoding="utf-8") as f:
    exec(f.read(), PACKAGE_INFO)


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


def os_supported():
    return sys.platform.startswith('linux')


if not (python_version_supported() and os_supported()):
    logger.warn(
        "[SETUP] This package supports only Python 3.6 and above on Linux. "
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


with io.open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='solarwinds_apm',
    cmdclass={
        'build_ext': CustomBuildExt,
        'build_ext_lambda': CustomBuildExtLambda,
        'build_py': CustomBuild,
    },
    version=PACKAGE_INFO["__version__"],
    author='SolarWinds, LLC',
    author_email='support@appoptics.com',
    url='https://www.appoptics.com/monitor/python-performance',
    download_url='https://pypi.python.org/pypi/solarwinds_apm',
    description='Custom distro for OpenTelemetry to connect to SolarWinds',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='solarwinds_apm appoptics_apm traceview tracelytics oboe liboboe instrumentation performance',
    ext_modules=ext_modules,
    packages=['solarwinds_apm', 'solarwinds_apm.extension'],
    package_data={
        'solarwinds_apm': ['extension/liboboe-1.0.so.0', 'extension/VERSION', 'extension/bson/bson.h', 'extension/bson/platform_hacks.h']
    },
    license_files=('LICENSE',),
    install_requires=[
        'opentelemetry-api==1.12.0rc1',
        'opentelemetry-sdk==1.12.0rc1',
        'opentelemetry-instrumentation==0.31b0',
    ],
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Typing :: Typed",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
    ],
    entry_points={
        'opentelemetry_distro': [
            'solarwinds_distro = solarwinds_apm.distro:SolarWindsDistro',
        ],
        'opentelemetry_configurator': [
            'solarwinds_configurator = solarwinds_apm.configurator:SolarWindsConfigurator',
        ],
        'opentelemetry_propagator': [
            'solarwinds_propagator = solarwinds_apm.propagator:SolarWindsPropagator',
        ],
        'opentelemetry_traces_exporter': [
            'solarwinds_exporter = solarwinds_apm.exporter:SolarWindsSpanExporter',
        ],
        'opentelemetry_traces_sampler': [
            'solarwinds_sampler = solarwinds_apm.sampler:ParentBasedSwSampler',
        ],
    },
)

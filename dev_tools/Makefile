#    Copyright 2021 SolarWinds, LLC
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
# ----The Makefile for automated building (and hopefully) deployment
SHELL=bash

.DEFAULT_GOAL := wrapper

#----------------------------------------------------------------------------------------------------------------------#
# variable definitions and recipes for downloading of required header and library files
#----------------------------------------------------------------------------------------------------------------------#
OTELOBOEREPO := /code/oboe/liboboe

# Copy the pre-compiled liboboe shared library from source specified in OTELOBOEREPO
copy-liboboe:
	@echo -e "Copying shared library.\n"
	@cd ../opentelemetry_distro_solarwinds/extension; \
		cp "${OTELOBOEREPO}/liboboe-1.0-x86_64.so.0.0.0" .; \
		if [ $$? -ne 0 ]; then echo " **** failed to copy shared library ****" ; exit 1; fi;

# Copy liboboe header files (Python wrapper for Oboe c-lib) from source specified in OTELOBOEREPO
copy-headers: copy-bson-headers
	@echo -e "Copying header files (.hpp, .h, .i)"
	@echo "Copying files from ${OTELOBOEREPO}:"
	@cd ../opentelemetry_distro_solarwinds/extension; \
		for i in oboe.h oboe_api.hpp oboe_api.cpp oboe_debug.h; do \
			echo "Copying $$i"; \
			cp "${OTELOBOEREPO}/$$i" .; \
			if [ $$? -ne 0 ]; then echo " **** failed to copy $$i ****" ; exit 1; fi; \
		done
	@cd ../opentelemetry_distro_solarwinds/extension; \
		echo "Copying oboe.i"; \
		cp "${OTELOBOEREPO}/swig/oboe.i" .; \
		if [ $$? -ne 0 ]; then echo " **** failed to copy oboe.i ****" ; exit 1; fi; \

# Copy bson header files from source specified in OTELOBOEREPO
copy-bson-headers:
	@echo -e "Copying bson header files (.hpp, .h)"
	@if [ ! -d ../opentelemetry_distro_solarwinds/extension/bson ]; then \
		mkdir ../opentelemetry_distro_solarwinds/extension/bson; \
		echo "Created ../opentelemetry_distro_solarwinds/extension/bson"; \
	 fi
	@echo "Copying files from ${OTELOBOEREPO}:"
	@cd ../opentelemetry_distro_solarwinds/extension/bson; \
		for i in bson.h platform_hacks.h; do \
			echo "Copying $$i"; \
			cp "${OTELOBOEREPO}/bson/$$i" .; \
			if [ $$? -ne 0 ]; then echo " **** fail to copy $$i ****" ; exit 1; fi; \
		done

# copy artifacts from local oboe
copy-all: copy-headers copy-liboboe

#----------------------------------------------------------------------------------------------------------------------#
# recipes for building the package distribution
#----------------------------------------------------------------------------------------------------------------------#
# Check if SWIG is installed
check-swig:
	@echo -e "Is SWIG installed?"
	@command -v swig >/dev/null 2>&1 || \
		{ echo >&2 "Swig is required to build the distribution. Aborting."; exit 1;}
	@echo -e "Yes."

# Build the Python wrapper from liboboe headers inside build container
wrapper: check-swig copy-all
	@echo -e "Generating SWIG wrapper for C/C++ headers."
	@cd ../opentelemetry_distro_solarwinds/extension && ./gen_bindings.sh

# Create package source distribution archive
sdist: wrapper
	@echo -e "Generating python agent sdist package"
	@python3.8 setup.py sdist
	@echo -e "\nDone."

.PHONY: nothing check-swig download-liboboe download-headers wrapper sdist

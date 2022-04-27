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

.DEFAULT_GOAL := nothing

# By default, 'make' does nothing and only prints available options
nothing:
	@echo -e "\nHi! How can I help you?"
	@echo -e "  - 'make wrapper':"
	@echo -e "          Locally generate SWIG wrapper for C/C++ headers."
	@echo -e "  - 'make wrapper-from-local':"
	@echo -e "          Locally generate SWIG wrapper for C/C++ headers using neighbouring oboe checkout."
	@echo -e "Check the Makefile for other targets/options.\n"

#----------------------------------------------------------------------------------------------------------------------#
# variable definitions and recipes for downloading of required header and library files
#----------------------------------------------------------------------------------------------------------------------#

# LIBOBOE is the name of the liboboe shared library
LIBOBOEALPINE := "liboboe-1.0-alpine-x86_64.so.0.0.0"
LIBOBOEORG := "liboboe-1.0-x86_64.so.0.0.0"
LIBOBOESERVERLESS := "liboboe-1.0-lambda-x86_64.so.0.0.0"
# Version of the C-library extension is stored under /solarwinds_observability/extension/VERSION (Otel export compatible as of 10.3.4)
OBOEVERSION := $(shell cat ./solarwinds_observability/extension/VERSION)

# specification of source of header and library files
ifdef S3_OBOE
    OBOEREPO := "https://rc-files-t2.s3-us-west-2.amazonaws.com/c-lib/${OBOEVERSION}"
else
    OBOEREPO := "https://files.appoptics.com/c-lib/${OBOEVERSION}"
endif

verify-oboe-version:
	@echo -e "Downloading Oboe VERSION file from ${OBOEREPO}"
	@cd solarwinds_observability/extension; \
		curl -f "${OBOEREPO}/VERSION" -o "VERSION.tmp" ; \
		if [ $$? -ne 0 ]; then echo " **** Failed to download VERSION  ****" ; exit 1; fi; \
		diff -q VERSION.tmp VERSION; \
		if [ $$? -ne 0 ]; then \
			echo " **** Failed version verification! Local VERSION differs from downloaded version   ****" ; \
			echo "Content of local VERSION file:"; \
			cat VERSION; \
			echo "Content of downloaded VERSION file:"; \
			cat VERSION.tmp; \
			rm VERSION.tmp; \
			exit 1; \
		fi; \
		rm VERSION.tmp
	@echo -e "VERSION verification successful"

# Download the pre-compiled liboboe shared library from source specified in OBOEREPO
download-liboboe: verify-oboe-version
	@echo -e "Downloading ${LIBOBOEORG} and ${LIBOBOEALPINE} shared libraries.\n"
	@cd solarwinds_observability/extension; \
		curl -o ${LIBOBOEORG}  "${OBOEREPO}/${LIBOBOEORG}"; \
		if [ $$? -ne 0 ]; then echo " **** fail to download ${LIBOBOEORG} ****" ; exit 1; fi; \
		curl -o ${LIBOBOEALPINE}  "${OBOEREPO}/${LIBOBOEALPINE}"; \
		if [ $$? -ne 0 ]; then echo " **** fail to download ${LIBOBOEALPINE} ****" ; exit 1; fi; \
		curl -f -O "${OBOEREPO}/VERSION"; \
		if [ $$? -ne 0 ]; then echo " **** fail to download VERSION  ****" ; exit 1; fi
	@echo -e "Downloading ${LIBOBOESERVERLESS} shared library.\n"
	@cd solarwinds_observability/extension; \
		curl -o $(LIBOBOESERVERLESS)  "${OBOEREPO}/${LIBOBOESERVERLESS}"; \
		if [ $$? -ne 0 ]; then echo " **** failed to download ${LIBOBOESERVERLESS} ****" ; exit 1; fi;

# Download liboboe header files (Python wrapper for Oboe c-lib) from source specified in OBOEREPO
download-headers: verify-oboe-version download-bson-headers
	@echo -e "Downloading header files (.hpp, .h, .i)"
	@echo "Downloading files from ${OBOEREPO}:"
	@cd solarwinds_observability/extension; \
		for i in oboe.h oboe_api.hpp oboe_api.cpp oboe.i oboe_debug.h; do \
			echo "Downloading $$i"; \
			curl -f -O "${OBOEREPO}/include/$$i"; \
			if [ $$? -ne 0 ]; then echo " **** fail to download $$i ****" ; exit 1; fi; \
		done

# Download bson header files from source specified in OBOEREPO
download-bson-headers:
	@echo -e "Downloading bson header files (.hpp, .h)"
	@if [ ! -d solarwinds_observability/extension/bson ]; then \
		mkdir solarwinds_observability/extension/bson; \
		echo "Created solarwinds_observability/extension/bson"; \
	 fi
	@echo "Downloading files from ${OBOEREPO}:"
	@cd solarwinds_observability/extension/bson; \
		for i in bson.h platform_hacks.h; do \
			echo "Downloading $$i"; \
			curl -f -O "${OBOEREPO}/include/bson/$$i"; \
			if [ $$? -ne 0 ]; then echo " **** fail to download $$i ****" ; exit 1; fi; \
		done

# download all required header and library files
download-all: download-headers download-liboboe


#----------------------------------------------------------------------------------------------------------------------#
# DEPRECATED: variable definitions and recipes for copying required header and library files from neighbouring local liboboe directory
#----------------------------------------------------------------------------------------------------------------------#

OTELOBOEREPO := /code/oboe/liboboe

# Copy the pre-compiled liboboe shared library from source specified in OTELOBOEREPO
copy-liboboe:
	@echo -e "Copying shared library.\n"
	@cd solarwinds_observability/extension; \
		cp "${OTELOBOEREPO}/liboboe-1.0-x86_64.so.0.0.0" .; \
		if [ $$? -ne 0 ]; then echo " **** failed to copy shared library ****" ; exit 1; fi;

# Copy liboboe header files (Python wrapper for Oboe c-lib) from source specified in OTELOBOEREPO
copy-headers: copy-bson-headers
	@echo -e "Copying header files (.hpp, .h, .i)"
	@echo "Copying files from ${OTELOBOEREPO}:"
	@cd solarwinds_observability/extension; \
		for i in oboe.h oboe_api.hpp oboe_api.cpp oboe_debug.h; do \
			echo "Copying $$i"; \
			cp "${OTELOBOEREPO}/$$i" .; \
			if [ $$? -ne 0 ]; then echo " **** failed to copy $$i ****" ; exit 1; fi; \
		done
	@cd solarwinds_observability/extension; \
		echo "Copying oboe.i"; \
		cp "${OTELOBOEREPO}/swig/oboe.i" .; \
		if [ $$? -ne 0 ]; then echo " **** failed to copy oboe.i ****" ; exit 1; fi; \

# Copy bson header files from source specified in OTELOBOEREPO
copy-bson-headers:
	@echo -e "Copying bson header files (.hpp, .h)"
	@if [ ! -d solarwinds_observability/extension/bson ]; then \
		mkdir solarwinds_observability/extension/bson; \
		echo "Created solarwinds_observability/extension/bson"; \
	 fi
	@echo "Copying files from ${OTELOBOEREPO}:"
	@cd solarwinds_observability/extension/bson; \
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
wrapper: check-swig download-all
	@echo -e "Generating SWIG wrapper for C/C++ headers."
	@cd solarwinds_observability/extension && ./gen_bindings.sh

# Build the Python wrapper from liboboe headers inside build container
wrapper-from-local: check-swig copy-all
	@echo -e "Generating SWIG wrapper for C/C++ headers, from local neighbouring oboe checkout"
	@cd solarwinds_observability/extension && ./gen_bindings.sh

# Create package source distribution archive
sdist: wrapper
	@echo -e "Generating python agent sdist package"
	@python3.8 setup.py sdist
	@echo -e "\nDone."

# clean up everything.
clean:
	@echo -e "Cleaning intermediate files."
	@cd solarwinds_observability/extension; rm -f oboe.py _oboe.so liboboe-1.0*so*
	@echo -e "Done."

.PHONY: nothing verify-oboe-version download-liboboe download-headers download-bson-headers download-all copy-liboboe copy-headers copy-bson-headers copy-all check-swig wrapper wrapper-from-local sdist clean

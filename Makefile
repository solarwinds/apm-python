# © 2023-2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# ----The Makefile for automated building (and hopefully) deployment
SHELL=bash

.DEFAULT_GOAL := nothing

# By default, 'make' does nothing and only prints available options
nothing:
	@echo -e "\nHi! How can I help you?"
	@echo -e "  - 'make package':"
	@echo -e "          Build the agent package distribution (sdist and bdist)."
	@echo -e "  - 'make sdist':"
	@echo -e "          Build sdist zip archive (.tar.gz in dist/)."
	@echo -e "  - 'make wheel':"
	@echo -e "          Build Python bdist (.whl in dist/)."
	@echo -e "  - 'make aws-lambda':"
	@echo -e "          Build the AWS Lambda layer (zip archive in dist/)."
	@echo -e "Check the Makefile for other targets/options.\n"

#----------------------------------------------------------------------------------------------------------------------#
# check if build deps are installed
#----------------------------------------------------------------------------------------------------------------------#

check-zip:
	@echo -e "Is zip installed?"
	@command -v zip >/dev/null 2>&1 || \
		{ echo >&2 "zip is required to build lambda layer. Installing."; dnf install zip -y;}
	@echo -e "Yes."

#----------------------------------------------------------------------------------------------------------------------#
# recipes for building the package distribution
#----------------------------------------------------------------------------------------------------------------------#

# Create package source distribution archive
sdist:
	@echo -e "Generating python agent sdist package"
	@python3.9 -m build --sdist
	@echo -e "\nDone."

# Check local package source distribution archive contents, without install
CURR_DIR := $(shell pwd)
check-sdist-local:
	@cd ./tests/docker/install && MODE=local APM_ROOT=$(CURR_DIR) ./_helper_check_sdist.sh
	@cd $(CURR_DIR)

# Build the Python library package bdist (wheel) for 64 bit linux systems using Python 3.9
wheel:
	@echo -e "Generating Python library wheel for 64 bit systems"
	@/opt/python/cp39-cp39/bin/pip -v wheel . -w ./dist/ --no-deps
	@echo -e "\nDone."

# Check local package wheel contents, without install
check-wheel-local:
	@cd ./tests/docker/install && MODE=local APM_ROOT=$(CURR_DIR) ./_helper_check_wheel.sh
	@cd $(CURR_DIR)

# Build and check the full Python agent distribution (sdist and wheels)
package: sdist check-sdist-local wheel check-wheel-local

target_dir := "./tmp-lambda"
install-lambda-modules:
	@if [ -f ./dist/solarwinds_apm_lambda.zip ]; then \
		echo -e "Deleting old solarwinds_apm_lambda.zip"; \
		rm ./dist/solarwinds_apm_lambda.zip; \
	 fi
	rm -rf ${target_dir}
	@echo -e "Creating target directory ${target_dir} for AWS Lambda layer artifacts."
	mkdir -p ${target_dir}/python
	@echo -e "Install setuptools"
	/opt/python/cp39-cp39/bin/pip install setuptools
	@echo -e "Install upstream dependencies to include in layer"
	/opt/python/cp39-cp39/bin/pip install -t ${target_dir}/python -r lambda/requirements.txt
	@echo -e "Install upstream dependencies without deps to include in layer"
	@/opt/python/cp39-cp39/bin/pip install -t ${target_dir}/nodeps -r lambda/requirements-nodeps.txt --no-deps
	@echo -e "Install solarwinds_apm to be packed up in zip archive to target directory."
	@/opt/python/cp39-cp39/bin/pip install . -t ${target_dir}/nodeps --no-deps
	@echo -e "Moving no-deps dependencies, needed for full opentelemetry/instrumentation path"
	@cp -r ${target_dir}/nodeps/* ${target_dir}/python
	@rm -rf ${target_dir}/nodeps
	@echo -e "Copying OpenTelemetry lambda wrapper and entry script into target directory."
	@cp lambda/otel_wrapper.py ${target_dir}/python/otel_wrapper.py
	@mkdir ${target_dir}/solarwinds-apm/
	@cp lambda/solarwinds-apm/wrapper ${target_dir}/solarwinds-apm/wrapper
	@chmod 755 ${target_dir}/solarwinds-apm/wrapper
	@echo -e "Removing unnecessary boto, six, urllib3 installations"
	@rm -rf ${target_dir}/python/boto*
	@rm -rf ${target_dir}/python/six*
	@rm -rf ${target_dir}/python/urllib3*
	@find ${target_dir}/python -type d -name '__pycache__' | xargs rm -rf

check-lambda-modules:
	./lambda/check_lambda_modules.sh ${target_dir}

# Build APM Python AWS lambda layer as zip artifact
target_dir := "./tmp-lambda"
aws-lambda: export AWS_LAMBDA_FUNCTION_NAME = set-for-build
aws-lambda: export LAMBDA_TASK_ROOT = set-for-build
aws-lambda: check-zip install-lambda-modules check-lambda-modules
	@if [[ ! -d dist ]]; then mkdir dist; fi
	@pushd ${target_dir} && zip -r ../dist/solarwinds_apm_lambda.zip . && popd
	@rm -rf ${target_dir} ./build
	@echo -e "\nDone."

#----------------------------------------------------------------------------------------------------------------------#
# variable definitions and recipes for testing, linting, cleanup
#----------------------------------------------------------------------------------------------------------------------#

# Example: make tox OPTIONS="-e py39-test"
# Example: make tox OPTIONS="-e lint -- --check-only"
tox:
	@python3.9 -m tox $(OPTIONS)

format:
	@echo -e "Not implemented."

lint:
	@echo -e "Not implemented."

# clean up intermediate build/dist files.
clean:
	@echo -e "Cleaning up intermediate build/dist files."
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' | xargs rm -rf
	@find . -type d -name '*.ropeproject' | xargs rm -rf
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg*
	@rm -f MANIFEST
	@rm -rf docs/build/
	@rm -f .coverage.*
	@echo -e "Done."

# clean up tox files
clean-tox:
	@echo -e "Cleaning up tox files."
	@rm -rf .tox/
	@echo -e "Done."

.PHONY: nothing check-zip sdist check-sdist-local wheel check-wheel-local package install-lambda-modules check-lambda-modules aws-lambda tox format lint clean clean-tox

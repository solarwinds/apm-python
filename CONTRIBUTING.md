# Contributing to solarwinds_apm
----

## Issues

### Security issues

Please report any security issues privately to the SolarWinds Product Security Incident Response Team (PSIRT) at [psirt@solarwinds.com](mailto:psirt@solarwinds.com).

### All other issues

For non-security issues, please submit your ideas, questions, or problems as [GitHub issues](https://github.com/solarwindscloud/solarwinds-apm-python/issues). Please add as much information as you can, such as: Python version, platform, installed dependencies and their version numbers, hosting, code examples or gists, steps to reproduce, stack traces, and logs. SolarWinds project maintainers may ask for clarification or more context after submission.

----
## Contributing
### Submitting Pull Requests
TODO

### Merging PRs
TODO

----
## Development

### Prerequisites

* Docker

### Build Container

To create and run a Docker container for testing and builds, run the following:
```bash
docker build -t dev-container .
./run_docker_dev.sh
```

The build container is based on the [PyPA image](https://github.com/pypa/manylinux) `manylinux2014_x86_64`. It uses [SWIG](https://www.swig.org/Doc1.3/Python.html) to compile required C/C++ libraries into a C-extension dependency.

### Regression Tests

Automated testing of this repo uses [tox](https://tox.readthedocs.io) and runs in Python 3.7, 3.8, 3.9, and/or 3.10 because these are the versions supported by [OTel Python](https://github.com/open-telemetry/opentelemetry-python/blob/main/tox.ini). Testing can be run inside the build container which provides all dependencies and a compiled C-extension. Here is how to set up then run unit and integration tests locally:

1. Create and run the Docker build container as described above.
2. Inside the build container: `make wrapper`. This downloads the version of oboe defined in `extension/VERSION` from SolarWinds Cloud and builds the SWIG bindings.
3. To run all tests for a specific version, provide tox options as a string. For example, to run in Python 3.7 against AO prod: `make tox OPTIONS="-e py37-nh-staging"`.
4. (WARNING: slow!) To run all tests for all supported Python environments, as well as linting and formatting: `make tox`
5. Other regular `tox` arguments can be included in `OPTIONS`. Some examples:

```
# Recreate tox environment for Python 3.8 pointed at AO prod
make tox OPTIONS="--recreate -e py38-ao-prod"

# Run only the Scenario 8 integration test, in all environments
make tox OPTIONS="-- tests/integration/test_scenario_1.py"
```

The unit and integration tests are also run on GitHub with the [Run tox tests](https://github.com/solarwindscloud/solarwinds-apm-python/actions/workflows/run_tox_tests.yaml) workflow.


### Install Agent in Development Mode

TODO

### Build Agent Source Distribution Archive

The `manylinux` build container can be used to generate a zipped archive source distribution (sdist), a wheel / build distribution (bdist), or both (package distribution). For prereleases, the container can be used to upload a package to SolarWinds PackageCloud.

For more information, run `make` inside the build container.

### Install tests

`tests/docker/install` can be used to test agent installation from sdist and wheel (if applicable, i.e. no wheels on Alpine). Part of this test workflow is the launch of minimal, instrumented Flask apps and submitting requests to them. This checks that the installed agent can connect to the collector.



#### Checking exported traces

If you have access to  traces can be generated and exported to SolarWinds. Installation test-dedicated services exist on SWO and are named `apm-python-install-testing-<python_version>-<linux_distro>` (e.g. `apm-python-install-testing-py3.7-debian10`). Traces exported there can be inspected manually after GH workflow trigger.

To set up, you'll need the API tokens named `apm-python-install-testing` for each of:
* SolarWinds staging (org: Staging)
* SolarWinds production (org: SWI)
* AppOptics production (org: Agent Testing)

Set these and the staging/prod collector endpoints as environment variables:
```
export SW_APM_COLLECTOR_AO_PROD=collector.appoptics.com
export SW_APM_COLLECTOR_PROD=apm.collector.cloud.solarwinds.com
export SW_APM_COLLECTOR_STAGING=apm.collector.st-ssp.solarwinds.com
export SW_APM_SERVICE_KEY_AO_PROD=<api_token>:apm-python-install-testing
export SW_APM_SERVICE_KEY_PROD=<api_token>:apm-python-install-testing
export SW_APM_SERVICE_KEY_STAGING=<api_token>:apm-python-install-testing
```

Optionally, you can set `MODE` (defaults to `local`). When `MODE=local`, the sdist and wheel must be pre-built by the build container (i.e. `run_docker.dev.sh`, `make package`). For all other modes (`MODE=testpypi`, `MODE=packagecloud`, `MODE=pypi`), the tests pull the agent from one of the public registries so local builds aren't needed.

You can also set `SOLARWINDS_APM_VERSION`. This determines the version of distribution installed. If `MODE=local` or not set, the tests will fail if no source distribution or compatible wheel can be found under `dist/` or in the registries. If `SOLARWINDS_APM_VERSION` is not set, the version as specified by the source code currently checked out will be assumed.

To run the install tests, use `docker-compose` in `tests/docker/install`. Note: any logs of interest should be output before container teardown. The tests export traces to staging and production platforms the same way as the Github Actions do -- see above section.

Example setup and run of local install tests, default `MODE=local`:
```
./run_docker_dev.sh
make clean
make package
exit
cd tests/docker/install
docker-compose up
```

Example setup and run of local install tests, only for Python 3.8 in Alpine 3.14:
```
./run_docker_dev.sh
make clean
make package
exit
cd tests/docker/install
docker-compose run --rm py3.8-install-alpine3.14
```

Example run of install tests from TestPyPI using agent version 0.0.3.2:
```
export SOLARWINDS_APM_VERSION=0.0.3.2
cd tests/docker/install
MODE=testpypi docker-compose up
```

Agent installation tests are also run using the GitHub workflow [Verify Installation](https://github.com/solarwindscloud/solarwinds-apm-python/actions/workflows/verify_install.yaml). These run by installing `solarwinds-apm` published on PyPI, PackageCloud, or TestPyPI.

### Formatting and Linting

Code formatting and linting are run using `black`, `isort`, `flake8`, and `pylint` via [tox](https://tox.readthedocs.io). First, create and run the Docker build container as described above. Then use the container to run formatting and linting in one of these ways:

```
# Run formatting and linting tools,
# without trying to fix issues:
./run_docker_dev.sh
make tox OPTIONS="-e lint -- --check-only"

# Run formatting and linting tools,
# and automatically fix issues if possible:
./run_docker_dev.sh
make tox OPTIONS="-e lint"
```

Remotely, CodeQL can be run on GitHub with the [CodeQL Analysis](https://github.com/solarwindscloud/solarwinds-apm-python/actions/workflows/codeql_analysis.yaml) workflow.


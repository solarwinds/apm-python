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

### Install locally and instrument a test app

TODO

### Install tests

`tests/docker/install` can be used to test agent installation from sdist and wheel (if applicable, i.e. no wheels on Alpine). Part of this test workflow is the launch of minimal, instrumented Flask apps and submitting requests to them. This checks that the installed agent can connect to the collector.

1. Create and run the Docker build container as described above.
2. Inside the build container: `make wrapper`. This downloads the version of oboe defined in `extension/VERSION` from SolarWinds Cloud and builds the SWIG bindings.
3. Next: `make package`. This generates sdist and wheels used for install testing.
4. Exit the build container with `exit`.
5. `cd tests/docker/install`
6. Check `tests/docker/install/docker-compose.yml` for which containers are available to run install tests, for a particular Linux distro and Python version. Some examples:

```
docker-compose up py3.7-install-debian9
docker-compose up py3.10-install-ubuntu20.04
```

Optionally, you can set `MODE` (defaults to `local`). When `MODE=local`, the sdist and wheel must be pre-built by the build container (i.e. `run_docker.dev.sh`, `make package`). For all other modes (`MODE=testpypi`, `MODE=packagecloud`, `MODE=pypi`), the tests pull the agent from one of the public registries so local builds aren't needed.

You can also set `SOLARWINDS_APM_VERSION`. This determines the version of distribution installed. If `MODE=local` or not set, the tests will fail if no source distribution or compatible wheel can be found under `dist/` or in the registries. If `SOLARWINDS_APM_VERSION` is not set, the version as specified by the source code currently checked out will be assumed.

Agent installation tests are also run using the GitHub workflow [Verify Installation](https://github.com/solarwindscloud/solarwinds-apm-python/actions/workflows/verify_install.yaml).

#### Checking exported traces

If you have access to SWO, traces and metrics can be generated by the install tests and exported to the platform. To set up, you'll need the API tokens named `apm-python-install-testing` for one or more of:
* SolarWinds staging
* SolarWinds production
* AppOptics production

Set these and the staging/prod collector endpoints as environment variables:
```
export SW_APM_COLLECTOR_AO_PROD=collector.appoptics.com
export SW_APM_COLLECTOR_PROD=apm.collector.cloud.solarwinds.com
export SW_APM_COLLECTOR_STAGING=apm.collector.st-ssp.solarwinds.com
export SW_APM_SERVICE_KEY_AO_PROD=<api_token>:apm-python-install-testing
export SW_APM_SERVICE_KEY_PROD=<api_token>:apm-python-install-testing
export SW_APM_SERVICE_KEY_STAGING=<api_token>:apm-python-install-testing
```


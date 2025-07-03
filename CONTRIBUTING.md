# Contributing to Python solarwinds-apm

Thank you for contributing and helping us improve Python `solarwinds-apm`.

----

## Issues

### Security issues

Please report any security issues privately to the SolarWinds Product Security Incident Response Team (PSIRT) at [psirt@solarwinds.com](mailto:psirt@solarwinds.com).

### All other issues

For non-security issues, please submit your ideas, questions, or problems as [GitHub issues](https://github.com/solarwinds/apm-python/issues). Please add as much information as you can, such as: Python version, platform, installed dependencies and their version numbers, hosting, code examples or gists, steps to reproduce, stack traces, and logs. SolarWinds project maintainers may ask for clarification or more context after submission.

----
## Contributing

Any changes to this project must be made through a pull request to `main`. Major changes should be linked to an existing [GitHub issue](https://github.com/solarwinds/apm-python/issues). Smaller contributions like typo corrections don't require an issue.

A PR is ready to merge when all tests pass, any major feedback has been resolved, and at least one SolarWinds maintainer has approved. Once ready, a PR can be merged by a SolarWinds maintainer.

----
## Development

### Prerequisites

* docker
* docker-compose

### Build Containers

The build containers are based on the [PyPA image](https://github.com/pypa/manylinux) for `manylinux_2_28_x86_64` or `manylinux_2_28_aarch64`. Choose what will run best on your setup (e.g. aarch64 for Apple silicon, or x86_64 for Intel).

To create and run a Docker container for testing and builds, run one of the following:
```bash
docker-compose run x86_64
```

```bash
docker-compose run aarch64
```

### Regression Tests

Automated testing of this repo uses [tox](https://tox.readthedocs.io) and runs in Python 3.9, 3.10, 3.11 and/or 3.12 because these are the versions supported by [OTel Python](https://github.com/open-telemetry/opentelemetry-python/blob/main/tox.ini). Testing can be run inside a build container which provides all dependencies. Here is how to set up then run unit and integration tests locally:

1. Create and run a Docker build container as described above.
2. To run all tests for a specific version, provide tox options as a string. For example, to run in Python 3.9: `make tox OPTIONS="-e py39-test"`.
3. (WARNING: slow!) To run all tests for all supported Python environments, as well as linting and formatting: `make tox`

Other regular `tox` arguments can be included in `OPTIONS`. Some examples:

```
# Recreate tox environment for Python 3.9 tests
make tox OPTIONS="--recreate -e py39-test"

# Run only the Scenario 8 integration test, in all environments
make tox OPTIONS="-- tests/integration/test_scenario_1.py"
```

The unit and integration tests are also run on GitHub with the [Run tox tests](https://github.com/solarwinds/apm-python/actions/workflows/run_tox_tests.yaml) workflow.

### Formatting and Linting

Code formatting and linting are run using `black`, `isort`, `flake8`, and `pylint` via [tox](https://tox.readthedocs.io). First, create and run a Docker build container as described above. Then use the container to run formatting and linting in one of these ways:

```
# Run formatting and linting tools for Python 3.12,
# without trying to fix issues:
./run_docker_dev.sh
make tox OPTIONS="-e py312-lint -- --check-only"

# Run formatting and linting tools for Python 3.9,
# and automatically fix issues if possible:
./run_docker_dev.sh
make tox OPTIONS="-e py39-lint"
```

Remotely, CodeQL can be run on GitHub with the [CodeQL Analysis](https://github.com/solarwinds/apm-python/actions/workflows/codeql_analysis.yaml) workflow.

### Install locally and instrument a test app

`solarwinds-apm` can be installed and used to instrument a Python app running on your local:

1. Create and run a Docker build container as described above.
2. In your Python app's environment/container, install your local `solarwinds-apm`. For example, if you've saved it to `~/gitrepos` then you could do:
  ```pip install -Ie ~/gitrepos/apm-python/```
3. Install all relevant Opentelemetry Python instrumentation libraries:
  ```opentelemetry-bootstrap --action=install```
4. Run your application with the prefix `opentelemetry-instrument` to wrap all common Python frameworks:
    ```opentelemetry-instrument <command_to_run_your_service>```

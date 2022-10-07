# Contributing to solarwinds_apm
----

## Development

### Prerequisites

* Docker

### Git Repos and Directory Structure

The following is highly recommended for development work on SolarWinds APM.

This repo can be used to auto-instrument [testbed apps](https://github.com/appoptics/solarwinds-apm-python-testbed) for manual testing and exploring. The code in this repository uses code in [solarwinds-apm-liboboe](https://github.com/librato/solarwinds-apm-liboboe) via C-extension with SWIG (see further below). Setup of the oboe extension is done by downloading oboe from SolarWinds Cloud OR with local oboe code.

To accommodate these dependencies locally, clone the following repositories into the same root directory. For example, if your development directory is `~/gitrepos/`, please clone `solarwinds-apm-liboboe`, `solarwinds-apm-python-testbed`, and `solarwinds-apm-python` repositories under `~/gitrepos`, so that your directory structure looks as shown below:
```
~/gitrepos/
|
|----solarwinds-apm-liboboe/
|
|----solarwinds-apm-python-testbed/
|
|----solarwinds-apm-python/
```
### Build Container

To create and run the Docker container which provides all necessary build tools, run the following command:
```bash
docker build -t dev-container .
./run_docker_dev.sh
```

The successfully-built build container is based on the [PyPA image](https://github.com/pypa/manylinux) `manylinux2014_x86_64`. It can use [SWIG](https://www.swig.org/Doc1.3/Python.html), a tool to connect C/C++ libraries with other languages via compiling a C-extension. This can be done with this repo's `Makefile` as described next.

#### Install Agent in Development Mode

##### (A) oboe SolarWinds Cloud download

If you don't need to make changes to oboe:

1. Inside the build container: `make wrapper`. This downloads the version of oboe defined in `extension/VERSION` from SolarWinds Cloud and builds the SWIG bindings.
2. Install the agent in your application (Linux environment only) in development mode by running
   ```python
   pip install -Ie ~/gitrepos/solarwinds-apm-python/
   ```
When installing the agent in development mode, every change in the Python source code will be reflected in the Python environment directly without re-installation.

##### (B) local oboe build

If you are making local changes to oboe for the custom-distro to use:

1. Go to `solarwinds-apm-liboboe/liboboe` repo, save your changes.
2. Run this container: `docker run -it --rm -v "$PWD"/../:/solarwinds-apm-oboe tracetools/clib-amazonlinux-build bash`
3. Inside the container: `INSTALL_DEPS=aws solarwinds-apm-liboboe/liboboe/build-scripts/c-lib.sh`
4. In another Terminal at `solarwinds-apm-liboboe/liboboe` while container is still running, after `c-lib.sh` is done: `docker cp <container_id>:/liboboe-1.0-x86_64.so.0.0.0 .`
5. Return to this repo.
6. Inside the build container: `make wrapper-from-local`. This copies the local C-extension artifacts and builds the SWIG bindings.
7. Install the agent in your application (Linux environment only) in development mode by running
   ```python
   pip install -Ie ~/gitrepos/solarwinds-apm-python/
   ```
Like (A) above, when installing the agent in development mode, every change in the Python source code will be reflected in the Python environment directly without re-installation. _However_, if changes have been made to the C-extension files, you need to reinstall the agent to reflect these changes in the Python environment.

#### Build Agent Source Distribution Archive

The `manylinux` build container can be used to generate a zipped archive source distribution (sdist), a wheel / build distribution (bdist), or both (package distribution). For prereleases, the container can be used to upload a package to SolarWinds PackageCloud.

For more information, run `make` inside the build container.

### Regression Tests

#### Unit tests

Automated unit testing of this repo uses [tox](https://tox.readthedocs.io) and runs in Python 3.7, 3.8, 3.9, and/or 3.10 because these are the versions supported by [OTel Python](https://github.com/open-telemetry/opentelemetry-python/blob/main/tox.ini). Tests for each Python version can be run against AO prod or NH staging.

The functional tests require a compiled C-extension and should be run inside the build container. Here is how to run tests:

1. For each backend you'll be running against, obtain an agent token to replace the appropriate `<AGENT_TOKEN>` in `tox.ini`.
2. _If running against AO prod:_ You'll need to obtain a certificate and save it to `{thisrepo}/tmp/solarwinds-apm/grpc-ao-prod.crt`. 
3. Create and run the Docker build container as described above.
4. Inside the build container: `make wrapper`. This downloads the version of oboe defined in `extension/VERSION` from SolarWinds Cloud and builds the SWIG bindings.
5. To run all tests for a specific version, provide tox options as a string. For example, to run in Python 3.7 against AO prod: `make tox OPTIONS="-e py37-ao-prod"`.
6. (WARNING: slow!) To run all tests for all supported Python environments: `make tox`

#### Integration tests

TODO

### Install tests

#### GitHub Action

Agent installation tests are run using the GitHub workflow [Verify Installation](https://github.com/appoptics/solarwinds-apm-python/actions/workflows/verify_install.yaml). Select one of PyPI, PackageCloud, or TestPyPI from which the tests will download and install. Input Solarwinds APM version is optional (defaults to latest published).

Part of this test workflow is the launch of minimal, instrumented Flask apps and submitting requests to them. This checks that the installed agent can connect to the collector, and traces can be generated and exported to SolarWinds. Installation test-dedicated services on SolarWinds staging (org: Staging), SolarWinds production (org: SWI), and AppOptics production (org: Agent Testing) are named `apm-python-install-testing-<python_version>-<linux_distro>` (e.g. `apm-python-install-testing-py3.7-debian10`). Traces exported there can be inspected manually after GH workflow trigger.

#### Locally

During development, `tests/docker/install` can be used to test agent installation from sdist and wheel (if applicable, i.e. no wheels on Alpine).

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

### Formatting and Linting

TODO

1. Create and run the Docker build container as described above.
2. `make format`
3. `make lint`

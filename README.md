# opentelemetry-python-instrumentation-custom-distro
SolarWinds APM custom distro for OpenTelemetry Python compatibility with SolarWinds Observability backend.

----

## Installation

TODO: `pypi` image

TODO: `pip install solarwinds_apm`

----
## Development

### Prerequisites

* Docker

### Git Repos and Directory Structure

The following is highly recommended for development work on SolarWinds APM.

This repo can be used to auto-instrument [testbed apps](https://github.com/appoptics/opentelemetry-python-testbed) for manual testing and exploring. The code in this repository uses code in [oboe](https://github.com/librato/oboe) via C-extension with SWIG (see further below). Setup of the oboe extension is done by downloading oboe from S3 OR with local oboe code.

To accommodate these dependencies locally, clone the following repositories into the same root directory. For example, if your development directory is `~/gitrepos/`, please clone `oboe`, `opentelemetry-python-testbed`, and `opentelemetry-python-instrumentation-custom-distro` repositories under `~/gitrepos`, so that your directory structure looks as shown below:
```
~/gitrepos/
|
|----oboe/
|
|----opentelemetry-python-testbed/
|
|----opentelemetry-python-instrumentation-custom-distro/
```
### Build Container

To create and run the Docker container which provides all necessary build tools, run the following command:
```bash
docker build -t dev-container .
./run_docker_dev.sh
```

The successfully-built build container can use [SWIG](https://www.swig.org/Doc1.3/Python.html), a tool to connect C/C++ libraries with other languages via compiling a C-extension. This can be done with this repo's `Makefile` as described next.

#### Install Agent in Development Mode

##### (A) oboe S3 download

If you don't need to make changes to oboe:

1. Inside the build container: `make wrapper`. This downloads the version of oboe defined in `extension/VERSION` from S3 and builds the SWIG bindings.
2. Install the agent in your application (Linux environment only) in development mode by running
   ```python
   pip install -Ie ~/gitrepos/opentelemetry-python-instrumentation-custom-distro/
   ```
When installing the agent in development mode, every change in the Python source code will be reflected in the Python environment directly without re-installation.

##### (B) local oboe build

If you are making local changes to oboe for the custom-distro to use:

1. Go to `oboe/liboboe` repo, save your changes.
2. Run this container: `docker run -it --rm -v "$PWD"/../:/oboe tracetools/clib-amazonlinux-build bash`
3. Inside the container: `INSTALL_DEPS=aws oboe/liboboe/build-scripts/c-lib.sh`
4. In another Terminal at `oboe/liboboe` while container is still running, after `c-lib.sh` is done: `docker cp <container_id>:/liboboe-1.0-x86_64.so.0.0.0 .`
5. Return to this repo.
6. Inside the build container: `make wrapper-from-local`. This copies the local C-extension artifacts and builds the SWIG bindings.
7. Install the agent in your application (Linux environment only) in development mode by running
   ```python
   pip install -Ie ~/gitrepos/opentelemetry-python-instrumentation-custom-distro/
   ```
Like (A) above, when installing the agent in development mode, every change in the Python source code will be reflected in the Python environment directly without re-installation. _However_, if changes have been made to the C-extension files, you need to reinstall the agent to reflect these changes in the Python environment.

#### Build Agent Source Distribution Archive
Inside the build container, execute `make sdist`. This will create a zip archive (source distribution) of the Python module under the `dist` directory.

### Regression Tests

Automated testing of this repo uses [tox](https://tox.readthedocs.io) and runs in Python 3.6, 3.7, 3.8, 3.9, and/or 3.10 because these are the versions supported by [OTel Python](https://github.com/open-telemetry/opentelemetry-python/blob/main/tox.ini).

The functional tests require a compiled C-extension and should be run inside the build container. Here is how to run tests:

1. Create and run the Docker build container as described above.
2. Inside the build container: `make wrapper`. This downloads the version of oboe defined in `extension/VERSION` from S3 and builds the SWIG bindings.
3. To run all tests for all Python environments: `make test-all`
4. To run all tests for a specific version, example: `make test PY=py39 OPTIONS="-- -s"`. If `PY` is not provided, `py36` is used by default. `OPTIONS` are optional.

### Formatting and Linting

TODO

1. Create and run the Docker build container as described above.
2. `make format`
3. `make lint`

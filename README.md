# opentelemetry-python-instrumentation-custom-distro
The custom distro to extend the OpenTelemetry Python agent for compatibility with AO


## Prerequisites

### Git Repos and Directory Structure

The code in this repository makes use of code located in the [otel-oboe](https://github.com/librato/otel-oboe) GIT repository. Thus, first make sure that you clone the following repositories into the same root directory. For example, if your development directory is `~/gitrepos/`, please clone the `otel-oboe` and the `opentelemetry-python-instrumentation-custom-distro` repositories under `~/gitrepos`, so that your directory structure looks as shown below:
```
~/gitrepos/
|
|----otel-oboe/
|
|----opentelemetry-python-instrumentation-custom-distro/
```

### Development (Build) Container

In order to compile the C-extension which is part of this Python module, SWIG needs to be installed. This repository provides a Linux-based Dockerfile which can be used to create a Docker image in which the C-extension can be build easily.

To build the Docker image which provides all necessary build tools, run the following command inside the `dev_tools` directory:
```bash
docker build -t dev-container .
```

Then you can start a build container by running `./run_docker_dev.sh` from within the `dev_tools` location. This will provide you with a docker container which has all volumes mapped as required so you can easily build the agent.

## How to Build and Install the Agent
* Switch into the build container by running
    ```bash
    ./run_docker_dev.sh
   ```
  from within the `dev_tools` directory.
* Inside the docker container, you can now build the agent with the provided Makefile.

### Install Agent from Source in Development Mode
* Execute `make wrapper` inside the build container. This copies the C-extension artifacts and builds the SWIG bindings.
* Install the agent in your application (Linux environment only) in development mode by running
   ```python
   pip install -Ie ~/gitrepos/opentelemetry-python-instrumentation-custom-distro/
   ```
When installing the agent in development mode every change in the Python source code will be reflected in the Python environment directly without re-installation. However, if changes have been made to the C-extension files, you need to reinstall the agent (as described above) to reflect these changes in the Python environment.

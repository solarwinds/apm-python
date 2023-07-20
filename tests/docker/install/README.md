# Installation tests

These files provide containers and scripts to test installation of packaged `solarwinds-apm-python`, from local or from registry. Here is how to set up and run install tests locally:

1. Set test mode to install from one of:
   * `export MODE=local` (default; must be built in project `dist/`)
   * `export MODE=testpypi`
   * `export MODE=pypi`
2. Optionally set the APM library version to install, e.g. `export SOLARWINDS_APM_VERSION=0.6.0`. If not provided, the install tests will use what's set in `version.py` (local) or the latest version (registry).
3. Set these additional environment variables, required to create and export test traces:
   * `SW_APM_COLLECTOR_PROD`
   * `SW_APM_COLLECTOR_STAGING`
   * `SW_APM_COLLECTOR_AO`
   * `SW_APM_SERVICE_KEY_PROD`
   * `SW_APM_SERVICE_KEY_STAGING`
   * `SW_APM_SERVICE_KEY_AO`
4. Run one of the containers interactively, with service name specified in `docker-compose.yml`:
   * For Debian/CentOS/Amazon/Fedora: `docker-compose run --rm <service_name> /bin/bash`
   * For Alpine: `docker-compose run --rm <service_name> /bin/sh`
5. `./_helper_run_install_tests.sh`

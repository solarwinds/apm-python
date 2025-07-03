[![PyPI version](https://badge.fury.io/py/solarwinds-apm.svg)](https://badge.fury.io/py/solarwinds-apm) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/solarwinds-apm) [![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?color=red)](https://github.com/solarwinds/apm-python/blob/main/LICENSE)

# Python solarwinds-apm
An [OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/) distribution for SolarWinds Observability. Provides automatic configuration, instrumentation, and APM data export for Python applications.

----
## Requirements
All published artifacts support Python 3.9 or higher. A full list of system requirements is available at [SolarWinds Observability System Requirements](https://documentation.solarwinds.com/en/success_center/observability/default.htm#cshid=app-sysreqs-python-agent).

See [CONTRIBUTING.md](https://github.com/solarwinds/apm-python/blob/main/CONTRIBUTING.md) for how to build for development.

## Getting Started
SolarWinds APM captures OpenTelemetry distributed traces and metrics from your application and sends them to SolarWinds Observability for analysis and visualization.

To install `solarwinds-apm` and all relevant Opentelemetry Python instrumentation libraries:
```
pip install solarwinds-apm "psutil>=5.0"
opentelemetry-bootstrap --action=install
```
`solarwinds-apm` already includes OpenTelemetry and therefore doesn't need to be installed separately. Python agent installation should be done _after_ installation of all other service dependencies. This is so `opentelemetry-bootstrap` detects those packages and installs their corresponding instrumentation libraries. For example:

```
pip install -r requirements.txt           # installs all other dependencies
pip install solarwinds-apm "psutil>=5.0"
opentelemetry-bootstrap --action=install
```

Set the service key and ingestion endpoint. An easy way to do this is via environment variables available to your application process. An example:

```
export SW_APM_SERVICE_KEY=<set-service-key-here>
export SW_APM_COLLECTOR=<set-collector-here>
```

Run your application with the prefix `opentelemetry-instrument` to wrap all common Python frameworks and start exporting OpenTelemetry traces and metrics:
```
opentelemetry-instrument <command_to_run_your_service>
```

You can also add custom span generation to your code by using the OpenTelemetry SDK. For example:
```
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my_custom_span") as custom_span:
   custom_span.set_attribute("my_custom_attribute", "foo_value")
   print("Here is my custom OpenTelemetry span")
```


## Documentation

OpenTelemetry Python documentation is available at the [OpenTelemetry-Python API Reference](https://opentelemetry-python.readthedocs.io/).

Online documentation for SolarWinds APM Python features, configuration, and more is available at [SolarWinds Observability](https://documentation.solarwinds.com/en/success_center/observability/default.htm#cshid=app-add-python-agent).


## Contributing

OpenTelemetry Python would not be possible without collaborations and efforts from many contributors. Our common goals as a community are to improve end user/developer experiences and empower them.

For more information about contributing to Python `solarwinds-apm`, see [CONTRIBUTING.md](https://github.com/solarwinds/apm-python/blob/main/CONTRIBUTING.md). Thank you to everyone who has contributed:

<a href="https://github.com/solarwinds/apm-python/graphs/contributors">
  <img src="https://contributors-img.web.app/image?repo=solarwinds/apm-python" />
</a>
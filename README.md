# solarwinds_apm
SolarWinds Observability distribution of OpenTelemetry Python, providing automatic instrumentation of Python applications for APM.

----
## Requirements
All published artifacts support Python 3.7 or higher. A full list of system requirements is available at: https://documentation.solarwinds.com/en/success_center/observability/default.htm#cshid=app-sysreqs-python-agent

See [CONTRIBUTING.md](https://github.com/appoptics/solarwinds-apm-python/blob/main/CONTRIBUTING.md) for how to build for development.

## Getting Started
SolarWinds APM captures distributed traces and metrics from your application and sends them to SolarWinds Observability for analysis and visualization.

To install `solarwinds_apm` in your Python service (already includes OpenTelemetry API and SDK):
```
pip install solarwinds-apm
opentelemetry-bootstrap --action=install
```

Run your application with the prefix `opentelemetry-instrument` to wrap all common Python frameworks and start exporting traces and metrics:
```
opentelemetry-instrument <command_to_run_your_service>
```

You can also add custom span generation to your code by using the OpenTelemetry SDK. For example:
```
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my_custom_span"):
   # Do business things
```


## Documentation

Online documentation on SolarWinds APM features, configuration, and more is available at https://documentation.solarwinds.com/en/success_center/observability/default.htm#cshid=app-add-python-agent


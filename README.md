# solarwinds_apm
SolarWinds Observability application performance management library (SWO APM) for Python, providing OpenTelemetry compatibility with the SolarWinds platform.

----
## Requirements
All published artifacts support Python 3.6 or higher. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to build for development.

## Getting Started
SWO APM captures distributed traces and metrics from your application and sends them to the SolarWinds platform for analysis and visualization.

To install `solarwinds_apm` in your Python service (includes OpenTelemetry API and SDK):
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

Online documentation on SWO APM features, configuration, and more is available at: https://www.appoptics.com/monitor/python-performance

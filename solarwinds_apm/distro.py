"""Module to configure OpenTelemetry to work with SolarWinds backend"""

from os import environ

from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)
from opentelemetry.instrumentation.distro import BaseDistro

from solarwinds_apm import (
    DEFAULT_SW_TRACES_EXPORTER,
    DEFAULT_SW_PROPAGATORS
) 


class SolarWindsDistro(BaseDistro):
    """OpenTelemetry Distro for SolarWinds reporting environment"""

    def _configure(self, **kwargs):
        """Configure default OTel exporter and propagators"""
        environ.setdefault(OTEL_TRACES_EXPORTER, DEFAULT_SW_TRACES_EXPORTER)
        environ.setdefault(OTEL_PROPAGATORS, ",".join(DEFAULT_SW_PROPAGATORS))

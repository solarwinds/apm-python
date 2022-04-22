"""Module to configure OpenTelemetry to work with SolarWinds backend"""

import logging
from os import environ

from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.sdk.environment_variables import OTEL_TRACES_SAMPLER

logger = logging.getLogger(__name__)

class SolarWindsDistro(BaseDistro):
    """OpenTelemetry Distro for SolarWinds reporting environment"""

    _DEFAULT_SW_PROPAGATORS = [
        "tracecontext",
        "baggage",
        "solarwinds_propagator",
    ]
    _DEFAULT_SW_TRACES_EXPORTER = "solarwinds_exporter"
    _DEFAULT_SW_TRACES_SAMPLER = "solarwinds_sampler"

    def _configure(self, **kwargs):
        environ.setdefault(OTEL_TRACES_SAMPLER, self._DEFAULT_SW_TRACES_SAMPLER)
        environ.setdefault(OTEL_TRACES_EXPORTER, self._DEFAULT_SW_TRACES_EXPORTER)
        
        # Configure context propagators to always include
        # tracecontext,baggage,solarwinds -- first and in that order
        # -- plus any others specified by env var
        environ_propagators = environ.get(
            OTEL_PROPAGATORS,
            ",".join(self._DEFAULT_SW_PROPAGATORS)
        ).split(",")
        if environ_propagators != self._DEFAULT_SW_PROPAGATORS:
            for default in self._DEFAULT_SW_PROPAGATORS:
                while default in environ_propagators:
                    environ_propagators.remove(default)
            environ_propagators = self._DEFAULT_SW_PROPAGATORS + environ_propagators
        environ[OTEL_PROPAGATORS] = ",".join(environ_propagators)

        logger.debug("Configured SolarWindsDistro: {}, {}, {}".format(
            environ.get(OTEL_TRACES_SAMPLER),
            environ.get(OTEL_TRACES_EXPORTER),
            environ.get(OTEL_PROPAGATORS)
        ))
    
    @classmethod
    def default_sw_traces_sampler(cls):
        return cls._DEFAULT_SW_TRACES_SAMPLER

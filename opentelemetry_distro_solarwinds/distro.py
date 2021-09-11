"""Module to configure OpenTelemetry agent to work with SolarWinds backend"""

from opentelemetry import trace
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry_distro_solarwinds.exporter import SolarWindsSpanExporter
from opentelemetry_distro_solarwinds.sampler import ParentBasedAoSampler


class SolarWindsDistro(BaseDistro):
    """SolarWinds custom distro for OpenTelemetry agents.

    With this custom distro, the following functionality is introduced:
        - no functionality added at this time
    """
    def _configure(self, **kwargs):
        # automatically make use of custom SolarWinds sampler
        trace.set_tracer_provider(
            TracerProvider(sampler=ParentBasedAoSampler()))
        # Automatically configure the SolarWinds Span exporter
        span_exporter = BatchSpanProcessor(SolarWindsSpanExporter())
        trace.get_tracer_provider().add_span_processor(span_exporter)

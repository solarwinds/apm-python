# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

"""SolarWinds TracerProvider with custom shutdown behavior."""

from opentelemetry.sdk.trace import TracerProvider
from typing_extensions import override

from solarwinds_apm.oboe.http_sampler import HttpSampler


class SolarwindsTracerProvider(TracerProvider):
    """Provide custom TracerProvider with HttpSampler shutdown support.

    Extends OpenTelemetry TracerProvider to properly shutdown HttpSampler.
    """

    @override
    def shutdown(self) -> None:
        """
        Shutdown the tracer provider and its sampler.

        Ensures HttpSampler daemon thread is properly terminated before parent shutdown.
        """
        if isinstance(self.sampler, HttpSampler):
            self.sampler.shutdown()
        super().shutdown()

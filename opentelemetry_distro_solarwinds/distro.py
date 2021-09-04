"""Module to configure OpenTelemetry agent to work with SolarWinds backend"""

from opentelemetry.instrumentation.distro import BaseDistro


class AoDistro(BaseDistro):
    """SolarWinds custom distro for OpenTelemetry agents.

    With this custom distro, the following functionality is introduced:
        - no functionality added at this time
    """
    def _configure(self, **kwargs):
        pass

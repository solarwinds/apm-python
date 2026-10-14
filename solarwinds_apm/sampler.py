# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

"""This module provides a SolarWinds-specific sampler.

The custom sampler will fetch sampling configurations for the SolarWinds backend.
"""

# TODO: Remove when Python < 3.10 support dropped
from __future__ import annotations

from opentelemetry.metrics import get_meter_provider
from opentelemetry.sdk.trace.sampling import ParentBased

from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.oboe.http_sampler import HttpSampler
from solarwinds_apm.oboe.json_sampler import JsonSampler


class ParentBasedSwSampler(ParentBased):
    """Respect parent span's sampling decision or use SolarWinds backend configuration.

    Requires SolarWindsApmConfig.
    """

    def __init__(
        self,
        apm_config: SolarWindsApmConfig,
    ) -> None:
        """
        Initialize ParentBasedSwSampler with SolarWinds APM configuration.

        Uses HttpSampler for non-Lambda environments or JsonSampler for Lambda.
        Uses HttpSampler/JsonSampler if no parent span.
        Uses HttpSampler/JsonSampler if parent span is_remote.
        Uses OpenTelemetry defaults if parent span is_local.

        Parameters:
        apm_config (SolarWindsApmConfig): The SolarWinds APM configuration.
        """
        configuration = SolarWindsApmConfig.to_configuration(apm_config)
        self.sampler = None
        if apm_config.is_lambda:
            self.sampler = JsonSampler(
                meter_provider=get_meter_provider(), config=configuration
            )
        else:
            self.sampler = HttpSampler(
                meter_provider=get_meter_provider(),
                config=configuration,
                initial=None,
            )
        super().__init__(
            root=self.sampler,
            remote_parent_sampled=self.sampler,
            remote_parent_not_sampled=self.sampler,
        )

    # should_sample defined by ParentBased

    def wait_until_ready(self, timeout: int) -> bool:
        """Wait until the sampler is ready.

        Parameters:
        timeout (int): Maximum time to wait in seconds.

        Returns:
        bool: True if sampler is ready, False if timeout occurred.
        """
        return self.sampler.wait_until_ready(timeout)

# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

from solarwinds_apm.oboe.http_sampler import HttpSampler
from solarwinds_apm.tracer_provider import SolarwindsTracerProvider


def test_shutdown_calls_sampler_shutdown():
    sampler = MagicMock(spec=HttpSampler)
    provider = SolarwindsTracerProvider(sampler=sampler)
    provider.shutdown()
    provider.sampler.shutdown.assert_called_once()

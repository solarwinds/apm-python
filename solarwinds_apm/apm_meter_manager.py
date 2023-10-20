# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging

# pylint:disable=deprecated-typing-alias
from typing import Iterable

from opentelemetry import metrics
from opentelemetry.metrics import CallbackOptions, Observation

from solarwinds_apm.apm_noop import SettingsApi

logger = logging.getLogger(__name__)

# TODO Change when SWIG updated
# TODO Move to Configurator?
oboe_settings_api = SettingsApi()


class SolarWindsMeterManager:
    """SolarWinds Python OTLP Meter Manager"""

    def __init__(self, **kwargs: int) -> None:
        # Returns a named `Meter` to handle instrument creation.
        # A convenience wrapper for MeterProvider.get_meter
        self.meter = metrics.get_meter("sw.apm.sampling.metrics")

        self.response_time = self.meter.create_histogram(
            name="trace.service.response_time",
            description="measures the duration of an inbound HTTP request",
            unit="ms",
        )

        # TypeError: 'ABCMeta' object is not subscriptable
        # with old import for this signature, with current Otel API
        def request_counter_func(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            status, trace_count = oboe_settings_api.consumeRequestCount()
            yield Observation(trace_count, {"status": status})

        self.request_counter = self.meter.create_observable_gauge(
            # TODO: This is just a test
            name="test.python.swig.request_counter",
            callbacks=[request_counter_func],
        )

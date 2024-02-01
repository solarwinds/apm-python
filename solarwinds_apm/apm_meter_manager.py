# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging

# TypeError: 'ABCMeta' object is not subscriptable
# with this old import for callback signatures, with current Otel API
# pylint:disable=deprecated-typing-alias
from typing import TYPE_CHECKING, Iterable

from opentelemetry.metrics import CallbackOptions, Observation, get_meter

if TYPE_CHECKING:
    from solarwinds_apm.apm_config import SolarWindsApmConfig
    from solarwinds_apm.extension.oboe import OboeAPI

logger = logging.getLogger(__name__)


class SolarWindsMeterManager:
    """SolarWinds Python OTLP Meter Manager"""

    def __init__(
        self,
        apm_config: "SolarWindsApmConfig",
        oboe_api: "OboeAPI",
        **kwargs: int,
    ) -> None:
        self.oboe_settings_api = oboe_api

        # Returns named `Meter` to handle instrument creation.
        # A convenience wrapper for MeterProvider.get_meter
        self.meter_response_times = get_meter("sw.apm.request.metrics")
        self.meter_request_counters = get_meter("sw.apm.sampling.metrics")

        self.response_time = self.meter_response_times.create_histogram(
            name="trace.service.response_time",
            description="measures the duration of an inbound HTTP request",
            unit="ms",
        )

        def consume_tracecount(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            status, trace_count = self.oboe_settings_api.consumeTraceCount()
            yield Observation(trace_count, {"status": status})

        self.tracecount = self.meter_request_counters.create_observable_gauge(
            name="trace.service.tracecount",
            callbacks=[consume_tracecount],
        )

        def consume_samplecount(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            status, sample_count = self.oboe_settings_api.consumeSampleCount()
            yield Observation(sample_count, {"status": status})

        self.samplecount = self.meter_request_counters.create_observable_gauge(
            name="trace.service.samplecount",
            callbacks=[consume_samplecount],
        )

        def consume_request_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            status, request_count = (
                self.oboe_settings_api.consumeRequestCount()
            )
            yield Observation(request_count, {"status": status})

        self.request_count = (
            self.meter_request_counters.create_observable_gauge(
                name="trace.service.request_count",
                callbacks=[consume_request_count],
            )
        )

        def consume_tokenbucket_exhaustion_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            (
                status,
                tokenbucket_exh_count,
            ) = self.oboe_settings_api.consumeTokenBucketExhaustionCount()
            yield Observation(tokenbucket_exh_count, {"status": status})

        self.tokenbucket_exhaustion_count = (
            self.meter_request_counters.create_observable_gauge(
                name="trace.service.tokenbucket_exhaustion_count",
                callbacks=[consume_tokenbucket_exhaustion_count],
            )
        )

        def consume_through_trace_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            (
                status,
                through_trace_count,
            ) = self.oboe_settings_api.consumeThroughTraceCount()
            yield Observation(through_trace_count, {"status": status})

        self.through_trace_count = (
            self.meter_request_counters.create_observable_gauge(
                name="trace.service.through_trace_count",
                callbacks=[consume_through_trace_count],
            )
        )

        def consume_triggered_trace_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            (
                status,
                tt_count,
            ) = self.oboe_settings_api.consumeTriggeredTraceCount()
            yield Observation(tt_count, {"status": status})

        self.triggered_trace_count = (
            self.meter_request_counters.create_observable_gauge(
                name="trace.service.triggered_trace_count",
                callbacks=[consume_triggered_trace_count],
            )
        )

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

from opentelemetry import metrics
from opentelemetry.metrics import CallbackOptions, Observation

from solarwinds_apm.apm_constants import INTL_SWO_SUPPORT_EMAIL

if TYPE_CHECKING:
    from solarwinds_apm.apm_config import SolarWindsApmConfig

logger = logging.getLogger(__name__)


class SolarWindsMeterManager:
    """SolarWinds Python OTLP Meter Manager"""

    def __init__(
        self, apm_config: "SolarWindsApmConfig", **kwargs: int
    ) -> None:
         # Returns named `Meter` to handle instrument creation.
        # A convenience wrapper for MeterProvider.get_meter
        self.meter_response_times = metrics.get_meter("sw.apm.request.metrics")
        self.meter_request_counters = metrics.get_meter("sw.apm.sampling.metrics")

        # TODO need a better condition
        # TODO move this init to Configurator?
        if apm_config.agent_enabled and apm_config.is_lambda:
            try:
                # pylint: disable=import-outside-toplevel
                import solarwinds_apm.extension.oboe as c_extension
            except ImportError as err:
                # At this point, if agent_enabled but cannot import
                # extension then something unexpected happened
                logger.error(
                    "Could not import extension for settings API. Please contact %s. Tracing disabled: %s",
                    INTL_SWO_SUPPORT_EMAIL,
                    err,
                )
                # pylint: disable=import-outside-toplevel
                import solarwinds_apm.apm_noop as c_extension
        else:
            # pylint: disable-next=import-outside-toplevel
            import solarwinds_apm.apm_noop as c_extension

        self.oboe_settings_api = c_extension.OboeAPI()

        self.response_time = self.meter_response_times.create_histogram(
            name="trace.service.response_time",
            description="measures the duration of an inbound HTTP request",
            unit="ms",
        )

        def request_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            status, trace_count = self.oboe_settings_api.consumeRequestCount()
            yield Observation(trace_count, {"status": status})

        self.request_count = self.meter_request_counters.create_observable_gauge(
            name="trace.service.request_count",
            callbacks=[request_count],
        )

        def token_bucket_exhaustion_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            (
                status,
                trace_count,
            ) = self.oboe_settings_api.consumeTokenBucketExhaustionCount()
            yield Observation(trace_count, {"status": status})

        self.token_bucket_exhaustion_count = (
            self.meter_request_counters.create_observable_gauge(
                name="trace.service.token_bucket_exhaustion_count",
                callbacks=[token_bucket_exhaustion_count],
            )
        )

        def consume_trace_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            status, trace_count = self.oboe_settings_api.consumeTraceCount()
            yield Observation(trace_count, {"status": status})

        self.consume_trace_count = self.meter_request_counters.create_observable_gauge(
            name="trace.service.consume_trace_count",
            callbacks=[consume_trace_count],
        )

        def consume_sample_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            status, trace_count = self.oboe_settings_api.consumeSampleCount()
            yield Observation(trace_count, {"status": status})

        self.consume_sample_count = self.meter_request_counters.create_observable_gauge(
            name="trace.service.consume_sample_count",
            callbacks=[consume_sample_count],
        )

        def consume_through_trace_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            (
                status,
                trace_count,
            ) = self.oboe_settings_api.consumeThroughTraceCount()
            yield Observation(trace_count, {"status": status})

        self.consume_through_trace_count = self.meter_request_counters.create_observable_gauge(
            name="trace.service.consume_through_trace_count",
            callbacks=[consume_through_trace_count],
        )

        def consume_triggered_trace_count(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            (
                status,
                trace_count,
            ) = self.oboe_settings_api.consumeTriggeredTraceCount()
            yield Observation(trace_count, {"status": status})

        self.consume_triggered_trace_count = (
            self.meter_request_counters.create_observable_gauge(
                name="trace.service.consume_triggered_trace_count",
                callbacks=[consume_triggered_trace_count],
            )
        )

        def get_last_used_sample_rate(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            (
                status,
                trace_count,
            ) = self.oboe_settings_api.getLastUsedSampleRate()
            yield Observation(trace_count, {"status": status})

        self.get_last_used_sample_rate = self.meter_request_counters.create_observable_gauge(
            name="trace.service.sample_rate",
            callbacks=[get_last_used_sample_rate],
        )

        def get_last_used_sample_source(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            (
                status,
                trace_count,
            ) = self.oboe_settings_api.getLastUsedSampleSource()
            yield Observation(trace_count, {"status": status})

        self.get_last_used_sample_source = self.meter_request_counters.create_observable_gauge(
            name="trace.service.sample_source",
            callbacks=[get_last_used_sample_source],
        )

# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from opentelemetry.sdk.metrics import MeterProvider


class Counters:
    def __init__(self, meter_provider: MeterProvider):
        self._meter = meter_provider.get_meter("sw.apm.sampling.metrics")
        self._request_count = self._meter.create_counter(
            name="trace.service.request_count",
            description="Count of all requests.",
            unit="{request}",
        )
        self._sample_count = self._meter.create_counter(
            name="trace.service.samplecount",
            description="Count of requests that went through sampling, which excludes those with a valid upstream decision or trigger traced.",
            unit="{request}",
        )
        self._trace_count = self._meter.create_counter(
            name="trace.service.tracecount",
            description="Count of all traces.",
            unit="{trace}",
        )
        self._through_trace_count = self._meter.create_counter(
            name="trace.service.through_trace_count",
            description="Count of requests with a valid upstream decision, thus passed through sampling.",
            unit="{request}",
        )
        self._triggered_trace_count = self._meter.create_counter(
            name="trace.service.triggered_trace_count",
            description="Count of triggered traces.",
            unit="{trace}",
        )
        self._token_bucket_exhaustion_count = self._meter.create_counter(
            name="trace.service.tokenbucket_exhaustion_count",
            description="Count of requests that were not traced due to token bucket rate limiting.",
            unit="{request}",
        )

    @property
    def request_count(self):
        return self._request_count

    @property
    def sample_count(self):
        return self._sample_count

    @property
    def trace_count(self):
        return self._trace_count

    @property
    def through_trace_count(self):
        return self._through_trace_count

    @property
    def triggered_trace_count(self):
        return self._triggered_trace_count

    @property
    def token_bucket_exhaustion_count(self):
        return self._token_bucket_exhaustion_count

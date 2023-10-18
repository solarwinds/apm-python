# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging

from opentelemetry import metrics

logger = logging.getLogger(__name__)


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

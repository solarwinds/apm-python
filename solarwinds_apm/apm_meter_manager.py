# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import random

# pylint:disable=deprecated-typing-alias
from typing import Iterable

from opentelemetry import metrics
from opentelemetry.metrics import CallbackOptions, Observation

logger = logging.getLogger(__name__)


class SolarWindsMeterManager:
    """SolarWinds Python OTLP Meter Manager"""

    def __init__(self, **kwargs: int) -> None:
        # Gets the global default meter
        meter = metrics.get_meter(__name__)

        self.response_time = meter.create_histogram(
            name="trace.service.response_time",
            description="measures the duration of an inbound HTTP request",
            unit="ms",
        )

        # TODO: TypeError: 'ABCMeta' object is not subscriptable
        #       with old import for this signature, with current Otel API
        def request_counter_func(
            options: CallbackOptions,
        ) -> Iterable[Observation]:
            # TODO: Use c-lib API to get request count
            yield Observation(random.randint(0, 10), {})

        self.request_counter = meter.create_observable_gauge(
            # TODO: Rename to SWO key
            name="tammy.test.request_counter",
            callbacks=[request_counter_func],
        )

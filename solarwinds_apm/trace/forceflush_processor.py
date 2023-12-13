# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING

from opentelemetry.metrics import get_meter_provider
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import get_tracer_provider

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

logger = logging.getLogger(__name__)


class ForceFlushSpanProcessor(SpanProcessor):
    def on_end(self, span: "ReadableSpan") -> None:
        # Force flush metrics after every entry span via flush of all meters
        # including PeriodicExportingMetricReader
        logger.debug("Performing MeterProvider force_flush of metrics")
        get_meter_provider().force_flush()

        # Force flush spans that have not yet been processed
        logger.debug("Performing TracerProvider force_flush of traces")
        get_tracer_provider().force_flush()

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""
Example usage:

from solarwinds_apm.api import set_transaction_name
set_transaction_name("my-foo-name")
"""

import logging

from opentelemetry.trace import get_current_span, get_tracer_provider

from solarwinds_apm.inbound_metrics_processor import SolarWindsInboundMetricsSpanProcessor

logger = logging.getLogger(__name__)

def set_transaction_name(name: str) -> None:
    # Assumes TracerProvider's active span processor is SynchronousMultiSpanProcessor
    # or ConcurrentMultiSpanProcessor
    span_processors = get_tracer_provider()._active_span_processor._span_processors
    inbound_processor = None
    for spr in span_processors:
        if type(spr) == SolarWindsInboundMetricsSpanProcessor:
            inbound_processor = spr
    
    if not inbound_processor:
        logger.error("Could not find configured InboundMetricsSpanProcessor.")
        return

    current_span = get_current_span()
    trace_id = current_span.get_span_context().trace_id
    inbound_processor._apm_txname_customizer[trace_id] = name
    logger.debug("Cached custom transaction name as %s", name)

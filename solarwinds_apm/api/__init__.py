# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import Any

from opentelemetry import baggage
from opentelemetry.trace import NoOpTracerProvider, get_tracer_provider

from solarwinds_apm.apm_constants import (
    INTL_SWO_CURRENT_SPAN_ID,
    INTL_SWO_CURRENT_TRACE_ID,
)
from solarwinds_apm.apm_oboe_codes import OboeReadyCode

# pylint: disable=import-error,no-name-in-module
from solarwinds_apm.extension.oboe import Context
from solarwinds_apm.inbound_metrics_processor import (
    SolarWindsInboundMetricsSpanProcessor,
)

logger = logging.getLogger(__name__)


def set_transaction_name(custom_name: str) -> bool:
    """
    Assign a custom transaction name to a current request. If multiple
    transaction names are set on the same trace, then the last one is used.
    Overrides default, out-of-the-box naming based on URL/controller/action.

    Any uppercase to lowercase conversions or special character replacements
    are done by the platform. Any truncations are done by the core extension.

    :custom_name:str, custom transaction name to apply

    :return:
    bool True for successful name assignment, False for not

    :Example:
     from solarwinds_apm.api import set_transaction_name
     result = set_transaction_name("my-foo-name")
    """
    if isinstance(get_tracer_provider(), NoOpTracerProvider):
        logger.debug(
            "Cannot cache custom transaction name %s because agent not enabled; ignoring",
            custom_name,
        )
        return True

    # Assumes TracerProvider's active span processor is SynchronousMultiSpanProcessor
    # or ConcurrentMultiSpanProcessor
    span_processors = (
        # pylint: disable=protected-access
        get_tracer_provider()._active_span_processor._span_processors
    )
    inbound_processor = None
    for spr in span_processors:
        if isinstance(spr, SolarWindsInboundMetricsSpanProcessor):
            inbound_processor = spr

    if not inbound_processor:
        logger.error("Could not find configured InboundMetricsSpanProcessor.")
        return False

    entry_trace_id = baggage.get_baggage(INTL_SWO_CURRENT_TRACE_ID)
    entry_span_id = baggage.get_baggage(INTL_SWO_CURRENT_SPAN_ID)
    if not entry_trace_id or not entry_span_id:
        logger.debug(
            "Cannot cache custom transaction name %s because OTel service entry span not started; ignoring",
            custom_name,
        )
        return False
    trace_span_id = f"{entry_trace_id}-{entry_span_id}"
    inbound_processor.apm_txname_manager[trace_span_id] = custom_name
    logger.debug(
        "Cached custom transaction name for %s as %s",
        trace_span_id,
        custom_name,
    )
    return True


def solarwinds_ready(
    wait_milliseconds: int = 3000,
    integer_response: bool = False,
) -> Any:
    """
    Wait for SolarWinds to be ready to send traces.

    This may be useful in short lived background processes when it is important to capture
    information during the whole time the process is running. Usually SolarWinds doesn't block an
    application while it is starting up.

    :param wait_milliseconds:int default 3000, the maximum time to wait in milliseconds
    :param integer_response:bool default False to return boolean value, otherwise True to
    return integer for detailed information

    :return:
    if integer_response:int code 1 for ready; 0,2,3,4,5 for not ready
    else:bool True for ready, False not ready

    :Example:
     from solarwinds_apm.api import solarwinds_ready
     if not solarwinds_ready(wait_milliseconds=10000, integer_response=True):
        Logger.info("SolarWinds not ready after 10 seconds, no metrics will be sent")
    """
    rc = Context.isReady(wait_milliseconds)
    if not isinstance(rc, int) or rc not in OboeReadyCode.code_values():
        logger.warning("Unrecognized return code: %s", rc)
        return (
            OboeReadyCode.OBOE_SERVER_RESPONSE_UNKNOWN
            if integer_response
            else False
        )
    if rc != OboeReadyCode.OBOE_SERVER_RESPONSE_OK[0]:
        logger.warning(OboeReadyCode.code_values()[rc])

    return (
        rc
        if integer_response
        else rc == OboeReadyCode.OBOE_SERVER_RESPONSE_OK[0]
    )

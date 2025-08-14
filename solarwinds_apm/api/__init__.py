# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging

from opentelemetry import context, trace
from opentelemetry.trace import NoOpTracerProvider, get_tracer_provider

from solarwinds_apm.apm_constants import (
    INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN,
    INTL_SWO_TRANSACTION_NAME_ATTR,
)
from solarwinds_apm.oboe import get_transaction_name_pool
from solarwinds_apm.oboe.http_sampler import HttpSampler
from solarwinds_apm.oboe.json_sampler import JsonSampler
from solarwinds_apm.oboe.transaction_name_pool import TRANSACTION_NAME_DEFAULT
from solarwinds_apm.sampler import ParentBasedSwSampler
from solarwinds_apm.tracer_provider import SolarwindsTracerProvider
from solarwinds_apm.w3c_transformer import W3CTransformer

logger = logging.getLogger(__name__)


def set_transaction_name(custom_name: str) -> bool:
    """
    Assign a custom transaction name to a current request. If multiple
    transaction names are set on the same trace, then the last one is used.
    Overrides default, out-of-the-box naming based on URL/controller/action.
    Takes precedence over transaction_name set in environment variable or
    config file.

    Any uppercase to lowercase conversions or special character replacements
    are done by the platform. Name length is limited to 256 characters;
    anything longer is truncated by APM library.

    :custom_name:str, custom transaction name to apply

    :return:
    bool True if successful name assignment or if tracing disabled,
         False if unsuccessful due to invalid name, nonexistent span, or distro error.

    :Example:
     from solarwinds_apm.api import set_transaction_name
     result = set_transaction_name("my-foo-name")
    """
    if not custom_name:
        logger.warning(
            "Cannot set custom transaction name as empty string; ignoring"
        )
        return False

    tracer_provider = get_tracer_provider()
    if isinstance(tracer_provider, NoOpTracerProvider):
        logger.debug(
            "Cannot cache custom transaction name %s because agent not enabled; ignoring",
            custom_name,
        )
        return True

    current_trace_entry_span = context.get_value(
        INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN
    )
    if not current_trace_entry_span:
        logger.warning(
            "Cannot set custom transaction name %s because OTel service entry span not started; ignoring",
            custom_name,
        )
        return False

    logger.debug(
        "Setting attribute %s for span %s as %s",
        INTL_SWO_TRANSACTION_NAME_ATTR,
        W3CTransformer.trace_and_span_id_from_context(
            current_trace_entry_span.context
        ),
        custom_name,
    )

    # check limit pool; set as "other" if reached and log debug/warning
    pool = get_transaction_name_pool()
    registered_name = pool.registered(custom_name)
    if registered_name == TRANSACTION_NAME_DEFAULT:
        logger.warning(
            "Transaction name pool is full; set as %s for span %s",
            TRANSACTION_NAME_DEFAULT,
            W3CTransformer.trace_and_span_id_from_context(
                current_trace_entry_span.context
            ),
        )
    current_trace_entry_span.set_attribute(
        INTL_SWO_TRANSACTION_NAME_ATTR, registered_name
    )
    return True


def solarwinds_ready(
    wait_milliseconds: int = 3000, integer_response: bool = False
) -> bool:
    """
    Wait for SolarWinds to be ready to send traces.

    This may be useful in short-lived background processes when it is important to capture
    information during the whole time the process is running. Usually SolarWinds doesn't block an
    application while it is starting up.

    :param wait_milliseconds:int default 3000, the maximum time to wait in milliseconds
    :param integer_response:bool default False, we are dropping this support, please see updated docs

    :return:
    bool True for ready, False not ready

    :Example:
     from solarwinds_apm.api import solarwinds_ready
     if not solarwinds_ready(wait_milliseconds=10000, integer_response=False):
        Logger.info("SolarWinds not ready after 10 seconds, no metrics will be sent")
    """
    if integer_response:
        logger.warning(
            "support of integer_response is dropped, please see updated docs"
        )

    tracer_provider = trace.get_tracer_provider()
    if isinstance(tracer_provider, SolarwindsTracerProvider):
        if isinstance(
            tracer_provider.sampler,
            (ParentBasedSwSampler, HttpSampler, JsonSampler),
        ):
            return tracer_provider.sampler.wait_until_ready(
                int(wait_milliseconds / 1000)
            )

        logger.debug(
            "SolarWinds not ready because sampler is not a Solarwinds-specific sampler"
        )
        return False

    logger.debug(
        "SolarWinds not ready. Got APM TracerProvider: %s",
        type(tracer_provider),
    )
    return False

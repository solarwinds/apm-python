# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# TODO: Remove when Python < 3.10 support dropped
from __future__ import annotations

import logging
import typing

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.propagators import textmap
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
from opentelemetry.trace.span import TraceState

from solarwinds_apm.apm_constants import (
    INTL_SWO_TRACESTATE_KEY,
    INTL_SWO_X_OPTIONS_KEY,
)
from solarwinds_apm.traceoptions import XTraceOptions
from solarwinds_apm.w3c_transformer import W3CTransformer

logger = logging.getLogger(__name__)


class SolarWindsPropagator(TraceContextTextMapPropagator):
    """Extracts and injects SolarWinds headers and W3C trace context
    headers for trace propagation.
    """

    _INVALID_SPAN_ID = 0x0000000000000000
    _TRACESTATE_HEADER_NAME = "tracestate"
    _XTRACEOPTIONS_HEADER_NAME = "x-trace-options"
    _XTRACEOPTIONS_SIGNATURE_HEADER_NAME = "x-trace-options-signature"

    def extract(
        self,
        carrier: textmap.CarrierT,
        context: Context | None = None,
        getter: textmap.Getter = textmap.default_getter,
    ) -> Context:
        """Extracts traceparent, tracestate, sw trace options, and signature
        from carrier into OTel Context.
        """
        context = super().extract(carrier, context, getter)

        xtraceoptions_header = getter.get(
            carrier, self._XTRACEOPTIONS_HEADER_NAME
        ) or [""]
        signature_header = getter.get(
            carrier, self._XTRACEOPTIONS_SIGNATURE_HEADER_NAME
        ) or [""]
        xtraceoptions = XTraceOptions(
            xtraceoptions_header[0],
            signature_header[0],
        )

        context.update({INTL_SWO_X_OPTIONS_KEY: xtraceoptions})
        return context

    def inject(
        self,
        carrier: textmap.CarrierT,
        context: Context | None = None,
        setter: textmap.Setter = textmap.default_setter,
    ) -> None:
        """Injects traceparent, tracestate with valid sw into carrier
        for HTTP request. Excludes any xtraceoptions_response if in
        tracestate.
        """
        super().inject(carrier, context, setter)

        span = trace.get_current_span(context)
        span_context = span.get_span_context()
        sw_value = W3CTransformer.sw_from_context(span_context)
        trace_state_header = carrier.get(self._TRACESTATE_HEADER_NAME, None)

        # Prepare carrier with carrier's or new tracestate
        trace_state = None
        # Note: OTel Propagation API callers (OTel instrumentors) may
        # inject header values as dictionary, not a string.
        if isinstance(trace_state_header, dict):
            trace_state_header = trace_state_header.get("StringValue")
        if not trace_state_header:
            # Only create new trace state if valid span_id
            if span_context.span_id == self._INVALID_SPAN_ID:
                return
            logger.debug(
                "Creating new trace state for injection with %s",
                sw_value,
            )
            trace_state = TraceState([(INTL_SWO_TRACESTATE_KEY, sw_value)])
        else:
            trace_state = TraceState.from_header([trace_state_header])
            # Check if trace_state already contains sw KV
            if INTL_SWO_TRACESTATE_KEY in trace_state:
                # If so, modify current span_id and trace_flags, and move to beginning of list
                logger.debug(
                    "Updating trace state for injection with %s",
                    sw_value,
                )
                trace_state = trace_state.update(
                    INTL_SWO_TRACESTATE_KEY, sw_value
                )

            else:
                # If not, add sw KV to beginning of list
                logger.debug(
                    "Adding KV to trace state for injection with %s",
                    sw_value,
                )
                trace_state = trace_state.add(
                    INTL_SWO_TRACESTATE_KEY, sw_value
                )

        # Remove any xtrace_options_response stored for ResponsePropagator
        trace_state = W3CTransformer.remove_response_from_sw(trace_state)
        setter.set(
            carrier, self._TRACESTATE_HEADER_NAME, trace_state.to_header()
        )

    # Note: this inherits deprecated `typing` use by OTel,
    #       for compatibility with Python3.8 else TypeError
    @property
    def fields(
        self,
    ) -> typing.Set[str]:  # pylint: disable=deprecated-typing-alias
        """Returns a set with the fields set in `inject`"""
        return super().fields

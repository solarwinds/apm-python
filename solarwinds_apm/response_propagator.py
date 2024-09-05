# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# TODO: Remove when Python < 3.10 support dropped
from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.instrumentation.propagators import ResponsePropagator
from opentelemetry.propagators import textmap
from opentelemetry.trace.span import TraceState

from solarwinds_apm.apm_constants import (
    INTL_SWO_COMMA,
    INTL_SWO_COMMA_W3C_SANITIZED,
    INTL_SWO_EQUALS,
    INTL_SWO_EQUALS_W3C_SANITIZED,
    INTL_SWO_X_OPTIONS_RESPONSE_KEY,
)
from solarwinds_apm.w3c_transformer import W3CTransformer

logger = logging.getLogger(__name__)


class SolarWindsTraceResponsePropagator(ResponsePropagator):
    """Propagator that injects SW values into HTTP responses"""

    _HTTP_HEADER_ACCESS_CONTROL_EXPOSE_HEADERS = (
        "Access-Control-Expose-Headers"
    )
    _XTRACE_HEADER_NAME = "x-trace"
    _XTRACEOPTIONS_RESPONSE_HEADER_NAME = "x-trace-options-response"

    def inject(
        self,
        carrier: textmap.CarrierT,
        context: Context | None = None,
        setter: textmap.Setter = textmap.default_setter,
    ) -> None:
        """Injects x-trace and options-response into the HTTP response carrier."""
        span = trace.get_current_span(context)
        span_context = span.get_span_context()
        if span_context == trace.INVALID_SPAN_CONTEXT:
            return

        x_trace = W3CTransformer.traceparent_from_context(span_context)
        setter.set(
            carrier,
            self._XTRACE_HEADER_NAME,
            x_trace,
        )
        exposed_headers = [self._XTRACE_HEADER_NAME]

        xtraceoptions_response = self.recover_response_from_tracestate(
            span_context.trace_state
        )
        if xtraceoptions_response:
            exposed_headers.append(
                f"{self._XTRACEOPTIONS_RESPONSE_HEADER_NAME}"
            )
            setter.set(
                carrier,
                self._XTRACEOPTIONS_RESPONSE_HEADER_NAME,
                xtraceoptions_response,
            )
        setter.set(
            carrier,
            self._HTTP_HEADER_ACCESS_CONTROL_EXPOSE_HEADERS,
            ",".join(exposed_headers),
        )

    def recover_response_from_tracestate(self, tracestate: TraceState) -> str:
        """Use tracestate to recover xtraceoptions response by
        converting delimiters:
        EQUALS_W3C_SANITIZED becomes EQUALS
        COMMA_W3C_SANITIZED becomes COMMA
        """
        sanitized = tracestate.get(INTL_SWO_X_OPTIONS_RESPONSE_KEY, None)
        if not sanitized:
            return ""
        return sanitized.replace(
            INTL_SWO_EQUALS_W3C_SANITIZED, INTL_SWO_EQUALS
        ).replace(INTL_SWO_COMMA_W3C_SANITIZED, INTL_SWO_COMMA)

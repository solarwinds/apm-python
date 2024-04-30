# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Provides functionality to transform OpenTelemetry Data to SolarWinds Observability data."""

from opentelemetry.sdk.trace import SpanContext
from opentelemetry.trace.span import TraceState

from solarwinds_apm.apm_constants import INTL_SWO_X_OPTIONS_RESPONSE_KEY


class W3CTransformer:
    """Transforms inputs to W3C-compliant data for SolarWinds context propagation"""

    _DECISION = "{}"
    _SPAN_ID_HEX = "{:016x}"
    _TRACE_FLAGS_HEX = "{:02x}"
    _TRACE_ID_HEX = "{:032x}"
    _VERSION = "00"

    @classmethod
    def span_id_from_int(cls, span_id: int) -> str:
        """Formats span ID as 16-byte hexadecimal string"""
        return cls._SPAN_ID_HEX.format(span_id)

    @classmethod
    def span_id_from_sw(cls, sw_val: str) -> str:
        """Formats span ID from sw tracestate value"""
        return sw_val.split("-")[0]

    @classmethod
    def trace_flags_from_int(cls, trace_flags: int) -> str:
        """Formats trace flags as 8-bit field"""
        return cls._TRACE_FLAGS_HEX.format(trace_flags)

    @classmethod
    def traceparent_from_context(cls, span_context: SpanContext) -> str:
        """Maps a liboboe W3C compatible trace_context from
        provided OTel span context."""
        template = "-".join(
            [
                cls._VERSION,
                cls._TRACE_ID_HEX,
                cls._SPAN_ID_HEX,
                cls._TRACE_FLAGS_HEX,
            ]
        )
        xtr = template.format(
            span_context.trace_id,
            span_context.span_id,
            span_context.trace_flags,
        )
        return xtr

    @classmethod
    def sw_from_context(cls, span_context: SpanContext) -> str:
        """Formats tracestate sw value from SpanContext as 16-byte span_id
        with 8-bit trace_flags.

        Example: 1a2b3c4d5e6f7g8h-01"""
        sw = "-".join([cls._SPAN_ID_HEX, cls._TRACE_FLAGS_HEX])
        return sw.format(span_context.span_id, span_context.trace_flags)

    @classmethod
    def trace_and_span_id_from_context(cls, span_context: SpanContext) -> str:
        """Formats trace ID and span ID as 32-byte and 16-byte hex str, respectively"""
        trace_span = "-".join([cls._TRACE_ID_HEX, cls._SPAN_ID_HEX])
        return trace_span.format(span_context.trace_id, span_context.span_id)

    @classmethod
    def sw_from_span_and_decision(cls, span_id: int, decision: str) -> str:
        """Formats tracestate sw value from span_id and liboboe decision
        as 16-byte span_id with 8-bit trace_flags.

        Example: 1a2b3c4d5e6f7g8h-01"""
        sw = "-".join([cls._SPAN_ID_HEX, cls._DECISION])
        return sw.format(span_id, decision)

    @classmethod
    def remove_response_from_sw(cls, trace_state: TraceState) -> TraceState:
        """Remove xtraceoptions response from tracestate"""
        if trace_state.get(INTL_SWO_X_OPTIONS_RESPONSE_KEY):
            trace_state = trace_state.delete(INTL_SWO_X_OPTIONS_RESPONSE_KEY)
        return trace_state

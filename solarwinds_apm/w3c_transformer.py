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
    """Transform inputs to W3C-compliant data for SolarWinds context propagation."""

    _DECISION = "{}"
    _SPAN_ID_HEX = "{:016x}"
    _TRACE_FLAGS_HEX = "{:02x}"
    _TRACE_ID_HEX = "{:032x}"
    _VERSION = "00"

    @classmethod
    def span_id_from_int(cls, span_id: int) -> str:
        """
        Format span ID as 16-byte hexadecimal string.

        Parameters:
        span_id (int): The span ID as an integer.

        Returns:
        str: The span ID formatted as 16-character hexadecimal string.
        """
        return cls._SPAN_ID_HEX.format(span_id)

    @classmethod
    def span_id_from_sw(cls, sw_val: str) -> str:
        """
        Extract span ID from sw tracestate value.

        Parameters:
        sw_val (str): The sw tracestate value (format: "<span_id>-<flags>").

        Returns:
        str: The span ID portion of the sw value.
        """
        return sw_val.split("-")[0]

    @classmethod
    def trace_flags_from_int(cls, trace_flags: int) -> str:
        """
        Format trace flags as 8-bit hexadecimal field.

        Parameters:
        trace_flags (int): The trace flags as an integer.

        Returns:
        str: The trace flags formatted as 2-character hexadecimal string.
        """
        return cls._TRACE_FLAGS_HEX.format(trace_flags)

    @classmethod
    def traceparent_from_context(cls, span_context: SpanContext) -> str:
        """
        Create W3C traceparent header from OpenTelemetry span context.

        Parameters:
        span_context (SpanContext): The OpenTelemetry span context.

        Returns:
        str: W3C traceparent header value (format: "00-<trace_id>-<span_id>-<flags>").
        """
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
        """
        Format tracestate sw value from SpanContext.

        Creates sw value as 16-byte span_id with 8-bit trace_flags.

        Parameters:
        span_context (SpanContext): The OpenTelemetry span context.

        Returns:
        str: SW tracestate value (format: "<span_id>-<flags>", e.g., "1a2b3c4d5e6f7g8h-01").
        """
        sw = "-".join([cls._SPAN_ID_HEX, cls._TRACE_FLAGS_HEX])
        return sw.format(span_context.span_id, span_context.trace_flags)

    @classmethod
    def trace_and_span_id_from_context(cls, span_context: SpanContext) -> str:
        """
        Format trace ID and span ID as hexadecimal strings.

        Parameters:
        span_context (SpanContext): The OpenTelemetry span context.

        Returns:
        str: Trace and span IDs (format: "<32-byte-trace-id>-<16-byte-span-id>").
        """
        trace_span = "-".join([cls._TRACE_ID_HEX, cls._SPAN_ID_HEX])
        return trace_span.format(span_context.trace_id, span_context.span_id)

    @classmethod
    def sw_from_span_and_decision(cls, span_id: int, decision: str) -> str:
        """
        Format tracestate sw value from span_id and liboboe decision.

        Creates sw value as 16-byte span_id with 8-bit trace_flags.

        Parameters:
        span_id (int): The span ID as an integer.
        decision (str): The liboboe sampling decision.

        Returns:
        str: SW tracestate value (format: "<span_id>-<decision>", e.g., "1a2b3c4d5e6f7g8h-01").
        """
        sw = "-".join([cls._SPAN_ID_HEX, cls._DECISION])
        return sw.format(span_id, decision)

    @classmethod
    def remove_response_from_sw(cls, trace_state: TraceState) -> TraceState:
        """
        Remove xtraceoptions response from tracestate.

        Parameters:
        trace_state (TraceState): The tracestate to modify.

        Returns:
        TraceState: Modified tracestate with xtraceoptions response removed.
        """
        if trace_state.get(INTL_SWO_X_OPTIONS_RESPONSE_KEY):
            trace_state = trace_state.delete(INTL_SWO_X_OPTIONS_RESPONSE_KEY)
        return trace_state

import logging
import typing

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.instrumentation.propagators import ResponsePropagator
from opentelemetry.propagators import textmap
from opentelemetry.trace.span import TraceState

from solarwinds_apm.apm_constants import (
    INTL_SWO_COMMA,
    INTL_SWO_COMMA_W3C_SANITIZED,
    INTL_SWO_EQUALS,
    INTL_SWO_EQUALS_W3C_SANITIZED
)
from solarwinds_apm.traceoptions import XTraceOptions
from solarwinds_apm.w3c_transformer import W3CTransformer

logger = logging.getLogger(__name__)

class SolarWindsTraceResponsePropagator(ResponsePropagator):
    """Propagator that injects SW values into HTTP responses"""
    _HTTP_HEADER_ACCESS_CONTROL_EXPOSE_HEADERS = "Access-Control-Expose-Headers"
    _XTRACE_HEADER_NAME = "x-trace"
    _XTRACEOPTIONS_RESPONSE_HEADER_NAME = "x-trace-options-response"
    
    def inject(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
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
            exposed_headers.append("{}".format(
                self._XTRACEOPTIONS_RESPONSE_HEADER_NAME
            ))
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
    
    def recover_response_from_tracestate(
        self,
        tracestate: TraceState
    ) -> str:
        """Use tracestate to recover xtraceoptions response by
        converting delimiters:
        EQUALS_W3C_SANITIZED becomes EQUALS
        COMMA_W3C_SANITIZED becomes COMMA
        """
        sanitized = tracestate.get(
            XTraceOptions.get_sw_xtraceoptions_response_key(),
            None
        )
        if not sanitized:
            return
        return sanitized.replace(
            INTL_SWO_EQUALS_W3C_SANITIZED,
            INTL_SWO_EQUALS
        ).replace(INTL_SWO_COMMA_W3C_SANITIZED, INTL_SWO_COMMA)

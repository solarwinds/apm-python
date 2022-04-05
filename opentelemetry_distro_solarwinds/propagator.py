import logging
import typing

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.propagators import textmap
from opentelemetry.trace.span import TraceState

from opentelemetry_distro_solarwinds.traceoptions import XTraceOptions
from opentelemetry_distro_solarwinds.w3c_transformer import W3CTransformer

logger = logging.getLogger(__file__)

class SolarWindsPropagator(textmap.TextMapPropagator):
    """Extracts and injects SolarWinds headers for trace propagation.
    Must be used in composite with TraceContextTextMapPropagator.
    """
    _TRACESTATE_HEADER_NAME = "tracestate"
    _XTRACEOPTIONS_HEADER_NAME = "x-trace-options"
    _XTRACEOPTIONS_SIGNATURE_HEADER_NAME = "x-trace-options-signature"

    def extract(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        getter: textmap.Getter = textmap.default_getter,
    ) -> Context:
        """Extracts sw trace options and signature from carrier into OTel
        Context. Note: tracestate is extracted by TraceContextTextMapPropagator
        """
        if context is None:
            context = Context()

        xtraceoptions_header = getter.get(
            carrier,
            self._XTRACEOPTIONS_HEADER_NAME
        )
        if not xtraceoptions_header:
            logger.debug("No xtraceoptions to extract; ignoring signature")
            return context
        logger.debug("Extracted xtraceoptions_header: {0}".format(
            xtraceoptions_header[0]
        ))

        signature_header = getter.get(
            carrier,
            self._XTRACEOPTIONS_SIGNATURE_HEADER_NAME
        )
        if signature_header:
            xtraceoptions = XTraceOptions(
                context,
                xtraceoptions_header[0],
                signature_header[0],
            )
        else:
            xtraceoptions = XTraceOptions(
                context,
                xtraceoptions_header[0],
            )
        context.update(dict(xtraceoptions))
        return context

    def inject(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        setter: textmap.Setter = textmap.default_setter,
    ) -> None:
        """Injects sw tracestate and trace options from SpanContext into carrier for HTTP request"""
        span = trace.get_current_span(context)
        span_context = span.get_span_context()
        trace_state = span_context.trace_state
        sw_value = W3CTransformer.sw_from_context(span_context)

        # Prepare carrier with context's or new tracestate
        if trace_state:
            # Check if trace_state already contains sw KV
            if "sw" in trace_state.keys():
                # If so, modify current span_id and trace_flags, and move to beginning of list
                logger.debug("Updating trace state for injection with {0}".format(sw_value))
                trace_state = trace_state.update("sw", sw_value)

            else:
                # If not, add sw KV to beginning of list
                logger.debug("Adding KV to trace state for injection with {0}".format(sw_value))
                trace_state.add("sw", sw_value)
        else:
            logger.debug("Creating new trace state for injection with {0}".format(sw_value))
            trace_state = TraceState([("sw", sw_value)])

        setter.set(
            carrier, self._TRACESTATE_HEADER_NAME, trace_state.to_header()
        )

    @property
    def fields(self) -> typing.Set[str]:
        """Returns a set with the fields set in `inject`"""
        return {
            self._TRACESTATE_HEADER_NAME
        }

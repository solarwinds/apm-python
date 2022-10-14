import logging
import typing

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.propagators import textmap
from opentelemetry.trace.span import TraceState

from solarwinds_apm.apm_constants import (
    INTL_SWO_X_OPTIONS_KEY,
    INTL_SWO_SIGNATURE_KEY,
    INTL_SWO_TRACESTATE_KEY
)
from solarwinds_apm.w3c_transformer import W3CTransformer

logger = logging.getLogger(__name__)

class SolarWindsPropagator(textmap.TextMapPropagator):
    """Extracts and injects SolarWinds headers for trace propagation.
    Must be used in composite with TraceContextTextMapPropagator.
    """
    _INVALID_SPAN_ID = 0x0000000000000000
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
            return context

        context.update({
            INTL_SWO_X_OPTIONS_KEY: xtraceoptions_header[0]
        })
        logger.debug("Extracted {} as {}: {}".format(
            self._XTRACEOPTIONS_HEADER_NAME,
            INTL_SWO_X_OPTIONS_KEY,
            xtraceoptions_header[0]
        ))

        signature_header = getter.get(
            carrier,
            self._XTRACEOPTIONS_SIGNATURE_HEADER_NAME
        )
        if signature_header:
            context.update({
                INTL_SWO_SIGNATURE_KEY: signature_header[0]
            })
            logger.debug("Extracted {} as {}: {}".format(
                self._XTRACEOPTIONS_SIGNATURE_HEADER_NAME,
                INTL_SWO_SIGNATURE_KEY,
                xtraceoptions_header[0]
            ))
        return context

    def inject(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        setter: textmap.Setter = textmap.default_setter,
    ) -> None:
        """Injects valid sw tracestate from carrier into carrier for HTTP request, to get
        tracestate injected by previous propagators"""
        span = trace.get_current_span(context)
        span_context = span.get_span_context()
        sw_value = W3CTransformer.sw_from_context(span_context)
        trace_state_header = carrier.get(self._TRACESTATE_HEADER_NAME, None)

        # Prepare carrier with carrier's or new tracestate
        trace_state = None
        if not trace_state_header:
            # Only create new trace state if valid span_id
            if span_context.span_id == self._INVALID_SPAN_ID:
                return
            else:
                logger.debug("Creating new trace state for injection with {}".format(sw_value))
                trace_state = TraceState([(INTL_SWO_TRACESTATE_KEY, sw_value)])
        else:
            trace_state = TraceState.from_header([trace_state_header])
            # Check if trace_state already contains sw KV
            if INTL_SWO_TRACESTATE_KEY in trace_state.keys():
                # If so, modify current span_id and trace_flags, and move to beginning of list
                logger.debug("Updating trace state for injection with {}".format(sw_value))
                trace_state = trace_state.update(INTL_SWO_TRACESTATE_KEY, sw_value)

            else:
                # If not, add sw KV to beginning of list
                logger.debug("Adding KV to trace state for injection with {}".format(sw_value))
                trace_state = trace_state.add(INTL_SWO_TRACESTATE_KEY, sw_value)

        setter.set(
            carrier, self._TRACESTATE_HEADER_NAME, trace_state.to_header()
        )

    @property
    def fields(self) -> typing.Set[str]:
        """Returns a set with the fields set in `inject`"""
        return {
            self._TRACESTATE_HEADER_NAME
        }

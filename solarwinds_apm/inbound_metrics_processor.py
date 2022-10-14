
import logging
from typing import (
    TYPE_CHECKING,
    Tuple,
)

from opentelemetry.trace import (
    SpanKind,
    StatusCode,
    TraceFlags,
)
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.semconv.trace import SpanAttributes

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan
    from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager


logger = logging.getLogger(__name__)


class SolarWindsInboundMetricsSpanProcessor(SpanProcessor):

    _HTTP_METHOD = SpanAttributes.HTTP_METHOD            # "http.method"
    _HTTP_ROUTE = SpanAttributes.HTTP_ROUTE              # "http.route"
    _HTTP_STATUS_CODE = SpanAttributes.HTTP_STATUS_CODE  # "http.status_code"
    _HTTP_URL = SpanAttributes.HTTP_URL                  # "http.url"

    _LIBOBOE_HTTP_SPAN_STATUS_UNAVAILABLE = 0

    def __init__(
        self,
        apm_txname_manager: "SolarWindsTxnNameManager",
        agent_enabled: bool,
    ) -> None:
        self._apm_txname_manager = apm_txname_manager
        if agent_enabled:
            from solarwinds_apm.extension.oboe import Span
            self._span = Span
        else:
            from solarwinds_apm.apm_noop import Span
            self._span = Span

    def on_end(self, span: "ReadableSpan") -> None:
        """Calculates and reports inbound trace metrics,
        and caches liboboe transaction name"""
        # Only calculate inbound metrics for service root spans
        parent_span_context = span.parent
        if parent_span_context and parent_span_context.is_valid \
            and not parent_span_context.is_remote:
            return

        is_span_http = self.is_span_http(span)
        span_time = self.calculate_span_time(
            span.start_time,
            span.end_time,
        )
        # TODO Use `domain` for custom transaction naming after alpha/beta
        domain = None
        has_error = self.has_error(span)
        trans_name, url_tran = self.calculate_transaction_names(span)

        liboboe_txn_name = None
        if is_span_http:
            # createHttpSpan needs these other params
            status_code = self.get_http_status_code(span)
            request_method = span.attributes.get(self._HTTP_METHOD, None)

            logger.debug(
                "createHttpSpan with trans_name: {}, url_tran: {}, domain: {}, span_time: {} status_code: {}, request_method: {}, has_error: {}".format(
                    trans_name, url_tran, domain, span_time, status_code, request_method, has_error,
                )
            )
            liboboe_txn_name = self._span.createHttpSpan(
                trans_name,
                url_tran,
                domain,
                span_time,
                status_code,
                request_method,
                has_error,
            )  
        else:
            logger.debug(
                "createSpan with trans_name: {}, domain: {}, span_time: {}, has_error: {}".format(
                    trans_name, domain, span_time, has_error,
                )
            )
            liboboe_txn_name = self._span.createSpan(
                trans_name,
                domain,
                span_time,
                has_error,
            )

        if span.context.trace_flags == TraceFlags.SAMPLED:
            # Cache txn_name for span export
            self._apm_txname_manager[
                "{}-{}".format(span.context.trace_id, span.context.span_id)
            ] = liboboe_txn_name

    def is_span_http(self, span: "ReadableSpan") -> bool:
        """This span from inbound HTTP request if from a SERVER by some http.method"""
        if span.kind == SpanKind.SERVER and span.attributes.get(self._HTTP_METHOD, None):
            return True
        return False

    def has_error(self, span: "ReadableSpan") -> bool:
        """Calculate if this span instance has_error"""
        if span.status.status_code == StatusCode.ERROR:
            return True
        return False

    def get_http_status_code(self, span: "ReadableSpan") -> int:
        """Calculate HTTP status_code from span or default to UNAVAILABLE"""
        status_code = span.attributes.get(self._HTTP_STATUS_CODE, None)
        # Something went wrong in OTel or instrumented service crashed early
        # if no status_code in attributes of HTTP span
        if not status_code:
            status_code = self._LIBOBOE_HTTP_SPAN_STATUS_UNAVAILABLE
        return status_code

    def calculate_transaction_names(self, span: "ReadableSpan") -> Tuple[str, str]:
        """Get trans_name and url_tran of this span instance."""
        url_tran = span.attributes.get(self._HTTP_URL, None)
        http_route = span.attributes.get(self._HTTP_ROUTE, None)
        trans_name = None
        if http_route:
            trans_name = http_route
        elif span.name:
            trans_name = span.name
        return trans_name, url_tran

    def calculate_span_time(
        self,
        start_time: int,
        end_time: int,
    ) -> int:
        """Calculate span time in microseconds (us) using start and end time
        in nanoseconds (ns). OTel span start/end_time are optional."""
        if not start_time or not end_time:
            return 0
        return int((end_time - start_time) // 1e3)

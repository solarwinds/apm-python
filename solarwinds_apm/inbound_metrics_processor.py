
import logging
from typing import (
    TYPE_CHECKING,
    Tuple,
)

from opentelemetry.trace import SpanKind, StatusCode
from opentelemetry.sdk.trace import SpanProcessor

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan
    from solarwinds_apm.extension.oboe import Reporter


logger = logging.getLogger(__name__)


class SolarWindsInboundMetricsSpanProcessor(SpanProcessor):

    _HTTP_METHOD = "http.method"
    _HTTP_ROUTE = "http.route"
    _HTTP_STATUS_CODE = "http.status_code"

    def __init__(
        self,
        reporter: "Reporter",
        agent_enabled: bool,
    ) -> None:
        self._reporter = reporter
        if agent_enabled:
            from solarwinds_apm.extension.oboe import Span
            self._span = Span
        else:
            from solarwinds_apm.apm_noop import Span
            self._span = Span

    def on_end(self, span: "ReadableSpan") -> None:
        """Calculates and reports inbound trace metrics"""
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

        if is_span_http:
            # createHttpSpan needs these other params
            status_code = span.attributes.get(self._HTTP_STATUS_CODE, None) 
            request_method = span.attributes.get(self._HTTP_METHOD, None)

            logger.debug(
                "createHttpSpan with trans_name: {}, url_tran: {}, domain: {}, span_time: {} status_code: {}, request_method: {}, has_error: {}".format(
                    trans_name, url_tran, domain, span_time, status_code, request_method, has_error,
                )
            )
            self._span.createHttpSpan(
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
            self._span.createSpan(
                trans_name,
                domain,
                span_time,
                has_error,
            )

        self._reporter.flush()

    def is_span_http(self, span: "ReadableSpan") -> bool:
        """This span from inbound HTTP request if from a SERVER by some http.route"""
        if span.kind == SpanKind.SERVER and span.attributes.get(self._HTTP_ROUTE, None):
            return True
        return False

    def has_error(self, span: "ReadableSpan") -> bool:
        """Calculate if this span instance has_error"""
        if span.status == StatusCode.ERROR:
            return True
        return False

    def calculate_transaction_names(self, span: "ReadableSpan") -> Tuple[str, str]:
        """Get trans_name and url_tran of this span instance."""
        trans_name = "unknown"
        if span.name:
            trans_name = span.name
        url_tran = span.attributes.get(self._HTTP_ROUTE, None)
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

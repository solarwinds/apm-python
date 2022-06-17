
import logging
from typing import TYPE_CHECKING

from opentelemetry.trace import SpanKind
from opentelemetry.sdk.trace import SpanProcessor

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan
    from solarwinds_apm.extension.oboe import Reporter


logger = logging.getLogger(__name__)


class SolarWindsInboundMetricsSpanProcessor(SpanProcessor):

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

        # TODO - We only do all this for root spans
        span_context = span.get_span_context()
        logger.info("span_context is {}".format(span_context))

        # The following is for Django A triggered trace
        # Always True and False
        logger.info("is_valid: {}, is_remote: {}".format(
            span_context.is_valid,
            span_context.is_remote,
        ))
        # Either SERVER or CLIENT
        logger.info("span.kind: {}".format(
            span.kind
        ))
        # Always GET, whether SERVER or CLIENT
        logger.info("span.attributes.get(http.method): {}".format(
            span.attributes.get("http.method", None)
        ))

        is_span_http = self.is_span_http(span)
        logger.info("is_span_http: {}".format(is_span_http))

        span_time = self.get_span_time(
            span.start_time,
            span.end_time,
        )
        # TODO Use `domain` for custom transaction naming after alpha/beta
        domain = None
        has_error = self.has_error()
        trans_name = self.get_transaction_name()

        if is_span_http:
            # Only createHttpSpan needs these other params:
            url_tran = span.attributes.get("http.url", None)
            status_code = span.attributes.get("http.status_code", None) 
            request_method = span.attributes.get("http.method", None)

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
        """This span from inbound HTTP request if from a SERVER"""
        if span.kind == SpanKind.SERVER:
            return True
        return False

    def get_transaction_name(self):
        """Get transaction name of this span instance"""
        # TODO
        return ""

    def has_error(self):
        """Calculate if this span instance has_error"""
        # TODO
        return False

    def get_span_time(
        self,
        start_time: int,
        end_time: int,
    ) -> int:
        """Calculate span time in microseconds (us) using start and end time
        in nanoseconds (ns). OTel span start/end_time are optional."""
        if not start_time or not end_time:
            return 0
        return int((end_time - start_time) // 1e3)

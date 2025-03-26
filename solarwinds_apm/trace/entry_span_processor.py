import logging
from typing import TYPE_CHECKING

from opentelemetry.context import Context
from opentelemetry.sdk.trace import SpanProcessor

if TYPE_CHECKING:

    from opentelemetry.sdk.trace import ReadableSpan, Span

logger = logging.getLogger(__name__)


class SolarWindsEntrySpanProcessor(SpanProcessor):
    """Test processor repurposed for debugging
    TODO remove from here, module __init__, and configurator"""

    def on_start(
        self,
        span: "Span",
        parent_context: Context | None = None,
    ) -> None:
        """Caches current span, if entry span, in entry span manager"""
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        logger.info("Entry Span at on_start: %s", span)
        logger.info("with type: %s", type(span))
        logger.info("with attributes: %s", span.attributes)

    def on_end(
        self,
        span: "ReadableSpan",
    ) -> None:
        """Updates cached entry span, if exists"""
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        logger.info("Entry Span at on_end: %s", span)
        logger.info("with type: %s", type(span))
        logger.info("with attributes: %s", span.attributes)

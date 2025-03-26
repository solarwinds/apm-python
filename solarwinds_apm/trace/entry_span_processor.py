import logging
from typing import TYPE_CHECKING

from opentelemetry.context import Context
from opentelemetry.sdk.trace import SpanProcessor

from solarwinds_apm.apm_entry_span_manager import SolarwindsEntrySpanManager

if TYPE_CHECKING:

    from opentelemetry.sdk.trace import ReadableSpan, Span

logger = logging.getLogger(__name__)


class SolarWindsEntrySpanProcessor(SpanProcessor):
    def __init__(
        self,
        apm_entry_span_manager: SolarwindsEntrySpanManager,
    ) -> None:
        self.apm_entry_span_manager = apm_entry_span_manager

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

        logger.info("Caching entry span %s", span.context.span_id)

        self.apm_entry_span_manager[span.context.span_id] = span

        try:
            logger.info("Entry Span at on_start: %s", span)
            logger.info("with type: %s", type(span))
            logger.info("with attributes: %s", span.attributes)
        except Exception as e:
            logger.error(
                "%s: %s",
                type(e).__name__,
                e,
            )

    def on_end(
        self,
        span: "ReadableSpan",
    ) -> None:
        """Updates cached entry span, if exists"""
        entry_span = self.apm_entry_span_manager.get(span.context.span_id)
        if entry_span:
            logger.info(
                "Setting span name, attributes for entry span %s",
                entry_span.context.span_id,
            )
            try:
                # AttributeError: can't set attribute 'name'
                # entry_span.name = "MyAwesomeSpanName"

                # AttributeError: can't set attribute 'attributes'
                # entry_span.attributes = {"bazbaz": "quxqux"}

                # Setting attribute on ended span.
                entry_span.set_attribute("foofoo", "barbar")
                entry_span.set_attribute(
                    "TransactionName", "MyAwesomeTransactionName"
                )
            except Exception as e:
                logger.error(
                    "%s: %s",
                    type(e).__name__,
                    e,
                )
            logger.info("Entry Span at on_end: %s", entry_span)
            logger.info("with type: %s", type(entry_span))
            logger.info("with attributes: %s", entry_span.attributes)

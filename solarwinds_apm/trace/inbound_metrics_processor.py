# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING, Any, Optional, Tuple

from opentelemetry import baggage, context
from opentelemetry.trace import TraceFlags

from solarwinds_apm.apm_constants import INTL_SWO_CURRENT_TRACE_ENTRY_SPAN_ID
from solarwinds_apm.trace.base_metrics_processor import _SwBaseMetricsProcessor
from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_config import SolarWindsApmConfig
    from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager


logger = logging.getLogger(__name__)


class SolarWindsInboundMetricsSpanProcessor(_SwBaseMetricsProcessor):
    """SolarWinds span processor for APM-proto inbound metrics generation"""

    def __init__(
        self,
        apm_txname_manager: "SolarWindsTxnNameManager",
        apm_config: "SolarWindsApmConfig",
    ) -> None:
        super().__init__(
            apm_txname_manager=apm_txname_manager,
        )
        self._span = apm_config.extension.Span
        self.config_transaction_name = apm_config.get(self._TRANSACTION_NAME)

    # This is moved in https://github.com/solarwinds/apm-python/pull/252
    def on_start(
        self,
        span: "ReadableSpan",
        parent_context: Optional[context.Context] = None,
    ) -> None:
        """Caches current trace ID and entry span ID in span context baggage"""
        # Only caches for service entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        context.attach(
            baggage.set_baggage(
                INTL_SWO_CURRENT_TRACE_ENTRY_SPAN_ID,
                W3CTransformer.trace_and_span_id_from_context(span.context),
            )
        )

    def on_end(self, span: "ReadableSpan") -> None:
        """Calculates and reports inbound trace metrics,
        and caches liboboe transaction name"""
        # Only calculate inbound metrics for service entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
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

            # TODO Change when this is logged (don't when no-op)
            # https://swicloud.atlassian.net/browse/NH-65061
            logger.debug(
                "createHttpSpan with trans_name: %s, url_tran: %s, domain: %s, span_time: %s status_code: %s, request_method: %s, has_error: %s",
                trans_name,
                url_tran,
                domain,
                span_time,
                status_code,
                request_method,
                has_error,
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
            # TODO Change when this is logged (don't when no-op)
            # https://swicloud.atlassian.net/browse/NH-65061
            logger.debug(
                "createSpan with trans_name: %s, domain: %s, span_time: %s, has_error: %s",
                trans_name,
                domain,
                span_time,
                has_error,
            )
            liboboe_txn_name = self._span.createSpan(
                trans_name,
                domain,
                span_time,
                has_error,
            )

        if span.context.trace_flags == TraceFlags.SAMPLED:
            # Cache txn_name for span export
            self.apm_txname_manager[
                W3CTransformer.trace_and_span_id_from_context(span.context)
            ] = liboboe_txn_name  # type: ignore

    # Disable pylint for compatibility with Python3.7 else TypeError
    def calculate_transaction_names(
        self, span: "ReadableSpan"
    ) -> Tuple[Any, Any]:  # pylint: disable=deprecated-typing-alias
        """Get trans_name and url_tran of this span instance."""
        url_tran = span.attributes.get(self._HTTP_URL, None)
        http_route = span.attributes.get(self._HTTP_ROUTE, None)
        trans_name = None
        custom_trans_name = self.calculate_custom_transaction_name(span)
        if not custom_trans_name:
            custom_trans_name = self.config_transaction_name

        if custom_trans_name:
            trans_name = custom_trans_name
        elif http_route:
            trans_name = http_route
        elif span.name:
            trans_name = span.name
        return trans_name, url_tran

    def calculate_custom_transaction_name(self, span: "ReadableSpan") -> Any:
        """Get custom transaction name for trace by trace_id, if any"""
        trans_name = None
        trace_span_id = W3CTransformer.trace_and_span_id_from_context(
            span.context
        )
        custom_name = self.apm_txname_manager.get(trace_span_id)
        if custom_name:
            trans_name = custom_name
            # Remove custom name from cache in case not sampled.
            # If sampled, should be re-added at on_end.
            del self.apm_txname_manager[trace_span_id]
        return trans_name

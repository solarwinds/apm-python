# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING, Any, Tuple

from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.semconv.trace import SpanAttributes

from solarwinds_apm.trace.tnames import TransactionNames
from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager


logger = logging.getLogger(__name__)


class TxnNameCalculatorProcessor(SpanProcessor):
    """Span processor that calculates and stores transaction names in
    Transaction Name manager by trace-span ID at span on_end.

    Name values are stored as tuples in this order:
    (transaction_name, url_transaction)

    Should be registered before other processors that depend
    on the stored names, e.g. before SolarWinds metrics processors."""

    _HTTP_ROUTE = SpanAttributes.HTTP_ROUTE  # "http.route"
    _HTTP_URL = SpanAttributes.HTTP_URL  # "http.url"

    def __init__(
        self,
        apm_txname_manager: "SolarWindsTxnNameManager",
    ) -> None:
        self.apm_txname_manager = apm_txname_manager

    def on_end(self, span: "ReadableSpan") -> None:
        """Calculates and stores automated and custom TransactionNames
        for service entry spans.

        If a custom name str was stored by the API, this method
        overwrites that str with a new TransactionName object"""
        # Only calculate inbound metrics for service entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        trans_name, url_tran = self.calculate_transaction_names(span)
        custom_name = self.calculate_custom_transaction_name(span)
        self.apm_txname_manager[
            W3CTransformer.trace_and_span_id_from_context(span.context)
        ] = TransactionNames(
            trans_name,
            url_tran,
            custom_name,
        )  # type: ignore

    # Disable pylint for compatibility with Python3.7 else TypeError
    def calculate_transaction_names(
        self, span: "ReadableSpan"
    ) -> Tuple[Any, Any]:  # pylint: disable=deprecated-typing-alias
        """Get trans_name and url_tran of this span instance."""
        url_tran = span.attributes.get(self._HTTP_URL, None)
        http_route = span.attributes.get(self._HTTP_ROUTE, None)
        trans_name = None

        if http_route:
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
        return trans_name

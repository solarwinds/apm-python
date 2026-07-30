# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Service entry span processor for transaction name management and context tracking."""

# TODO: Remove when Python < 3.10 support dropped
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from opentelemetry import context
from opentelemetry.sdk.trace import Span, SpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes

from solarwinds_apm.apm_constants import (
    INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN,
    INTL_SWO_TRANSACTION_ATTR_KEY,
    INTL_SWO_TRANSACTION_ATTR_MAX,
)
from solarwinds_apm.oboe import get_transaction_name_pool
from solarwinds_apm.oboe.transaction_name_calculator import (
    resolve_transaction_name,
)
from solarwinds_apm.oboe.transaction_name_pool import TRANSACTION_NAME_DEFAULT
from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

logger = logging.getLogger(__name__)


class ServiceEntrySpanProcessor(SpanProcessor):
    """
    Span processor for managing service entry spans.

    Handles transaction name calculation and context tracking for service entry spans,
    which are spans without valid local parents.
    """

    def __init__(self) -> None:
        """
        Initialize the ServiceEntrySpanProcessor.
        """
        self.context_tokens = {}

    def set_default_transaction_name(
        self,
        span: Span,
        attribute_value: str,
        resolve: bool = False,
    ) -> None:
        """
        Set initial transaction name as span attribute.

        Pool registration is deferred to _on_ending() for all transaction names.

        Parameters:
        span (Span): The span to set the transaction name on.
        attribute_value (str): The transaction name value.
        resolve (bool): Whether to resolve the transaction name (e.g., for URL paths). Defaults to False.
        """
        transaction_name = attribute_value
        if resolve:
            transaction_name = resolve_transaction_name(attribute_value)
        # Set attribute without pool registration (finalized in _on_ending)
        span.set_attribute(
            INTL_SWO_TRANSACTION_ATTR_KEY,
            transaction_name[:INTL_SWO_TRANSACTION_ATTR_MAX],
        )

    def on_start(
        self,
        span: Span,
        parent_context: context.Context | None = None,
    ) -> None:
        """
        Calculate default transaction name and cache entry span for custom naming.

        Calculates transaction name for span and metrics following this order
        of decreasing precedence, truncated to 255 char:
        1. SW_APM_TRANSACTION_NAME
        2. Any instrumentor-set span attributes for FaaS
        3. AWS_LAMBDA_FUNCTION_NAME
        4. Any instrumentor-set span attributes for HTTP
        5. Span name (default)
        6. "other" (when the transaction name pool limit reached at span _on_ending)

        If entry span, caches it in context for custom transaction naming.

        Parameters:
        span (Span): The span that is starting.
        parent_context (context.Context | None): The parent context, if any. Defaults to None.
        """
        # Only caches for service entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        # Calculate non-custom txn name for entry span if we can retrieve the URL
        # or serverless name. Otherwise, use the span's name
        sw_apm_txn_name = os.environ.get("SW_APM_TRANSACTION_NAME", None)
        faas_name = span.attributes.get(ResourceAttributes.FAAS_NAME, None)
        lambda_function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", None)
        http_route = span.attributes.get(SpanAttributes.HTTP_ROUTE, None)
        url_path = span.attributes.get(SpanAttributes.URL_PATH, None)
        if sw_apm_txn_name:
            self.set_default_transaction_name(span, sw_apm_txn_name)
        elif faas_name:
            self.set_default_transaction_name(span, faas_name)
        elif lambda_function_name:
            self.set_default_transaction_name(
                span,
                lambda_function_name[:INTL_SWO_TRANSACTION_ATTR_MAX],
            )
        elif http_route:
            self.set_default_transaction_name(span, http_route)
        elif url_path:
            self.set_default_transaction_name(span, url_path, resolve=True)
        else:
            self.set_default_transaction_name(span, span.name)

        # Cache the entry span in current context to use upstream-managed
        # execution scope and handle async tracing, for custom naming
        entry_trace_span_id = W3CTransformer.trace_and_span_id_from_context(
            span.context
        )
        logger.debug(
            "Attaching context with key %s as entry span with name: %s, trace/span id: %s",
            INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN,
            span.name,
            entry_trace_span_id,
        )
        token = context.attach(
            context.set_value(
                INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN,
                span,
            )
        )
        logger.debug(
            "Storing token %s for trace/span id %s",
            token,
            entry_trace_span_id,
        )
        self.context_tokens[entry_trace_span_id] = token

    def _on_ending(self, span: Span) -> None:
        """
        Finalize transaction name by registering with pool.

        This is called before the span becomes immutable, allowing us to update
        the transaction name attribute with the final pool-registered version.

        See span on_start for order of precendence for transaction name setting.
        If transaction name pool limit is reached here at _on_ending, then
        name is set here as "other".

        Parameters:
        span (Span): The span that is ending (still mutable).
        """
        # Only process entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        # Read whatever transaction name is set (initial OR user-set)
        txn_name = span.attributes.get(INTL_SWO_TRANSACTION_ATTR_KEY)
        if txn_name:
            pool = get_transaction_name_pool()
            registered_name = pool.registered(txn_name)
            if registered_name == TRANSACTION_NAME_DEFAULT:
                logger.warning(
                    "Transaction name pool is full; set as %s for span %s",
                    TRANSACTION_NAME_DEFAULT,
                    W3CTransformer.trace_and_span_id_from_context(
                        span.context
                    ),
                )
            # Update with pool-registered name
            span.set_attribute(INTL_SWO_TRANSACTION_ATTR_KEY, registered_name)

    def on_end(self, span: ReadableSpan) -> None:
        """
        Clean up context for service entry spans.

        Detaches and removes the context token for entry spans.
        Only processes service entry spans (spans without valid local parent).

        Parameters:
        span (ReadableSpan): The span that has ended.
        """
        # Only attempt for service entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        entry_trace_span_id = W3CTransformer.trace_and_span_id_from_context(
            span.context
        )
        # Retrieve the token corresponding to this trace/span id,
        # reset its context (detach), and removes token from APM's cache
        token = self.context_tokens.pop(entry_trace_span_id, None)
        if token is None:
            logger.debug(
                "No token found for entry trace/span id: %s",
                entry_trace_span_id,
            )
            return
        logger.debug(
            "Detaching from context using token %s from trace/span id: %s",
            token,
            entry_trace_span_id,
        )
        context.detach(token)

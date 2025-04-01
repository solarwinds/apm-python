# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

# TODO: Remove when Python < 3.10 support dropped
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from opentelemetry import context
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes

from solarwinds_apm.apm_constants import INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN
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
    def __init__(self) -> None:
        self.context_tokens = {}

    def on_start(
        self,
        span: "ReadableSpan",
        parent_context: context.Context | None = None,
    ) -> None:
        """If entry span, caches it at its trace ID. Used for custom transaction naming."""
        # Only caches for service entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        # Calculate non-custom txn name for entry span if we can retrieve the URL

        # TODO: use in order of precedence, else span.name
        faas_name = span.attributes.get(ResourceAttributes.FAAS_NAME, "")
        http_route = span.attributes.get(SpanAttributes.HTTP_ROUTE, "")
        url_path = span.attributes.get(SpanAttributes.URL_PATH, "")
        http_target = (
            span.attributes.get(SpanAttributes.URL_PATH, None)
            or span.attributes.get(SpanAttributes.HTTP_TARGET, None)
            or ""
        )

        url = (
            span.attributes.get(SpanAttributes.URL_FULL)
            or span.attributes.get(SpanAttributes.HTTP_URL)
            or ""
        )
        if url:
            resolved_name = resolve_transaction_name(url)
            pool = get_transaction_name_pool()
            registered_name = pool.registered(resolved_name)
            if registered_name == TRANSACTION_NAME_DEFAULT:
                logger.warning(
                    "Transaction name pool is full; set as %s for span %s",
                    TRANSACTION_NAME_DEFAULT,
                    W3CTransformer.trace_and_span_id_from_context(
                        span.context
                    ),
                )
            span.set_attribute("TransactionName", registered_name)

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

    def on_end(self, span: "ReadableSpan") -> None:
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

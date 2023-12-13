# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING, Optional

from opentelemetry import baggage, context
from opentelemetry.sdk.trace import SpanProcessor

from solarwinds_apm.apm_constants import INTL_SWO_CURRENT_TRACE_ENTRY_SPAN_ID
from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

logger = logging.getLogger(__name__)


class ServiceEntryIdSpanProcessor(SpanProcessor):
    def on_start(
        self,
        span: "ReadableSpan",
        parent_context: Optional[context.Context] = None,
    ) -> None:
        """Caches current trace ID and entry span ID in span context baggage for API set_transaction_name"""
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

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

from solarwinds_apm.apm_constants import INTL_SWO_CURRENT_TRACE_ENTRY_SPAN_ID
from solarwinds_apm.apm_entry_span_manager import SolarwindsEntrySpanManager

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

logger = logging.getLogger(__name__)


class ServiceEntrySpanProcessor(SpanProcessor):
    def __init__(
        self,
        apm_entry_span_manager: SolarwindsEntrySpanManager,
    ) -> None:
        self.apm_entry_span_manager = apm_entry_span_manager

    def on_start(
        self,
        span: "ReadableSpan",
        parent_context: context.Context | None = None,
    ) -> None:
        """If entry span, caches it e.g. for API set_transaction_name"""
        # Only caches for service entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        self.apm_entry_span_manager[INTL_SWO_CURRENT_TRACE_ENTRY_SPAN_ID] = (
            span
        )

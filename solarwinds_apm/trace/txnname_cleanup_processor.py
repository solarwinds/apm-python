# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING

from opentelemetry.sdk.trace import SpanProcessor

from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager


logger = logging.getLogger(__name__)


class TxnNameCleanupProcessor(SpanProcessor):
    """Span processor that deletes any transaction names stored in
    Transaction Name manager by trace-span ID at span on_end.

    Should be registered after other processors that depend
    on the stored names, e.g. after SolarWinds metrics processors."""

    def __init__(
        self,
        apm_txname_manager: "SolarWindsTxnNameManager",
    ) -> None:
        self.apm_txname_manager = apm_txname_manager

    def on_end(self, span: "ReadableSpan") -> None:
        trace_span_id = W3CTransformer.trace_and_span_id_from_context(
            span.context
        )
        txn_name = self.apm_txname_manager.get(trace_span_id)
        if txn_name:
            del self.apm_txname_manager[trace_span_id]

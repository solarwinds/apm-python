# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import random
from typing import TYPE_CHECKING

from solarwinds_apm.trace.base_metrics_processor import _SwBaseMetricsProcessor
from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_config import SolarWindsApmConfig
    from solarwinds_apm.apm_meter_manager import SolarWindsMeterManager
    from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager


logger = logging.getLogger(__name__)


class SolarWindsOTLPMetricsSpanProcessor(_SwBaseMetricsProcessor):
    """SolarWinds span processor for OTLP metrics recording"""

    def __init__(
        self,
        apm_txname_manager: "SolarWindsTxnNameManager",
        apm_config: "SolarWindsApmConfig",
        apm_meters: "SolarWindsMeterManager",
    ) -> None:
        super().__init__(
            apm_txname_manager=apm_txname_manager,
        )
        self.service_name = apm_config.service_name
        self.apm_meters = apm_meters

    def on_end(self, span: "ReadableSpan") -> None:
        """Calculates and reports OTLP trace metrics"""
        # Only calculate OTLP metrics for service entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        # TODO add sw.service_name
        # https://swicloud.atlassian.net/browse/NH-67392
        # support ssa and conform to Otel proto common_pb2
        meter_attrs = {
            "sw.nonce": random.getrandbits(64) >> 1,
        }

        # TODO add trace.service.requests, trace.service.errors
        # https://swicloud.atlassian.net/browse/NH-67392
        has_error = self.has_error(span)
        if has_error:
            meter_attrs.update({"sw.is_error": "true"})
        else:
            meter_attrs.update({"sw.is_error": "false"})

        # trans_name will never be None because always at least span.name
        # TODO don't assume successfully calculated and stored for every span
        txn_name_tuple = self.apm_txname_manager.get(
            W3CTransformer.trace_and_span_id_from_context(span.context)
        )
        trans_name = txn_name_tuple[0]

        is_span_http = self.is_span_http(span)
        span_time = self.calculate_span_time(
            span.start_time,
            span.end_time,
        )

        if is_span_http:
            status_code = self.get_http_status_code(span)
            request_method = span.attributes.get(self._HTTP_METHOD, None)
            meter_attrs.update(
                {
                    self._HTTP_STATUS_CODE: status_code,
                    self._HTTP_METHOD: request_method,
                    "sw.transaction": trans_name,
                }
            )
        else:
            meter_attrs.update({"sw.transaction": trans_name})
        self.apm_meters.response_time.record(
            amount=span_time,
            attributes=meter_attrs,
        )
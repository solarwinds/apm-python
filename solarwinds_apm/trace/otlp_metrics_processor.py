# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING

from solarwinds_apm.trace.base_metrics_processor import _SwBaseMetricsProcessor

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_config import SolarWindsApmConfig
    from solarwinds_apm.apm_meter_manager import SolarWindsMeterManager
    from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager
    from solarwinds_apm.trace.tnames import TransactionNames


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
        # SW_APM_TRANSACTION_NAME and AWS_LAMBDA_FUNCTION_NAME
        self.env_transaction_name = apm_config.get("transaction_name")
        self.lambda_function_name = apm_config.lambda_function_name

        self.apm_meters = apm_meters

    def calculate_otlp_transaction_name(
        self,
        tnames: "TransactionNames",
    ) -> str:
        """Calculate transaction name for OTLP metrics following this order
        of decreasing precedence:

        1. custom SDK name
        2. SW_APM_TRANSACTION_NAME
        3. AWS_LAMBDA_FUNCTION_NAME
        4. automated naming from span name, attributes
        """
        if tnames.custom_name:
            return tnames.custom_name

        if self.env_transaction_name:
            return self.env_transaction_name

        if self.lambda_function_name:
            return self.lambda_function_name

        return tnames.trans_name

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

        tnames = self.get_tnames(span)
        if not tnames:
            logger.error(
                "Could not get transaction name. Not recording otlp metrics."
            )
            return

        trans_name = self.calculate_otlp_transaction_name(tnames)

        meter_attrs = {}
        has_error = self.has_error(span)
        if has_error:
            meter_attrs.update({"sw.is_error": "true"})
        else:
            meter_attrs.update({"sw.is_error": "false"})

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

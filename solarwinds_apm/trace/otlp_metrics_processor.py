# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING

from solarwinds_apm.apm_constants import INTL_SWO_TRANSACTION_ATTR_KEY
from solarwinds_apm.apm_meter_manager import SolarWindsMeterManager
from solarwinds_apm.apm_noop import SolarWindsMeterManager as NoopMeterManager
from solarwinds_apm.trace.base_metrics_processor import _SwBaseMetricsProcessor

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_config import SolarWindsApmConfig
    from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager
    from solarwinds_apm.extension.oboe import OboeAPI


logger = logging.getLogger(__name__)


class SolarWindsOTLPMetricsSpanProcessor(_SwBaseMetricsProcessor):
    """SolarWinds span processor for OTLP metrics recording."""

    def __init__(
        self,
        apm_txname_manager: "SolarWindsTxnNameManager",
        apm_config: "SolarWindsApmConfig",
        oboe_api: "OboeAPI",
    ) -> None:
        super().__init__(
            apm_txname_manager=apm_txname_manager,
        )
        self.service_name = apm_config.service_name
        # SW_APM_TRANSACTION_NAME and AWS_LAMBDA_FUNCTION_NAME
        self.env_transaction_name = apm_config.get("transaction_name")
        self.lambda_function_name = apm_config.lambda_function_name

        # TODO Add experimental trace flag, clean up
        #      https://swicloud.atlassian.net/browse/NH-65067
        #
        if not apm_config.get("experimental").get("otel_collector") is True:
            logger.debug(
                "Experimental otel_collector flag not configured. Creating meter manager as no-op."
            )
            self.apm_meters = NoopMeterManager()
        else:
            self.apm_meters = SolarWindsMeterManager(
                apm_config,
                oboe_api,
            )

    def calculate_otlp_transaction_name(
        self,
        span_name: str,
    ) -> str:
        """Calculate transaction name for OTLP metrics following this order
        of decreasing precedence:

        1. SW_APM_TRANSACTION_NAME
        2. AWS_LAMBDA_FUNCTION_NAME
        3. automated naming from span name
        4. "unknown_service" backup, to match OpenTelemetry SDK Resource default

        See also _SwSampler.calculate_otlp_transaction_name
        """
        if self.env_transaction_name:
            return self.env_transaction_name

        if self.lambda_function_name:
            return self.lambda_function_name

        if span_name:
            return span_name

        return "unknown_service"

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

        trans_name = self.calculate_otlp_transaction_name(span.name)

        meter_attrs = {}
        has_error = self.has_error(span)
        if has_error:
            meter_attrs.update({"sw.is_error": "true"})
        else:
            meter_attrs.update({"sw.is_error": "false"})

        is_span_http = self.is_span_http(span)
        # convert from ns to milliseconds
        span_time = self.calculate_span_time(
            span.start_time,
            span.end_time,
            1e6,
        )

        if is_span_http:
            status_code = self.get_http_status_code(span)
            request_method = span.attributes.get(self._HTTP_METHOD, None)
            meter_attrs.update(
                {
                    self._HTTP_STATUS_CODE: status_code,
                    self._HTTP_METHOD: request_method,
                    INTL_SWO_TRANSACTION_ATTR_KEY: trans_name,
                }
            )
        else:
            meter_attrs.update({INTL_SWO_TRANSACTION_ATTR_KEY: trans_name})
        self.apm_meters.response_time.record(
            amount=span_time,
            attributes=meter_attrs,
        )

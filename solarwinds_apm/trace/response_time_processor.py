# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING

from opentelemetry.metrics import get_meter

from solarwinds_apm.apm_constants import (
    INTL_SWO_TRANSACTION_ATTR_KEY,
    INTL_SWO_TRANSACTION_NAME_ATTR,
)
from solarwinds_apm.trace.base_metrics_processor import _SwBaseMetricsProcessor

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_config import SolarWindsApmConfig


logger = logging.getLogger(__name__)


class ResponseTimeProcessor(_SwBaseMetricsProcessor):
    """SolarWinds span processor for recording response_time metrics."""

    def __init__(
        self,
        apm_config: "SolarWindsApmConfig",
    ) -> None:
        super().__init__()
        self.service_name = apm_config.service_name
        # SW_APM_TRANSACTION_NAME and AWS_LAMBDA_FUNCTION_NAME
        self.env_transaction_name = apm_config.get("transaction_name")
        self.lambda_function_name = apm_config.lambda_function_name

        self._meter_response_times = get_meter("sw.apm.request.metrics")
        self.response_time = self._meter_response_times.create_histogram(
            name="trace.service.response_time",
            description="measures the duration of an inbound HTTP request",
            unit="ms",
        )

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

        trans_name = span.attributes.get(INTL_SWO_TRANSACTION_NAME_ATTR, None)

        meter_attrs = {}
        has_error = self.has_error(span)
        if has_error:
            meter_attrs.update({"sw.is_error": True})
        else:
            meter_attrs.update({"sw.is_error": False})

        is_span_http = self.is_span_http(span)
        # convert from ns to milliseconds
        span_time = self.calculate_span_time(
            span.start_time,
            span.end_time,
            1e6,
        )

        meter_attrs.update({INTL_SWO_TRANSACTION_ATTR_KEY: trans_name})
        if is_span_http:
            status_code = self.get_http_status_code(span)
            # UNAVAILABLE is zero
            if status_code > 0:
                meter_attrs.update({self._HTTP_STATUS_CODE: status_code})
            request_method = span.attributes.get(self._HTTP_METHOD, None)
            if request_method:
                meter_attrs.update({self._HTTP_METHOD: request_method})

        self.response_time.record(
            amount=span_time,
            attributes=meter_attrs,
        )

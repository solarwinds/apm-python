# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING

from opentelemetry.metrics import get_meter
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import SpanKind, StatusCode

from solarwinds_apm.apm_constants import (
    INTL_SWO_TRANSACTION_ATTR_KEY,
    INTL_SWO_TRANSACTION_ATTR_MAX,
    INTL_SWO_TRANSACTION_NAME_ATTR,
)

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_config import SolarWindsApmConfig


logger = logging.getLogger(__name__)


class ResponseTimeProcessor(SpanProcessor):
    """SolarWinds span processor for recording response_time metrics."""

    _HTTP_REQUEST_METHOD = (
        SpanAttributes.HTTP_REQUEST_METHOD
    )  # http.request.method
    _HTTP_RESPONSE_STATUS_CODE = (
        SpanAttributes.HTTP_RESPONSE_STATUS_CODE
    )  # "http.response.status_code"

    # Deprecated, but potentially still used by some instrumentors
    _HTTP_METHOD = SpanAttributes.HTTP_METHOD  # "http.method"
    _HTTP_STATUS_CODE = SpanAttributes.HTTP_STATUS_CODE  # "http.status_code"

    _HTTP_SPAN_STATUS_UNAVAILABLE = 0

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
            description="Duration of each entry span for the service, typically meaning the time taken to process an inbound request.",
            unit="ms",
        )

    def is_span_http(self, span: "ReadableSpan") -> bool:
        """This span from inbound HTTP request if from a SERVER by some http.request.method or http.method"""
        return bool(
            span.kind == SpanKind.SERVER
            and (
                span.attributes.get(self._HTTP_REQUEST_METHOD, None)
                or span.attributes.get(self._HTTP_METHOD, None)
            )
        )

    def has_error(self, span: "ReadableSpan") -> bool:
        """Calculate if this span instance has_error"""
        return span.status.status_code == StatusCode.ERROR

    def calculate_span_time(
        self,
        start_time: int,
        end_time: int,
        time_conversion: int = 1e3,
    ) -> int:
        """Calculate span time (via time_conversion e.g. 1e3, 1e6)
        using start and end time in nanoseconds (ns). OTel span
        start/end_time are optional."""
        if not start_time or not end_time:
            return 0
        ms_start_time = int(start_time // time_conversion)
        ms_end_time = int(end_time // time_conversion)
        return ms_end_time - ms_start_time

    def calculate_otlp_transaction_name(
        self,
        span_name: str,
    ) -> str:
        """Calculate transaction name for OTLP metrics following this order
        of decreasing precedence, truncated to 255 char:

        1. SW_APM_TRANSACTION_NAME
        2. AWS_LAMBDA_FUNCTION_NAME
        3. automated naming from span name
        4. "unknown" backup, to match core lib

        See also _SwSampler.calculate_otlp_transaction_name
        """
        if self.env_transaction_name:
            return self.env_transaction_name[:INTL_SWO_TRANSACTION_ATTR_MAX]

        if self.lambda_function_name:
            return self.lambda_function_name[:INTL_SWO_TRANSACTION_ATTR_MAX]

        if span_name:
            return span_name[:INTL_SWO_TRANSACTION_ATTR_MAX]

        return "unknown"

    def enhance_meter_attrs_with_http_span_attrs(
        self, span: "ReadableSpan", meter_attrs: dict
    ) -> dict:
        """Enhances meter_attrs with span's status code, request method if available. Current span attributes take precedence over deprecated attributes for metrics attributes values. APM uses current attributes for metrics keys.

        Default metrics attribute status code value is unavailable (0). No default for method and unset if not set on span.
        """
        status_code_new = span.attributes.get(
            self._HTTP_RESPONSE_STATUS_CODE, None
        )
        status_code_old = span.attributes.get(self._HTTP_STATUS_CODE, None)
        if status_code_new and status_code_new > 0:
            meter_attrs.update(
                {self._HTTP_RESPONSE_STATUS_CODE: status_code_new}
            )
        elif status_code_old and status_code_old > 0:
            meter_attrs.update(
                {self._HTTP_RESPONSE_STATUS_CODE: status_code_old}
            )
        # Something went wrong in OTel or instrumented service crashed early
        # if no status_code, current nor deprecated, in attributes of HTTP span
        else:
            meter_attrs.update(
                {
                    self._HTTP_RESPONSE_STATUS_CODE: self._HTTP_SPAN_STATUS_UNAVAILABLE
                }
            )

        request_method_new = span.attributes.get(
            self._HTTP_REQUEST_METHOD, None
        )
        request_method_old = span.attributes.get(self._HTTP_METHOD, None)
        if request_method_new:
            meter_attrs.update({self._HTTP_REQUEST_METHOD: request_method_new})
        elif request_method_old:
            meter_attrs.update({self._HTTP_REQUEST_METHOD: request_method_old})

        return meter_attrs

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
            meter_attrs = self.enhance_meter_attrs_with_http_span_attrs(
                span, meter_attrs
            )

        self.response_time.record(
            amount=span_time,
            attributes=meter_attrs,
        )

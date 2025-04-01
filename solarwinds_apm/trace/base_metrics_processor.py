# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING

from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import SpanKind, StatusCode

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan


logger = logging.getLogger(__name__)


class _SwBaseMetricsProcessor(SpanProcessor):
    """Solarwinds base class for metrics span processors"""

    _HTTP_METHOD = SpanAttributes.HTTP_METHOD  # "http.method"
    _HTTP_STATUS_CODE = SpanAttributes.HTTP_STATUS_CODE  # "http.status_code"

    _HTTP_SPAN_STATUS_UNAVAILABLE = 0
    _TRANSACTION_NAME = "transaction_name"

    def is_span_http(self, span: "ReadableSpan") -> bool:
        """This span from inbound HTTP request if from a SERVER by some http.method"""
        if span.kind == SpanKind.SERVER and span.attributes.get(
            self._HTTP_METHOD, None
        ):
            return True
        return False

    def get_http_status_code(self, span: "ReadableSpan") -> int:
        """Calculate HTTP status_code from span or default to UNAVAILABLE"""
        status_code = span.attributes.get(self._HTTP_STATUS_CODE, None)
        # Something went wrong in OTel or instrumented service crashed early
        # if no status_code in attributes of HTTP span
        if not status_code:
            status_code = self._HTTP_SPAN_STATUS_UNAVAILABLE
        return status_code

    def has_error(self, span: "ReadableSpan") -> bool:
        """Calculate if this span instance has_error"""
        if span.status.status_code == StatusCode.ERROR:
            return True
        return False

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

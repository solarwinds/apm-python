# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import random
from typing import TYPE_CHECKING

from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import SpanKind, StatusCode


if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_meter_manager import SolarWindsMeterManager


logger = logging.getLogger(__name__)


class SolarWindsOTLPMetricsSpanProcessor(SpanProcessor):
    # TODO If needed for both inbound and otlp metrics, refactor
    _HTTP_METHOD = SpanAttributes.HTTP_METHOD  # "http.method"
    #_HTTP_ROUTE = SpanAttributes.HTTP_ROUTE  # "http.route"
    _HTTP_STATUS_CODE = SpanAttributes.HTTP_STATUS_CODE  # "http.status_code"
    #_HTTP_URL = SpanAttributes.HTTP_URL  # "http.url"

    def __init__(
        self,
        apm_meters: "SolarWindsMeterManager",
    ) -> None:
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

        # support ssa and conform to Otel proto common_pb2
        meter_attrs = {
            "sw.nonce": random.getrandbits(64) >> 1
        }

        is_span_http = self.is_span_http(span)
        span_time = self.calculate_span_time(
            span.start_time,
            span.end_time,
        )
        has_error = self.has_error(span)

        if is_span_http:
            status_code = self.get_http_status_code(span)
            request_method = span.attributes.get(self._HTTP_METHOD, None)

            self.apm_meters.response_time.record(
                amount=span_time,
                attributes=meter_attrs,
            )
        else:
            # TODO
            pass


    # TODO If needed for both inbound and otlp metrics, refactor
    def is_span_http(self, span: "ReadableSpan") -> bool:
        """This span from inbound HTTP request if from a SERVER by some http.method"""
        if span.kind == SpanKind.SERVER and span.attributes.get(
            self._HTTP_METHOD, None
        ):
            return True
        return False

    # TODO If needed for both inbound and otlp metrics, refactor
    def has_error(self, span: "ReadableSpan") -> bool:
        """Calculate if this span instance has_error"""
        if span.status.status_code == StatusCode.ERROR:
            return True
        return False

    # TODO If needed for both inbound and otlp metrics, refactor
    def get_http_status_code(self, span: "ReadableSpan") -> int:
        """Calculate HTTP status_code from span or default to UNAVAILABLE"""
        status_code = span.attributes.get(self._HTTP_STATUS_CODE, None)
        # Something went wrong in OTel or instrumented service crashed early
        # if no status_code in attributes of HTTP span
        if not status_code:
            status_code = self._LIBOBOE_HTTP_SPAN_STATUS_UNAVAILABLE
        return status_code

    def calculate_span_time(
        self,
        start_time: int,
        end_time: int,
    ) -> int:
        """Calculate span time in ??? using start and end time
        in nanoseconds (ns). OTel span start/end_time are optional."""
        if not start_time or not end_time:
            return 0
        return int((end_time - start_time) // 1e6)

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import random
from typing import TYPE_CHECKING, Any, Tuple

from opentelemetry.metrics import get_meter_provider
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import SpanKind, StatusCode, get_tracer_provider

from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_config import SolarWindsApmConfig
    from solarwinds_apm.apm_meter_manager import SolarWindsMeterManager
    from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager


logger = logging.getLogger(__name__)


class SolarWindsOTLPMetricsSpanProcessor(SpanProcessor):
    # TODO Refactor for both inbound and otlp metrics
    #      https://swicloud.atlassian.net/browse/NH-65061
    _HTTP_METHOD = SpanAttributes.HTTP_METHOD  # "http.method"
    _HTTP_ROUTE = SpanAttributes.HTTP_ROUTE  # "http.route"
    _HTTP_STATUS_CODE = SpanAttributes.HTTP_STATUS_CODE  # "http.status_code"
    _HTTP_URL = SpanAttributes.HTTP_URL  # "http.url"

    _HTTP_SPAN_STATUS_UNAVAILABLE = 0

    def __init__(
        self,
        apm_txname_manager: "SolarWindsTxnNameManager",
        apm_config: "SolarWindsApmConfig",
        apm_meters: "SolarWindsMeterManager",
    ) -> None:
        self.apm_txname_manager = apm_txname_manager
        self.service_name = apm_config.service_name
        self.apm_meters = apm_meters

    # TODO Assumes SolarWindsInboundMetricsSpanProcessor.on_start
    #      is called to store span ID for any custom txn naming
    #      https://swicloud.atlassian.net/browse/NH-65061

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
        trans_name, _ = self.calculate_transaction_names(span)

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

        # This does not cache txn_name for span export because
        # assuming SolarWindsInboundMetricsSpanProcessor does it
        # for SW-style trace export. This processor is for OTLP-style.
        # TODO: Cache txn_name for OTLP span export?
        #       https://swicloud.atlassian.net/browse/NH-65061

        # Force flush metrics after every entry span via flush of all meters
        # including PeriodicExportingMetricReader
        logger.debug("Performing MeterProvider force_flush of metrics")
        get_meter_provider().force_flush()

        # Force flush spans that have not yet been processed
        logger.debug("Performing TracerProvider force_flush of traces")
        get_tracer_provider().force_flush()

    # TODO Refactor for both inbound and otlp metrics
    #      https://swicloud.atlassian.net/browse/NH-65061
    def is_span_http(self, span: "ReadableSpan") -> bool:
        """This span from inbound HTTP request if from a SERVER by some http.method"""
        if span.kind == SpanKind.SERVER and span.attributes.get(
            self._HTTP_METHOD, None
        ):
            return True
        return False

    # TODO Refactor for both inbound and otlp metrics
    #      https://swicloud.atlassian.net/browse/NH-65061
    def has_error(self, span: "ReadableSpan") -> bool:
        """Calculate if this span instance has_error"""
        if span.status.status_code == StatusCode.ERROR:
            return True
        return False

    # TODO Refactor for both inbound and otlp metrics
    #      https://swicloud.atlassian.net/browse/NH-65061
    def get_http_status_code(self, span: "ReadableSpan") -> int:
        """Calculate HTTP status_code from span or default to UNAVAILABLE"""
        status_code = span.attributes.get(self._HTTP_STATUS_CODE, None)
        # Something went wrong in OTel or instrumented service crashed early
        # if no status_code in attributes of HTTP span
        if not status_code:
            # TODO change if refactor
            status_code = self._HTTP_SPAN_STATUS_UNAVAILABLE
        return status_code

    # TODO Refactor for both inbound and otlp metrics
    #      https://swicloud.atlassian.net/browse/NH-65061
    # Disable pylint for compatibility with Python3.7 else TypeError
    def calculate_transaction_names(
        self, span: "ReadableSpan"
    ) -> Tuple[Any, Any]:  # pylint: disable=deprecated-typing-alias
        """Get trans_name and url_tran of this span instance."""
        url_tran = span.attributes.get(self._HTTP_URL, None)
        http_route = span.attributes.get(self._HTTP_ROUTE, None)
        trans_name = None
        custom_trans_name = self.calculate_custom_transaction_name(span)

        if custom_trans_name:
            trans_name = custom_trans_name
        elif http_route:
            trans_name = http_route
        elif span.name:
            trans_name = span.name
        return trans_name, url_tran

    # TODO Refactor for both inbound and otlp metrics
    #      https://swicloud.atlassian.net/browse/NH-65061
    def calculate_custom_transaction_name(self, span: "ReadableSpan") -> Any:
        """Get custom transaction name for trace by trace_id, if any"""
        trans_name = None
        trace_span_id = W3CTransformer.trace_and_span_id_from_context(
            span.context
        )
        custom_name = self.apm_txname_manager.get(trace_span_id)
        if custom_name:
            trans_name = custom_name
            # TODO change if refactor
            # Assume SolarWindsInboundMetricsSpanProcessor is
            # active and is doing the removal of any
            # custom txn name from cache if not sampled,
            # so not doing it here for OTLP
        return trans_name

    def calculate_span_time(
        self,
        start_time: int,
        end_time: int,
    ) -> int:
        """Calculate span time in milliseconds (ms) using start and end time
        in nanoseconds (ns). OTel span start/end_time are optional."""
        if not start_time or not end_time:
            return 0
        return int((end_time - start_time) // 1e6)

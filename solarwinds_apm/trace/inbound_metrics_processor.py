# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import TYPE_CHECKING

from solarwinds_apm.trace.base_metrics_processor import _SwBaseMetricsProcessor

# from opentelemetry.trace import TraceFlags


# from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan

    from solarwinds_apm.apm_config import SolarWindsApmConfig


logger = logging.getLogger(__name__)


class SolarWindsInboundMetricsSpanProcessor(_SwBaseMetricsProcessor):
    """SolarWinds span processor for APM-proto inbound metrics generation"""

    def __init__(
        self,
        apm_config: "SolarWindsApmConfig",
    ) -> None:
        super().__init__()
        # self._span = apm_config.extension.Span
        self.config_transaction_name = apm_config.get(self._TRANSACTION_NAME)

    def on_end(self, span: "ReadableSpan") -> None:
        """Calculates and reports inbound trace metrics.

        If trace is sampled, caches liboboe transaction name under
        a prefixed key for solarwinds_exporter. For example:

        {
            'oboe-<trace_id_01>-<span_id_01>': 'some_http_name',
            'oboe-<trace_id_02>-<span_id_02>': 'some_non_http_name',
        }
        """
        # Only calculate inbound metrics for service entry spans
        parent_span_context = span.parent
        if (
            parent_span_context
            and parent_span_context.is_valid
            and not parent_span_context.is_remote
        ):
            return

        # TODO https://swicloud.atlassian.net/browse/NH-105550
        trans_name = "foo"
        url_tran = "bar"

        is_span_http = self.is_span_http(span)
        # convert from ns to microseconds
        span_time = self.calculate_span_time(
            span.start_time,
            span.end_time,
        )
        # TODO Use `domain` for custom transaction naming after alpha/beta
        domain = None
        has_error = self.has_error(span)

        # liboboe_txn_name = None
        if is_span_http:
            # createHttpSpan needs these other params
            status_code = self.get_http_status_code(span)
            request_method = span.attributes.get(self._HTTP_METHOD, None)

            logger.debug(
                "createHttpSpan with trans_name: %s, url_tran: %s, domain: %s, span_time: %s status_code: %s, request_method: %s, has_error: %s",
                trans_name,
                url_tran,
                domain,
                span_time,
                status_code,
                request_method,
                has_error,
            )
            # liboboe_txn_name = self._span.createHttpSpan(
            #     trans_name,
            #     url_tran,
            #     domain,
            #     span_time,
            #     status_code,
            #     request_method,
            #     has_error,
            # )
        else:
            logger.debug(
                "createSpan with trans_name: %s, domain: %s, span_time: %s, has_error: %s",
                trans_name,
                domain,
                span_time,
                has_error,
            )
            # liboboe_txn_name = self._span.createSpan(
            #     trans_name,
            #     domain,
            #     span_time,
            #     has_error,
            # )

        # if span.context.trace_flags == TraceFlags.SAMPLED:
        #     # Cache txn_name for span export
        #     txname_key = f"{INTL_SWO_LIBOBOE_TXN_NAME_KEY_PREFIX}-{W3CTransformer.trace_and_span_id_from_context(span.context)}"
        #     # TO-DO https://swicloud.atlassian.net/browse/NH-105550 : replacement of liboboe txn name with the new txn name
        #     self.apm_txname_manager[txname_key] = (
        #         "To-do-txn-name"  # liboboe_txn_name
        #     )

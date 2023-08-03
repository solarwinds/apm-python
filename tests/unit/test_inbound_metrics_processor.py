# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest  # pylint: disable=unused-import

from solarwinds_apm.inbound_metrics_processor import SolarWindsInboundMetricsSpanProcessor


class TestSolarWindsInboundMetricsSpanProcessor():

    def patch_for_on_start(self, mocker):
        mock_otel_context = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.context"
        )
        mock_attach = mocker.Mock()
        mock_otel_context.configure_mock(
            **{
                "attach": mock_attach
            }
        )
        mock_otel_baggage = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.baggage"
        )
        mock_set_baggage = mocker.Mock()
        mock_otel_baggage.configure_mock(
            **{
                "set_baggage": mock_set_baggage
            }
        )
        mock_swo_baggage_key = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.INTL_SWO_CURRENT_TRACE_ENTRY_SPAN_ID"
        )
        mock_w3c = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.W3CTransformer"
        )
        mock_ts_id = mocker.Mock(return_value="some-id")
        mock_w3c.configure_mock(
            **{
                "trace_and_span_id_from_context": mock_ts_id
            }
        )
        return mock_swo_baggage_key, mock_set_baggage, mock_attach

    def test_on_start_valid_local_parent_span(self, mocker):
        """Only scenario to skip baggage set with entry span"""
        mock_swo_baggage_key, mock_set_baggage, mock_attach = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": True,
                "is_remote": False,
            }
        )
        mock_span.configure_mock(
            **{
                "parent": mock_parent
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_start(mock_span, None) is None
        mock_swo_baggage_key.assert_not_called()
        mock_set_baggage.assert_not_called()
        mock_attach.assert_not_called()

    def test_on_start_valid_remote_parent_span(self, mocker):
        mock_swo_baggage_key, mock_set_baggage, mock_attach = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": True,
                "is_remote": True,
            }
        )
        mock_span.configure_mock(
            **{
                "parent": mock_parent
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_start(mock_span, None) is None
        mock_set_baggage.assert_called_once_with(
            mock_swo_baggage_key,
            "some-id",
        )
        mock_attach.assert_called_once()

    def test_on_start_invalid_remote_parent_span(self, mocker):
        mock_swo_baggage_key, mock_set_baggage, mock_attach = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": False,
                "is_remote": True,
            }
        )
        mock_span.configure_mock(
            **{
                "parent": mock_parent
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_start(mock_span, None) is None
        mock_set_baggage.assert_called_once_with(
            mock_swo_baggage_key,
            "some-id",
        )
        mock_attach.assert_called_once()

    def test_on_start_invalid_local_parent_span(self, mocker):
        mock_swo_baggage_key, mock_set_baggage, mock_attach = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": False,
                "is_remote": False,
            }
        )
        mock_span.configure_mock(
            **{
                "parent": mock_parent
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_start(mock_span, None) is None
        mock_set_baggage.assert_called_once_with(
            mock_swo_baggage_key,
            "some-id",
        )
        mock_attach.assert_called_once()

    def test_on_start_missing_parent(self, mocker):
        mock_swo_baggage_key, mock_set_baggage, mock_attach = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "parent": None
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_start(mock_span, None) is None
        mock_set_baggage.assert_called_once_with(
            mock_swo_baggage_key,
            "some-id",
        )
        mock_attach.assert_called_once()

    def patch_for_on_end(
        self,
        mocker,
        is_span_http=True,
    ):
        mock_is_span_http = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SolarWindsInboundMetricsSpanProcessor.is_span_http"
        )
        if is_span_http:
            mock_is_span_http.configure_mock(return_value=True)
        else:
            mock_is_span_http.configure_mock(return_value=False)

        mock_has_error = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SolarWindsInboundMetricsSpanProcessor.has_error"
        )
        mock_has_error.configure_mock(return_value=False)

        mock_calculate_span_time = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SolarWindsInboundMetricsSpanProcessor.calculate_span_time"
        )
        mock_calculate_span_time.configure_mock(return_value=123)

        mock_calculate_transaction_names = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SolarWindsInboundMetricsSpanProcessor.calculate_transaction_names"
        )
        mock_calculate_transaction_names.configure_mock(return_value=("foo", "bar"))

        mock_get_http_status_code = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SolarWindsInboundMetricsSpanProcessor.get_http_status_code"
        )
        mock_get_http_status_code.configure_mock(return_value="foo-code")

        mock_create_http_span = mocker.Mock(return_value="foo-http-name")
        mock_create_span = mocker.Mock(return_value="foo-name")
        mock_ext_span = mocker.Mock()
        mock_ext_span.configure_mock(
            **{
                "createHttpSpan": mock_create_http_span,
                "createSpan": mock_create_span,
            }
        )
        mock_ext = mocker.Mock()
        mock_ext.configure_mock(
            **{
                "Span": mock_ext_span
            }
        )
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "extension": mock_ext
            }
        )

        mock_txname_manager = mocker.Mock()
        mock_set = mocker.Mock()
        mock_del = mocker.Mock()
        mock_txname_manager.configure_mock(
            **{
                "__setitem__": mock_set,
                "__delitem__": mock_del,
            }
        )

        mock_w3c = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.W3CTransformer"
        )
        mock_ts_id = mocker.Mock(return_value="some-id")
        mock_w3c.configure_mock(
            **{
                "trace_and_span_id_from_context": mock_ts_id
            }
        )

        return mock_get_http_status_code, \
            mock_create_http_span, \
            mock_create_span, \
            mock_apm_config, \
            mock_txname_manager, \
            mock_set, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error, \
            mock_calculate_transaction_names

    def test_on_end_valid_local_parent_span(self, mocker):
        """Only scenario to skip inbound metrics generation (not entry span)"""
        _, _, _, _, _, _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error, \
            mock_calculate_transaction_names = self.patch_for_on_end(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": True,
                "is_remote": False,
            }
        )
        mock_span.configure_mock(
            **{
                "parent": mock_parent
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_not_called()
        mock_calculate_span_time.assert_not_called()
        mock_has_error.assert_not_called()
        mock_calculate_transaction_names.assert_not_called()

    def test_on_end_valid_remote_parent_span(self, mocker):
        _, _, _, _, _, _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error, \
            mock_calculate_transaction_names = self.patch_for_on_end(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": True,
                "is_remote": True,
            }
        )
        mock_span.configure_mock(
            **{
                "parent": mock_parent
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_called_once()
        mock_calculate_span_time.assert_called_once()
        mock_has_error.assert_called_once()
        mock_calculate_transaction_names.assert_called_once()

    def test_on_end_invalid_remote_parent_span(self, mocker):
        _, _, _, _, _, _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error, \
            mock_calculate_transaction_names = self.patch_for_on_end(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": False,
                "is_remote": True,
            }
        )
        mock_span.configure_mock(
            **{
                "parent": mock_parent
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_called_once()
        mock_calculate_span_time.assert_called_once()
        mock_has_error.assert_called_once()
        mock_calculate_transaction_names.assert_called_once()

    def test_on_end_invalid_local_parent_span(self, mocker):
        _, _, _, _, _, _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error, \
            mock_calculate_transaction_names = self.patch_for_on_end(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": False,
                "is_remote": False,
            }
        )
        mock_span.configure_mock(
            **{
                "parent": mock_parent
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_called_once()
        mock_calculate_span_time.assert_called_once()
        mock_has_error.assert_called_once()
        mock_calculate_transaction_names.assert_called_once()

    def test_on_end_missing_parent(self, mocker):
        _, _, _, _, _, _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error, \
            mock_calculate_transaction_names = self.patch_for_on_end(mocker)
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "parent": None
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_called_once()
        mock_calculate_span_time.assert_called_once()
        mock_has_error.assert_called_once()
        mock_calculate_transaction_names.assert_called_once()

    def test_on_end_is_span_http(self, mocker):
        mock_get_http_status_code, \
            mock_create_http_span, \
            mock_create_span, \
            mock_apm_config, \
            mock_txname_manager, \
            mock_set, \
            _, _, _, _ = self.patch_for_on_end(
                mocker,
                is_span_http=True
            )

        mock_spanattributes = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_METHOD": "http.method"
            }
        )
        mock_traceflags = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.TraceFlags"
        )
        mock_traceflags.configure_mock(
            **{
                "SAMPLED": "foo-sampled"
            }
        )

        mock_span_context = mocker.Mock()
        mock_span_context.configure_mock(
            **{
                "trace_flags": "foo-sampled"
            }
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "parent": None,
                "attributes": {
                    "http.method": "foo-method"
                },
                "context": mock_span_context
            }
        )

        processor = SolarWindsInboundMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
        )
        assert processor.on_end(mock_span) is None
        mock_get_http_status_code.assert_called_once()
        mock_create_http_span.assert_called_once_with(
            "foo",
            "bar",
            None,
            123,
            "foo-code",
            "foo-method",
            False,
        )
        mock_create_span.assert_not_called()
        mock_set.assert_called_once_with("some-id", "foo-http-name")

    def test_on_end_not_is_span_http(self, mocker):
        mock_get_http_status_code, \
            mock_create_http_span, \
            mock_create_span, \
            mock_apm_config, \
            mock_txname_manager, \
            mock_set, \
            _, _, _, _ = self.patch_for_on_end(
                mocker,
                is_span_http=False
            )

        mock_traceflags = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.TraceFlags"
        )
        mock_traceflags.configure_mock(
            **{
                "SAMPLED": "foo-sampled"
            }
        )

        mock_span_context = mocker.Mock()
        mock_span_context.configure_mock(
            **{
                "trace_flags": "foo-sampled"
            }
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "parent": None,
                "context": mock_span_context
            }
        )

        processor = SolarWindsInboundMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
        )
        assert processor.on_end(mock_span) is None
        mock_get_http_status_code.assert_not_called()
        mock_create_http_span.assert_not_called()
        mock_create_span.assert_called_once_with(
            "foo",
            None,
            123,
            False,
        )
        mock_set.assert_called_once_with("some-id", "foo-name")

    def test_is_span_http_true(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_METHOD": "http.method"
            }
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "kind": "foo",
                "attributes": {
                    "http.method": "bar"
                }
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert True == processor.is_span_http(mock_span)

    def test_is_span_http_false_not_server_kind(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_METHOD": "http.method"
            }
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "kind": "not-foo-hehe",
                "attributes": {
                    "http.method": "bar"
                }
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert False == processor.is_span_http(mock_span)

    def test_is_span_http_false_no_http_method(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_METHOD": "http.method"
            }
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "kind": "foo",
                "attributes": {
                    "NOT.http.method.hehehehe": "bar"
                }
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert False == processor.is_span_http(mock_span)

    def test_has_error_true(self, mocker):
        mock_statuscode = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.StatusCode"
        )
        mock_statuscode.configure_mock(
            **{
                "ERROR": "foo"
            }
        )
        mock_span = mocker.Mock()
        mock_status = mocker.Mock()
        mock_status.configure_mock(
            **{
                "status_code": "foo"
            }
        )
        mock_span.configure_mock(
            **{
                "status": mock_status
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert True == processor.has_error(mock_span)

    def test_has_error_false(self, mocker):
        mock_statuscode = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.StatusCode"
        )
        mock_statuscode.configure_mock(
            **{
                "ERROR": "foo"
            }
        )
        mock_span = mocker.Mock()
        mock_status = mocker.Mock()
        mock_status.configure_mock(
            **{
                "status_code": "not-foo-hehehe"
            }
        )
        mock_span.configure_mock(
            **{
                "status": mock_status
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert False == processor.has_error(mock_span)

    def test_get_http_status_code_from_span(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_STATUS_CODE": "http.status_code"
            }
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "kind": "foo",
                "attributes": {
                    "http.status_code": "foo"
                }
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert "foo" == processor.get_http_status_code(mock_span)

    def test_get_http_status_code_default(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_STATUS_CODE": "http.status_code"
            }
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "kind": "foo",
                "attributes": {
                    "NOT.http.status_code.muahaha": "foo"
                }
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert 0 == processor.get_http_status_code(mock_span)

    def test_calculate_transaction_names_custom(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_URL": "http.url",
                "HTTP_ROUTE": "http.route"
            }
        )
        mock_calculate_custom = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SolarWindsInboundMetricsSpanProcessor.calculate_transaction_names"
        )
        mock_calculate_custom.configure_mock(return_value="foo")
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "attributes": {
                    "http.url": "bar"
                }
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert "foo", "bar" == processor.calculate_transaction_names(mock_span)

    def test_calculate_transaction_names_http_route(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_URL": "http.url",
                "HTTP_ROUTE": "http.route"
            }
        )
        mock_calculate_custom = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SolarWindsInboundMetricsSpanProcessor.calculate_transaction_names"
        )
        mock_calculate_custom.configure_mock(return_value=None)
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "attributes": {
                    "http.route": "foo",
                    "http.url": "bar",
                }
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert "foo", "bar" == processor.calculate_transaction_names(mock_span)

    def test_calculate_transaction_names_span_name(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_URL": "http.url",
                "HTTP_ROUTE": "http.route"
            }
        )
        mock_calculate_custom = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.SolarWindsInboundMetricsSpanProcessor.calculate_transaction_names"
        )
        mock_calculate_custom.configure_mock(return_value=None)
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "name": "foo",
                "attributes": {
                    "not.http.route.hehe": "baz",
                    "http.url": "bar",
                }
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert "foo", "bar" == processor.calculate_transaction_names(mock_span)

    def test_calculate_custom_transaction_name_none(self, mocker):
        mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.W3CTransformer"
        )
        mock_txname_manager = mocker.Mock()
        mock_get = mocker.Mock(return_value=None)
        mock_del = mocker.Mock()
        mock_txname_manager.configure_mock(
            **{
                "get": mock_get,
                "__delitem__": mock_del,
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mock_txname_manager,
            mocker.Mock(),
        )
        assert processor.calculate_custom_transaction_name(mocker.Mock()) is None
        mock_del.assert_not_called()

    def test_calculate_custom_transaction_name_present(self, mocker):
        mock_w3c = mocker.patch(
            "solarwinds_apm.inbound_metrics_processor.W3CTransformer"
        )
        mock_ts_id = mocker.Mock(return_value="some-id")
        mock_w3c.configure_mock(
            **{
                "trace_and_span_id_from_context": mock_ts_id
            }
        )
        mock_txname_manager = mocker.Mock()
        mock_get = mocker.Mock(return_value="foo")
        mock_del = mocker.Mock()
        mock_txname_manager.configure_mock(
            **{
                "get": mock_get,
                "__delitem__": mock_del,
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mock_txname_manager,
            mocker.Mock(),
        )
        assert "foo" == processor.calculate_custom_transaction_name(mocker.Mock())
        mock_del.assert_called_once_with("some-id")

    def test_calculate_span_time_missing(self, mocker):
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert 0 == processor.calculate_span_time(0, 0)
        assert 0 == processor.calculate_span_time(0, 1000)
        assert 0 == processor.calculate_span_time(1000, 0)

    def test_calculate_span_time(self, mocker):
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
            mocker.Mock(),
        )
        assert 1 == processor.calculate_span_time(2000, 3000)

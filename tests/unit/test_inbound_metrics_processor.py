# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest  # pylint: disable=unused-import

from solarwinds_apm.inbound_metrics_processor import SolarWindsInboundMetricsSpanProcessor


class TestSolarWindsInboundMetricsSpanProcessor():

    def test_on_start_valid_local_parent_span(self):
        pass

    def test_on_start(self):
        pass

    def test_on_end_valid_local_parent_span(self):
        pass

    def test_on_end_is_span_http(self):
        pass

    def test_on_end_not_is_span_http(self):
        pass

    def test_on_end_sampled(self):
        pass

    def test_on_end_not_sampled(self):
        pass

    def test_is_span_http_true(self):
        pass

    def test_is_span_http_false(self):
        pass

    def test_has_error_true(self):
        pass

    def test_has_error_false(self):
        pass

    def test_get_http_status_code_default(self):
        pass

    def test_get_http_status_code_from_span(self):
        pass

    def test_calculate_transaction_names_custom(self):
        pass

    def test_calculate_transaction_names_http_route(self):
        pass

    def test_calculate_transaction_names_span_name(self):
        pass

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

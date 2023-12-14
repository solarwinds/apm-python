# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager
from solarwinds_apm.trace import TxnNameCalculatorProcessor


class TestTxnNameCalculatorProcessor:

    def patch_on_end(self, mocker):
        mock_w3c = mocker.patch(
            "solarwinds_apm.trace.txnname_calculator_processor.W3CTransformer"
        )
        mock_ts_id = mocker.Mock(return_value="some-id")
        mock_w3c.configure_mock(
            **{
                "trace_and_span_id_from_context": mock_ts_id
            }
        )

        mocker.patch(
            "solarwinds_apm.trace.TxnNameCalculatorProcessor.calculate_transaction_names",
            return_value=("foo", "bar")
        )

    def test_on_end_valid_local_parent_span(self, mocker):
        self.patch_on_end(mocker)
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

        txn_name_mgr = SolarWindsTxnNameManager()
        processor = TxnNameCalculatorProcessor(
            txn_name_mgr,
        )
        processor.on_end(mock_span)
        assert not txn_name_mgr.get("some-id")

    def test_on_end_valid_remote_parent_span(self, mocker):
        self.patch_on_end(mocker)
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

        txn_name_mgr = SolarWindsTxnNameManager()
        processor = TxnNameCalculatorProcessor(
            txn_name_mgr,
        )
        processor.on_end(mock_span)
        assert txn_name_mgr.get("some-id") == ("foo", "bar")

    def test_on_end_invalid_remote_parent_span(self, mocker):
        self.patch_on_end(mocker)
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

        txn_name_mgr = SolarWindsTxnNameManager()
        processor = TxnNameCalculatorProcessor(
            txn_name_mgr,
        )
        processor.on_end(mock_span)
        assert txn_name_mgr.get("some-id") == ("foo", "bar")

    def test_on_end_invalid_local_parent_span(self, mocker):
        self.patch_on_end(mocker)
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

        txn_name_mgr = SolarWindsTxnNameManager()
        processor = TxnNameCalculatorProcessor(
            txn_name_mgr,
        )
        processor.on_end(mock_span)
        assert txn_name_mgr.get("some-id") == ("foo", "bar")

    def test_on_end_missing_parent(self, mocker):
        self.patch_on_end(mocker)
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "parent": None
            }
        )

        txn_name_mgr = SolarWindsTxnNameManager()
        processor = TxnNameCalculatorProcessor(
            txn_name_mgr,
        )
        processor.on_end(mock_span)
        assert txn_name_mgr.get("some-id") == ("foo", "bar")

    def test_calculate_transaction_names_span_name_default(self, mocker):
        """Otel Python span.name should always exist"""
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_URL": "http.url",
                "HTTP_ROUTE": "http.route"
            }
        )
        mock_calculate_custom = mocker.patch(
            "solarwinds_apm.trace.TxnNameCalculatorProcessor.calculate_custom_transaction_name"
        )
        mock_calculate_custom.configure_mock(return_value=None)
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "name": "foo",
                "attributes": {
                    "http.route": None,
                    "http.url": None
                }
            }
        )
        mock_get = mocker.Mock(return_value=None)
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get
            }
        )
        processor = TxnNameCalculatorProcessor(
            mocker.Mock(),
        )
        assert ("foo", None) == processor.calculate_transaction_names(mock_span)

    def test_calculate_transaction_names_custom(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_URL": "http.url",
                "HTTP_ROUTE": "http.route"
            }
        )
        mock_calculate_custom = mocker.patch(
            "solarwinds_apm.trace.TxnNameCalculatorProcessor.calculate_custom_transaction_name"
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
        processor = TxnNameCalculatorProcessor(
            mocker.Mock(),
        )
        result = processor.calculate_transaction_names(mock_span)
        assert "foo", "bar" == result

    def test_calculate_transaction_names_yes_custom_yes_config(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_URL": "http.url",
                "HTTP_ROUTE": "http.route"
            }
        )
        mock_calculate_custom = mocker.patch(
            "solarwinds_apm.trace.TxnNameCalculatorProcessor.calculate_custom_transaction_name"
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
        mock_get = mocker.Mock(return_value="not-used")
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get
            }
        )
        processor = TxnNameCalculatorProcessor(
            mocker.Mock(),
        )
        result = processor.calculate_transaction_names(mock_span)
        assert "foo", "bar" == result

    def test_calculate_transaction_names_no_custom_yes_config(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_URL": "http.url",
                "HTTP_ROUTE": "http.route"
            }
        )
        mock_calculate_custom = mocker.patch(
            "solarwinds_apm.trace.TxnNameCalculatorProcessor.calculate_custom_transaction_name"
        )
        mock_calculate_custom.configure_mock(return_value=None)
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "attributes": {
                    "http.url": "bar"
                }
            }
        )
        mock_get = mocker.Mock(return_value="foo")
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get
            }
        )
        processor = TxnNameCalculatorProcessor(
            mocker.Mock(),
        )
        result = processor.calculate_transaction_names(mock_span)
        assert "foo", "bar" == result

    def test_calculate_transaction_names_http_route(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_URL": "http.url",
                "HTTP_ROUTE": "http.route"
            }
        )
        mock_calculate_custom = mocker.patch(
            "solarwinds_apm.trace.TxnNameCalculatorProcessor.calculate_custom_transaction_name"
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
        processor = TxnNameCalculatorProcessor(
            mocker.Mock(),
        )
        result = processor.calculate_transaction_names(mock_span)
        assert "foo", "bar" == result

    def test_calculate_transaction_names_span_name_and_url(self, mocker):
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_URL": "http.url",
                "HTTP_ROUTE": "http.route"
            }
        )
        mock_calculate_custom = mocker.patch(
            "solarwinds_apm.trace.TxnNameCalculatorProcessor.calculate_custom_transaction_name"
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
        processor = TxnNameCalculatorProcessor(
            mocker.Mock(),
        )
        result = processor.calculate_transaction_names(mock_span)
        assert "foo", "bar" == result

    def test_calculate_custom_transaction_name_none(self, mocker):
        mocker.patch(
            "solarwinds_apm.trace.txnname_calculator_processor.W3CTransformer"
        )
        mock_txname_manager = mocker.Mock()
        mock_get = mocker.Mock(return_value=None)
        mock_txname_manager.configure_mock(
            **{
                "get": mock_get,
            }
        )
        processor = TxnNameCalculatorProcessor(
            mock_txname_manager,
        )
        assert processor.calculate_custom_transaction_name(mocker.Mock()) is None

    def test_calculate_custom_transaction_name_present(self, mocker):
        mock_w3c = mocker.patch(
            "solarwinds_apm.trace.txnname_calculator_processor.W3CTransformer"
        )
        mock_ts_id = mocker.Mock(return_value="some-id")
        mock_w3c.configure_mock(
            **{
                "trace_and_span_id_from_context": mock_ts_id
            }
        )
        mock_txname_manager = mocker.Mock()
        mock_get = mocker.Mock(return_value="foo")
        mock_txname_manager.configure_mock(
            **{
                "get": mock_get,
            }
        )
        processor = TxnNameCalculatorProcessor(
            mock_txname_manager,
        )
        assert "foo" == processor.calculate_custom_transaction_name(mocker.Mock())

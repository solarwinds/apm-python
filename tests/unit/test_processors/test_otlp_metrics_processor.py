# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from os import environ

from solarwinds_apm.trace import SolarWindsOTLPMetricsSpanProcessor
from solarwinds_apm.trace.tnames import TransactionNames

class TestSolarWindsOTLPMetricsSpanProcessor:

    def get_mock_apm_config(
        self,
        mocker,
        outer_txn_retval="unused",
        lambda_function_name="unused",
    ):
        mock_apm_config = mocker.Mock()
        mock_get_inner = mocker.Mock(return_value=True)
        mock_inner = mocker.Mock()
        mock_inner.configure_mock(
            **{
                "get": mock_get_inner,
            }
        )
        def outer_side_effect(cnf_key):
            if cnf_key == "experimental":
                return mock_inner
            # We mock this assuming processor does
            # one outer `get` of 'transaction_name'
            else:
                return outer_txn_retval

        mock_get_outer = mocker.Mock(
            side_effect=outer_side_effect,
        )
        mock_apm_config.configure_mock(
            **{
                "service_name": "foo-service",
                "get": mock_get_outer,
                "lambda_function_name": lambda_function_name,
            }
        )
        return mock_apm_config

    def test__init(self, mocker, mock_meter_manager):
        mock_tx_mgr = mocker.Mock()
        mock_oboe_api = mocker.Mock()
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            "foo-env-txn-name",
            "foo-lambda-name",
        )
        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_tx_mgr,
            mock_apm_config,
            mock_oboe_api,
        )
        assert processor.apm_txname_manager == mock_tx_mgr
        assert processor.service_name == "foo-service"
        assert processor.env_transaction_name == "foo-env-txn-name"
        assert processor.lambda_function_name == "foo-lambda-name"

    def test__init_not_experimental(self, mocker, mock_meter_manager):
        # TODO
        pass

    def test_calculate_otlp_transaction_name_custom(self, mocker, mock_meter_manager):
        mock_apm_config = self.get_mock_apm_config(mocker)
        tnames = TransactionNames(
            "unused",
            "unused",
            "foo-custom-name",
        )
        assert "foo-custom-name" == SolarWindsOTLPMetricsSpanProcessor(
            mocker.Mock(),
            mock_apm_config,
            mocker.Mock()
        ).calculate_otlp_transaction_name(tnames)

    def test_calculate_otlp_transaction_name_env_trans(self, mocker, mock_meter_manager):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            "foo-env-trans-name",
        )
        tnames = TransactionNames(
            "unused",
            "unused",
            None,
        )
        assert "foo-env-trans-name" == SolarWindsOTLPMetricsSpanProcessor(
            mocker.Mock(),
            mock_apm_config,
            mocker.Mock()
        ).calculate_otlp_transaction_name(tnames)

    def test_calculate_otlp_transaction_name_env_lambda(self, mocker, mock_meter_manager):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            outer_txn_retval=None,
            lambda_function_name="foo-lambda-name",
        )
        tnames = TransactionNames(
            "unused",
            "unused",
            None,
        )
        assert "foo-lambda-name" == SolarWindsOTLPMetricsSpanProcessor(
            mocker.Mock(),
            mock_apm_config,
            mocker.Mock()
        ).calculate_otlp_transaction_name(tnames)

    def test_calculate_otlp_transaction_name_default(self, mocker, mock_meter_manager):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            outer_txn_retval=None,
            lambda_function_name=None,
        )

        tnames = TransactionNames(
            "foo-trans-name",
            "unused",
            None,
        )

        assert "foo-trans-name" == SolarWindsOTLPMetricsSpanProcessor(
            mocker.Mock(),
            mock_apm_config,
            mocker.Mock()
        ).calculate_otlp_transaction_name(tnames)

    def patch_for_on_end(
        self,
        mocker,
        has_error=True,
        is_span_http=True,
        get_retval=TransactionNames("foo", "bar")
    ):
        mocker.patch(
            "solarwinds_apm.trace.SolarWindsOTLPMetricsSpanProcessor.calculate_otlp_transaction_name",
            return_value="foo",
        )

        mock_has_error = mocker.patch(
            "solarwinds_apm.trace.SolarWindsOTLPMetricsSpanProcessor.has_error"
        )
        if has_error:
            mock_has_error.configure_mock(return_value=True)
        else:
            mock_has_error.configure_mock(return_value=False)

        mock_is_span_http = mocker.patch(
            "solarwinds_apm.trace.SolarWindsOTLPMetricsSpanProcessor.is_span_http"
        )
        if is_span_http:
            mock_is_span_http.configure_mock(return_value=True)
        else:
            mock_is_span_http.configure_mock(return_value=False)

        mock_calculate_span_time = mocker.patch(
            "solarwinds_apm.trace.SolarWindsOTLPMetricsSpanProcessor.calculate_span_time"
        )
        mock_calculate_span_time.configure_mock(return_value=123)

        mock_get_http_status_code = mocker.patch(
            "solarwinds_apm.trace.SolarWindsOTLPMetricsSpanProcessor.get_http_status_code"
        )
        mock_get_http_status_code.configure_mock(return_value="foo-code")

        mock_apm_config = self.get_mock_apm_config(mocker)

        mock_txname_manager = mocker.Mock()
        mock_set = mocker.Mock()
        mock_del = mocker.Mock()
        mock_txname_manager.configure_mock(
            **{
                "__setitem__": mock_set,
                "__delitem__": mock_del,
                "get": mocker.Mock(return_value=get_retval)
            }
        )

        mock_w3c = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.W3CTransformer"
        )
        mock_ts_id = mocker.Mock(return_value="some-id")
        mock_w3c.configure_mock(
            **{
                "trace_and_span_id_from_context": mock_ts_id
            }
        )

        mock_oboe_api = mocker.Mock()

        mock_basic_span = mocker.Mock()
        mock_basic_span.configure_mock(
            **{
                "attributes": {
                    "http.method": "foo-method"
                },
            }
        )

        mock_response_time = mocker.Mock()
        mock_response_time.record = mocker.Mock()
        mock_mm = mocker.Mock()
        type(mock_mm).response_time = mock_response_time
        mocker.patch(
            "solarwinds_apm.trace.otlp_metrics_processor.SolarWindsMeterManager",
            return_value=mock_mm,
        )

        return mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            mock_basic_span

    def test_on_end_valid_local_parent_span(self, mocker):
        """Only scenario to skip OTLP metrics generation (not entry span)"""
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            _ = self.patch_for_on_end(
                mocker,
            )
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

        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_span)

        mock_response_time.record.assert_not_called()

    def test_on_end_valid_remote_parent_span(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            _ = self.patch_for_on_end(
                mocker,
            )
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
                "parent": mock_parent,
                "attributes": {
                    "http.method": "foo-method"
                }
            }
        )

        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_span)

        mock_response_time.record.assert_called_once()
        mock_response_time.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': 'true',
                        'http.status_code': 'foo-code',
                        'http.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_invalid_remote_parent_span(self, mocker, mock_meter_manager):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            _ = self.patch_for_on_end(
                mocker,
            )
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
                "parent": mock_parent,
                "attributes": {
                    "http.method": "foo-method"
                }
            }
        )

        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_span)

        mock_response_time.record.assert_called_once()
        mock_response_time.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': 'true',
                        'http.status_code': 'foo-code',
                        'http.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_invalid_local_parent_span(self, mocker, mock_meter_manager):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            _ = self.patch_for_on_end(
                mocker,
            )
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
                "parent": mock_parent,
                "attributes": {
                    "http.method": "foo-method"
                }
            }
        )

        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_span)

        mock_response_time.record.assert_called_once()
        mock_response_time.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': 'true',
                        'http.status_code': 'foo-code',
                        'http.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_missing_parent(self, mocker, mock_meter_manager):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            _ = self.patch_for_on_end(
                mocker,
            )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "parent": None,
                "attributes": {
                    "http.method": "foo-method"
                }
            }
        )

        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_span)

        mock_response_time.record.assert_called_once()
        mock_response_time.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': 'true',
                        'http.status_code': 'foo-code',
                        'http.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_missing_txn_name(self, mocker, mock_meter_manager):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                get_retval=None,
            )

        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_basic_span)

        mock_oboe_api.response_time.record.assert_not_called()

    def test_on_end_txn_name_wrong_type(self, mocker, mock_meter_manager):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                get_retval="some-str",
            )

        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_basic_span)

        mock_oboe_api.response_time.record.assert_not_called()

    def test_on_end_is_span_http_has_error(self, mocker, mock_meter_manager):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=True,
                is_span_http=True,
            )
        
        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_basic_span)

        mock_response_time.record.assert_called_once()
        mock_response_time.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': 'true',
                        'http.status_code': 'foo-code',
                        'http.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_is_span_http_not_has_error(self, mocker, mock_meter_manager):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=True,
            )
        
        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_basic_span)

        mock_response_time.record.assert_called_once()
        mock_response_time.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': 'false',
                        'http.status_code': 'foo-code',
                        'http.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_not_is_span_http_has_error(self, mocker, mock_meter_manager):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=True,
                is_span_http=False,
            )
        
        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_basic_span)

        mock_response_time.record.assert_called_once()
        mock_response_time.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': 'true',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_not_is_span_http_not_has_error(self, mocker, mock_meter_manager):
        mock_txname_manager, \
            mock_apm_config, \
            mock_oboe_api, \
            mock_response_time, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=False,
                get_retval=TransactionNames("foo", "bar"),
            )
        
        processor = SolarWindsOTLPMetricsSpanProcessor(
            mock_txname_manager,
            mock_apm_config,
            mock_oboe_api,
        )
        processor.on_end(mock_basic_span)

        mock_response_time.record.assert_called_once()
        mock_response_time.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': 'false',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )
# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm.trace import ResponseTimeProcessor

class TestResponseTimeProcessor:

    def get_mock_apm_config(
        self,
        mocker,
        outer_txn_retval="unused",
        lambda_function_name="unused",
    ):
        mock_apm_config = mocker.Mock()
        def outer_side_effect(cnf_key):
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

    def test__init(self, mocker):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            "foo-env-txn-name",
            "foo-lambda-name",
        )
        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        assert processor.service_name == "foo-service"
        assert processor.env_transaction_name == "foo-env-txn-name"
        assert processor.lambda_function_name == "foo-lambda-name"

    def test_is_span_http_true(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.trace.response_time_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.response_time_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_REQUEST_METHOD": "http.request.method"
            }
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "kind": "foo",
                "attributes": {
                    "http.request.method": "bar"
                }
            }
        )
        processor = ResponseTimeProcessor(mocker.Mock())
        assert True == processor.is_span_http(mock_span)

    def test_is_span_http_true_old_attr(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.trace.response_time_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.response_time_processor.SpanAttributes"
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
        processor = ResponseTimeProcessor(mocker.Mock())
        assert True == processor.is_span_http(mock_span)

    def test_is_span_http_false_no_http_method(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.trace.response_time_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.response_time_processor.SpanAttributes"
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
        processor = ResponseTimeProcessor(mocker.Mock())
        assert False == processor.is_span_http(mock_span)

    def test_has_error_true(self, mocker):
        mock_statuscode = mocker.patch(
            "solarwinds_apm.trace.response_time_processor.StatusCode"
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
        processor = ResponseTimeProcessor(mocker.Mock())
        assert True == processor.has_error(mock_span)

    def test_has_error_false(self, mocker):
        mock_statuscode = mocker.patch(
            "solarwinds_apm.trace.response_time_processor.StatusCode"
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
        processor = ResponseTimeProcessor(mocker.Mock())
        assert False == processor.has_error(mock_span)

    def test_calculate_span_time_missing(self, mocker):
        processor = ResponseTimeProcessor(mocker.Mock())
        assert 0 == processor.calculate_span_time(0, 0)
        assert 0 == processor.calculate_span_time(0, 1000)
        assert 0 == processor.calculate_span_time(1000, 0)

    def test_calculate_span_time_default_1e3(self, mocker):
        processor = ResponseTimeProcessor(mocker.Mock())
        assert 1 == processor.calculate_span_time(2000, 3000)

    def test_calculate_span_time_1e6(self, mocker):
        processor = ResponseTimeProcessor(mocker.Mock())
        assert 1 == processor.calculate_span_time(
            2000000,
            3000000,
            1e6,
        )

    def test_calculate_otlp_transaction_name_env_trans(self, mocker):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            "foo-env-trans-name",
        )
        assert "foo-env-trans-name" == ResponseTimeProcessor(
            mock_apm_config,
        ).calculate_otlp_transaction_name("foo-span")

    def test_calculate_otlp_transaction_name_env_trans_truncated(self, mocker):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            "foo-txn-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofoooooofooofoooofoo",
        )
        assert "foo-txn-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofoooooo" == ResponseTimeProcessor(
            mock_apm_config,
        ).calculate_otlp_transaction_name("foo-span")

    def test_calculate_otlp_transaction_name_env_lambda(self, mocker):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            outer_txn_retval=None,
            lambda_function_name="foo-lambda-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofoooooofooofoooofoo",
        )
        assert "foo-lambda-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofooo" == ResponseTimeProcessor(
            mock_apm_config,
        ).calculate_otlp_transaction_name("foo-span")

    def test_calculate_otlp_transaction_name_env_lambda_truncated(self, mocker):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            outer_txn_retval=None,
            lambda_function_name="foo-lambda-name",
        )
        assert "foo-lambda-name" == ResponseTimeProcessor(
            mock_apm_config,
        ).calculate_otlp_transaction_name("foo-span")

    def test_calculate_otlp_transaction_name_span_name(self, mocker):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            outer_txn_retval=None,
            lambda_function_name=None,
        )
        assert "foo-span" == ResponseTimeProcessor(
            mock_apm_config,
        ).calculate_otlp_transaction_name("foo-span")

    def test_calculate_otlp_transaction_name_span_name_truncated(self, mocker):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            outer_txn_retval=None,
            lambda_function_name=None,
        )
        assert "foo-span-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofooooo" == ResponseTimeProcessor(
            mock_apm_config,
        ).calculate_otlp_transaction_name("foo-span-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofoooooofooofoooofoo")

    def test_calculate_otlp_transaction_name_empty(self, mocker):
        mock_apm_config = self.get_mock_apm_config(
            mocker,
            outer_txn_retval=None,
            lambda_function_name=None,
        )
        assert "unknown" == ResponseTimeProcessor(
            mock_apm_config,
        ).calculate_otlp_transaction_name("")

    def patch_for_on_end(
        self,
        mocker,
        has_error=True,
        is_span_http=True,
        get_retval="foo",
        missing_http_attrs=False,
    ):
        mock_has_error = mocker.patch(
            "solarwinds_apm.trace.ResponseTimeProcessor.has_error"
        )
        if has_error:
            mock_has_error.configure_mock(return_value=True)
        else:
            mock_has_error.configure_mock(return_value=False)

        mock_is_span_http = mocker.patch(
            "solarwinds_apm.trace.ResponseTimeProcessor.is_span_http"
        )
        if is_span_http:
            mock_is_span_http.configure_mock(return_value=True)
        else:
            mock_is_span_http.configure_mock(return_value=False)

        mock_calculate_span_time = mocker.patch(
            "solarwinds_apm.trace.ResponseTimeProcessor.calculate_span_time"
        )
        mock_calculate_span_time.configure_mock(return_value=123)
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

        mock_basic_span = mocker.Mock()
        if missing_http_attrs:
            mock_basic_span.configure_mock(
                **{
                    "attributes": {
                        "TransactionName": "foo"
                    },
                }
            )
        else:
            mock_basic_span.configure_mock(
                **{
                    "attributes": {
                        "http.request.method": "foo-method",
                        "http.response.status_code": 200,
                        "TransactionName": "foo"
                    },
                }
            )


        mock_get_meter = mocker.patch(
            "solarwinds_apm.trace.response_time_processor.get_meter"
        )
        mock_meter = mocker.Mock()
        mock_get_meter.return_value = mock_meter
        mock_histogram= mocker.Mock()
        mock_meter.create_histogram.return_value = mock_histogram
        mock_histogram.record = mocker.Mock()

        return mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            mock_basic_span

    def test_enhance_meter_attrs_with_http_span_attrs_new_attrs(self, mocker):
        mock_apm_config = self.get_mock_apm_config(mocker)
        processor = ResponseTimeProcessor(mock_apm_config)
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "attributes": {
                "http.request.method": "GET",
                "http.response.status_code": 200
            }
        })
        
        meter_attrs = {"sw.is_error": False}
        result = processor.enhance_meter_attrs_with_http_span_attrs(mock_span, meter_attrs)
        
        assert result["http.response.status_code"] == 200
        assert result["http.request.method"] == "GET"
        assert result["sw.is_error"] == False

    def test_enhance_meter_attrs_with_http_span_attrs_old_attrs(self, mocker):
        mock_apm_config = self.get_mock_apm_config(mocker)
        processor = ResponseTimeProcessor(mock_apm_config)
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "attributes": {
                "http.method": "POST",
                "http.status_code": 404
            }
        })
        
        meter_attrs = {"sw.is_error": True}
        result = processor.enhance_meter_attrs_with_http_span_attrs(mock_span, meter_attrs)
        
        assert result["http.response.status_code"] == 404
        assert result["http.request.method"] == "POST"
        assert result["sw.is_error"] == True

    def test_enhance_meter_attrs_with_http_span_attrs_new_preferred_over_old(self, mocker):
        mock_apm_config = self.get_mock_apm_config(mocker)
        processor = ResponseTimeProcessor(mock_apm_config)
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "attributes": {
                "http.request.method": "GET",
                "http.method": "POST",
                "http.response.status_code": 200,
                "http.status_code": 500
            }
        })
        
        meter_attrs = {}
        result = processor.enhance_meter_attrs_with_http_span_attrs(mock_span, meter_attrs)
        
        assert result["http.response.status_code"] == 200
        assert result["http.request.method"] == "GET"

    def test_enhance_meter_attrs_with_http_span_attrs_zero_status_code_fallback(self, mocker):
        mock_apm_config = self.get_mock_apm_config(mocker)
        processor = ResponseTimeProcessor(mock_apm_config)
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "attributes": {
                "http.request.method": "PUT",
                "http.response.status_code": 0,
                "http.status_code": 201
            }
        })
        
        meter_attrs = {}
        result = processor.enhance_meter_attrs_with_http_span_attrs(mock_span, meter_attrs)
        
        assert result["http.response.status_code"] == 201
        assert result["http.request.method"] == "PUT"

    def test_enhance_meter_attrs_with_http_span_attrs_no_status_code(self, mocker):
        mock_apm_config = self.get_mock_apm_config(mocker)
        processor = ResponseTimeProcessor(mock_apm_config)
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "attributes": {
                "http.request.method": "DELETE"
            }
        })
        
        meter_attrs = {}
        result = processor.enhance_meter_attrs_with_http_span_attrs(mock_span, meter_attrs)
        
        assert result["http.response.status_code"] == 0
        assert result["http.request.method"] == "DELETE"

    def test_enhance_meter_attrs_with_http_span_attrs_no_method(self, mocker):
        mock_apm_config = self.get_mock_apm_config(mocker)
        processor = ResponseTimeProcessor(mock_apm_config)
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "attributes": {
                "http.response.status_code": 302
            }
        })
        
        meter_attrs = {}
        result = processor.enhance_meter_attrs_with_http_span_attrs(mock_span, meter_attrs)
        
        assert result["http.response.status_code"] == 302
        assert "http.request.method" not in result

    def test_enhance_meter_attrs_with_http_span_attrs_no_http_attrs(self, mocker):
        mock_apm_config = self.get_mock_apm_config(mocker)
        processor = ResponseTimeProcessor(mock_apm_config)
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "attributes": {
                "some.other.attr": "value"
            }
        })
        
        meter_attrs = {"existing": "value"}
        result = processor.enhance_meter_attrs_with_http_span_attrs(mock_span, meter_attrs)
        
        assert result["http.response.status_code"] == 0
        assert "http.request.method" not in result
        assert result["existing"] == "value"

    def test_on_end_valid_local_parent_span(self, mocker):
        """Only scenario to skip OTLP metrics generation (not entry span)"""
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
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

        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_span)

        mock_histogram.record.assert_not_called()

    def test_on_end_valid_remote_parent_span(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
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
                    "http.method": "foo-method",
                    "http.status_code": 200,
                    "TransactionName": "foo"
                }
            }
        )

        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_span)

        mock_histogram.record.assert_called_once()
        mock_histogram.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': True,
                        'http.response.status_code': 200,
                        'http.request.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_invalid_remote_parent_span(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
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
                    "http.method": "foo-method",
                    "http.status_code": 200,
                    "TransactionName": "foo"
                }
            }
        )

        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_span)

        mock_histogram.record.assert_called_once()
        mock_histogram.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': True,
                        'http.response.status_code': 200,
                        'http.request.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_invalid_local_parent_span(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
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
                    "http.method": "foo-method",
                    "http.response.status_code": 200,
                    "TransactionName": "foo"
                }
            }
        )

        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_span)

        mock_histogram.record.assert_called_once()
        mock_histogram.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': True,
                        'http.response.status_code': 200,
                        'http.request.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_missing_parent(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            _ = self.patch_for_on_end(
                mocker,
            )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "parent": None,
                "attributes": {
                    "http.method": "foo-method",
                    "http.response.status_code": 200,
                    "TransactionName": "foo"
                }
            }
        )

        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_span)

        mock_histogram.record.assert_called_once()
        mock_histogram.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': True,
                        'http.response.status_code': 200,
                        'http.request.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_missing_txn_name(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                get_retval=None,
            )
        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_basic_span)

    def test_on_end_txn_name_wrong_type(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                get_retval="some-str",
            )

        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_basic_span)

    def test_on_end_is_span_http_has_error(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=True,
                is_span_http=True,
            )
        
        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_basic_span)

        mock_histogram.record.assert_called_once()
        mock_histogram.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': True,
                        'http.response.status_code': 200,
                        'http.request.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_is_span_http_not_has_error(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=True,
            )
        
        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_basic_span)

        mock_histogram.record.assert_called_once()
        mock_histogram.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': False,
                        'http.response.status_code': 200,
                        'http.request.method': 'foo-method',
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_is_span_http_no_status_code_no_method(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=True,
                is_span_http=True,
                missing_http_attrs=True,
            )

        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_basic_span)

        mock_histogram.record.assert_called_once()
        mock_histogram.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': True,
                        'http.response.status_code': 0,
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_not_is_span_http_has_error(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=True,
                is_span_http=False,
            )
        
        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_basic_span)

        mock_histogram.record.assert_called_once()
        mock_histogram.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': True,
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_not_is_span_http_not_has_error(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=False,
            )
        
        processor = ResponseTimeProcessor(
            mock_apm_config,
        )
        processor.on_end(mock_basic_span)

        mock_histogram.record.assert_called_once()
        mock_histogram.record.assert_has_calls(
            [
                mocker.call(
                    amount=123,
                    attributes={
                        'sw.is_error': False,
                        'sw.transaction': 'foo'
                    }
                )
            ]
        )

    def test_on_end_http_new_status_code_attr(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            _ = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=True,
            )
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "parent": None,
            "attributes": {
                "http.request.method": "GET",
                "http.response.status_code": 200,
                "sw.transaction": "test-transaction"
            }
        })
        
        processor = ResponseTimeProcessor(mock_apm_config)
        processor.on_end(mock_span)
        
        mock_histogram.record.assert_called_once()
        call_args = mock_histogram.record.call_args
        assert call_args[1]['attributes']['http.response.status_code'] == 200
        assert call_args[1]['attributes']['http.request.method'] == "GET"

    def test_on_end_http_old_status_code_attr(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            _ = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=True,
            )
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "parent": None,
            "attributes": {
                "http.method": "POST",
                "http.status_code": 404,
                "sw.transaction": "test-transaction"
            }
        })
        
        processor = ResponseTimeProcessor(mock_apm_config)
        processor.on_end(mock_span)
        
        mock_histogram.record.assert_called_once()
        call_args = mock_histogram.record.call_args
        assert call_args[1]['attributes']['http.response.status_code'] == 404
        assert call_args[1]['attributes']['http.request.method'] == "POST"

    def test_on_end_http_new_attrs_preferred_over_old(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            _ = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=True,
            )
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "parent": None,
            "attributes": {
                "http.request.method": "GET",  # new
                "http.method": "POST",  # old (should be ignored)
                "http.response.status_code": 200,  # new
                "http.status_code": 500,  # old (should be ignored)
                "sw.transaction": "test-transaction"
            }
        })
        
        processor = ResponseTimeProcessor(mock_apm_config)
        processor.on_end(mock_span)
        
        mock_histogram.record.assert_called_once()
        call_args = mock_histogram.record.call_args
        # Should use new attributes, not old ones
        assert call_args[1]['attributes']['http.response.status_code'] == 200
        assert call_args[1]['attributes']['http.request.method'] == "GET"

    def test_on_end_http_zero_status_code_fallback(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            _ = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=True,
            )
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "parent": None,
            "attributes": {
                "http.request.method": "GET",
                "http.response.status_code": 0,  # invalid
                "http.status_code": 201,  # should be used
                "sw.transaction": "test-transaction"
            }
        })
        
        processor = ResponseTimeProcessor(mock_apm_config)
        processor.on_end(mock_span)
        
        mock_histogram.record.assert_called_once()
        call_args = mock_histogram.record.call_args
        assert call_args[1]['attributes']['http.response.status_code'] == 201

    def test_on_end_http_no_status_code_unavailable(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            _ = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=True,
            )
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "parent": None,
            "attributes": {
                "http.request.method": "GET",
                "sw.transaction": "test-transaction"
            }
        })
        
        processor = ResponseTimeProcessor(mock_apm_config)
        processor.on_end(mock_span)
        
        mock_histogram.record.assert_called_once()
        call_args = mock_histogram.record.call_args
        assert call_args[1]['attributes']['http.response.status_code'] == 0

    def test_on_end_http_fallback_to_old_method(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            _ = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=True,
            )
        
        mock_span = mocker.Mock()
        mock_span.configure_mock(**{
            "parent": None,
            "attributes": {
                "http.method": "DELETE",  # old attribute
                "http.response.status_code": 204,
                "sw.transaction": "test-transaction"
            }
        })
        
        processor = ResponseTimeProcessor(mock_apm_config)
        processor.on_end(mock_span)
        
        mock_histogram.record.assert_called_once()
        call_args = mock_histogram.record.call_args
        assert call_args[1]['attributes']['http.request.method'] == "DELETE"

    def test_on_end_non_http_span_no_http_attrs(self, mocker):
        mock_txname_manager, \
            mock_apm_config, \
            mock_histogram, \
            mock_basic_span = self.patch_for_on_end(
                mocker,
                has_error=False,
                is_span_http=False,
                missing_http_attrs=True,
            )
        
        processor = ResponseTimeProcessor(mock_apm_config)
        processor.on_end(mock_basic_span)
        
        mock_histogram.record.assert_called_once()
        call_args = mock_histogram.record.call_args
        # Should not contain HTTP attributes
        assert 'http.response.status_code' not in call_args[1]['attributes']
        assert 'http.request.method' not in call_args[1]['attributes']
        assert call_args[1]['attributes']['sw.transaction'] == "foo"

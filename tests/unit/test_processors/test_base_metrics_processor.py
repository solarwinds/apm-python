# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm.trace.base_metrics_processor import _SwBaseMetricsProcessor

class TestSwBaseMetricsProcessor:

    def test_is_span_http_true(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
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
        processor = _SwBaseMetricsProcessor(
            mocker.Mock(),
        )
        assert True == processor.is_span_http(mock_span)

    def test_is_span_http_false_not_server_kind(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
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
        processor = _SwBaseMetricsProcessor(
            mocker.Mock(),
        )
        assert False == processor.is_span_http(mock_span)

    def test_is_span_http_false_no_http_method(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
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
        processor = _SwBaseMetricsProcessor(
            mocker.Mock(),
        )
        assert False == processor.is_span_http(mock_span)

    def test_is_span_http_false_no_server_kind_no_method(self, mocker):
        mock_spankind = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanKind"
        )
        mock_spankind.configure_mock(
            **{
                "SERVER": "foo"
            }
        )
        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
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
                    "NOT.http.method.hehehehe": "bar"
                }
            }
        )
        processor = _SwBaseMetricsProcessor(
            mocker.Mock(),
        )
        assert False == processor.is_span_http(mock_span)

    def test_has_error_true(self, mocker):
        mock_statuscode = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.StatusCode"
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
        processor = _SwBaseMetricsProcessor(
            mocker.Mock(),
        )
        assert True == processor.has_error(mock_span)

    def test_has_error_false(self, mocker):
        mock_statuscode = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.StatusCode"
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
        processor = _SwBaseMetricsProcessor(
            mocker.Mock(),
        )
        assert False == processor.has_error(mock_span)

    def test_calculate_span_time_missing(self, mocker):
        processor = _SwBaseMetricsProcessor(
            mocker.Mock(),
        )
        assert 0 == processor.calculate_span_time(0, 0)
        assert 0 == processor.calculate_span_time(0, 1000)
        assert 0 == processor.calculate_span_time(1000, 0)

    def test_calculate_span_time(self, mocker):
        processor = _SwBaseMetricsProcessor(
            mocker.Mock(),
        )
        assert 1 == processor.calculate_span_time(2000, 3000)
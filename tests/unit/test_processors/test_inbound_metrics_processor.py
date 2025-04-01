# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm.trace import SolarWindsInboundMetricsSpanProcessor


class TestSolarWindsInboundMetricsSpanProcessor():

    def patch_for_on_end(
        self,
        mocker,
        is_span_http=True,
        get_retval="foo",
    ):
        mock_is_span_http = mocker.patch(
            "solarwinds_apm.trace.SolarWindsInboundMetricsSpanProcessor.is_span_http"
        )
        if is_span_http:
            mock_is_span_http.configure_mock(return_value=True)
        else:
            mock_is_span_http.configure_mock(return_value=False)

        mock_has_error = mocker.patch(
            "solarwinds_apm.trace.SolarWindsInboundMetricsSpanProcessor.has_error"
        )
        mock_has_error.configure_mock(return_value=False)

        mock_calculate_span_time = mocker.patch(
            "solarwinds_apm.trace.SolarWindsInboundMetricsSpanProcessor.calculate_span_time"
        )
        mock_calculate_span_time.configure_mock(return_value=123)

        mock_get_http_status_code = mocker.patch(
            "solarwinds_apm.trace.SolarWindsInboundMetricsSpanProcessor.get_http_status_code"
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

        mock_set = mocker.Mock()
        mock_del = mocker.Mock()

        return mock_get_http_status_code, \
            mock_create_http_span, \
            mock_create_span, \
            mock_apm_config, \
            mock_set, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error

    def test_on_end_valid_local_parent_span(self, mocker):
        """Only scenario to skip inbound metrics generation (not entry span)"""
        _, _, _, _, \
            _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error = self.patch_for_on_end(mocker)
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
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_not_called()
        mock_calculate_span_time.assert_not_called()
        mock_has_error.assert_not_called()

    def test_on_end_valid_remote_parent_span(self, mocker):
        _, _, _, _, \
            _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error = self.patch_for_on_end(mocker)
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
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_called_once()
        mock_calculate_span_time.assert_called_once()
        mock_has_error.assert_called_once()

    def test_on_end_invalid_remote_parent_span(self, mocker):
        _, _, _, _, \
             _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error = self.patch_for_on_end(mocker)
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
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_called_once()
        mock_calculate_span_time.assert_called_once()
        mock_has_error.assert_called_once()

    def test_on_end_invalid_local_parent_span(self, mocker):
        _, _, _, _, \
            _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error = self.patch_for_on_end(mocker)
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
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_called_once()
        mock_calculate_span_time.assert_called_once()
        mock_has_error.assert_called_once()

    def test_on_end_missing_parent(self, mocker):
        _, _, _, _, \
            _, \
            mock_is_span_http, \
            mock_calculate_span_time, \
            mock_has_error = self.patch_for_on_end(mocker)
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "parent": None
            }
        )
        processor = SolarWindsInboundMetricsSpanProcessor(
            mocker.Mock(),
        )
        assert processor.on_end(mock_span) is None
        mock_is_span_http.assert_called_once()
        mock_calculate_span_time.assert_called_once()
        mock_has_error.assert_called_once()

    # def test_on_end_missing_txn_name(self, mocker):
    #     mock_get_http_status_code, \
    #         mock_create_http_span, \
    #         mock_create_span, \
    #         mock_apm_config, \
    #         mock_set, \
    #         mock_is_span_http, \
    #         mock_calculate_span_time, \
    #         mock_has_error = self.patch_for_on_end(
    #             mocker,
    #             get_retval=None,
    #         )
        
    #     processor = SolarWindsInboundMetricsSpanProcessor(
    #         mocker.Mock(),
    #     )
    #     processor.on_end(mocker.Mock())
    #     mock_get_http_status_code.assert_not_called()
    #     mock_create_http_span.assert_not_called()
    #     mock_create_span.assert_not_called()
    #     mock_apm_config.assert_not_called()
    #     mock_set.assert_not_called()
    #     mock_is_span_http.assert_not_called()
    #     mock_calculate_span_time.assert_not_called()
    #     mock_has_error.assert_not_called()

    # def test_on_end_txn_name_wrong_type(self, mocker):
    #     mock_get_http_status_code, \
    #         mock_create_http_span, \
    #         mock_create_span, \
    #         mock_apm_config, \
    #         mock_set, \
    #         mock_is_span_http, \
    #         mock_calculate_span_time, \
    #         mock_has_error = self.patch_for_on_end(
    #             mocker,
    #             get_retval="some-str",
    #         )
        
    #     processor = SolarWindsInboundMetricsSpanProcessor(
    #         mocker.Mock(),
    #     )
    #     processor.on_end(mocker.Mock())
    #     mock_get_http_status_code.assert_not_called()
    #     mock_create_http_span.assert_not_called()
    #     mock_create_span.assert_not_called()
    #     mock_apm_config.assert_not_called()
    #     mock_set.assert_not_called()
    #     mock_is_span_http.assert_not_called()
    #     mock_calculate_span_time.assert_not_called()
    #     mock_has_error.assert_not_called()

    def test_on_end_is_span_http(self, mocker):
        mock_get_http_status_code, \
            mock_create_http_span, \
            mock_create_span, \
            mock_apm_config, \
            mock_set, \
            _, _, _ = self.patch_for_on_end(
                mocker,
                is_span_http=True
            )

        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_METHOD": "http.method"
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
            mock_apm_config,
        )
        assert processor.on_end(mock_span) is None
        mock_get_http_status_code.assert_called_once()
        # mock_create_http_span.assert_called_once_with(
        #     "foo",
        #     "bar",
        #     None,
        #     123,
        #     "foo-code",
        #     "foo-method",
        #     False,
        # )
        # mock_create_span.assert_not_called()
        # mock_set.assert_called_once_with("oboe-some-id", "foo-http-name")

    def test_on_end_not_is_span_http(self, mocker):
        mock_get_http_status_code, \
            mock_create_http_span, \
            mock_create_span, \
            mock_apm_config, \
            mock_set, \
            _, _, _ = self.patch_for_on_end(
                mocker,
                is_span_http=False
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
            mock_apm_config,
        )
        assert processor.on_end(mock_span) is None
        mock_get_http_status_code.assert_not_called()
        # mock_create_http_span.assert_not_called()
        # mock_create_span.assert_called_once_with(
        #     "foo",
        #     None,
        #     123,
        #     False,
        # )
        # mock_set.assert_called_once_with("oboe-some-id", "foo-name")

    def test_on_end_not_sampled_is_http(self, mocker):
        """Still submit inbound metrics but don't (re-)cache txn name because not exported"""
        mock_get_http_status_code, \
            mock_create_http_span, \
            mock_create_span, \
            mock_apm_config, \
            mock_set, \
            _, _, _ = self.patch_for_on_end(
                mocker,
                is_span_http=True
            )

        mock_spanattributes = mocker.patch(
            "solarwinds_apm.trace.base_metrics_processor.SpanAttributes"
        )
        mock_spanattributes.configure_mock(
            **{
                "HTTP_METHOD": "http.method"
            }
        )

        mock_span_context = mocker.Mock()
        mock_span_context.configure_mock(
            **{
                "trace_flags": "not-foo-sampled-hehe"
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
            mock_apm_config,
        )
        assert processor.on_end(mock_span) is None
        mock_get_http_status_code.assert_called_once()
        # mock_create_http_span.assert_called_once_with(
        #     "foo",
        #     "bar",
        #     None,
        #     123,
        #     "foo-code",
        #     "foo-method",
        #     False,
        # )
        # mock_create_span.assert_not_called()
        mock_set.assert_not_called()

    def test_on_end_not_sampled_not_is_http(self, mocker):
        """Still submit inbound metrics but don't (re-)cache txn name because not exported"""
        mock_get_http_status_code, \
            mock_create_http_span, \
            mock_create_span, \
            mock_apm_config, \
            mock_set, \
            _, _, _ = self.patch_for_on_end(
                mocker,
                is_span_http=False
            )

        mock_span_context = mocker.Mock()
        mock_span_context.configure_mock(
            **{
                "trace_flags": "not-foo-sampled-hehe"
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
            mock_apm_config,
        )
        assert processor.on_end(mock_span) is None
        mock_get_http_status_code.assert_not_called()
        # mock_create_http_span.assert_not_called()
        # mock_create_span.assert_called_once_with(
        #     "foo",
        #     None,
        #     123,
        #     False,
        # )
        mock_set.assert_not_called()

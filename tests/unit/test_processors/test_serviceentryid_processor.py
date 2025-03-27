# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm.trace import ServiceEntrySpanProcessor

class TestServiceEntrySpanProcessor():

    def patch_for_on_start(self, mocker):
        mock_otel_context = mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.context"
        )
        mock_attach = mocker.Mock()
        mock_otel_context.configure_mock(
            **{
                "attach": mock_attach
            }
        )
        mock_otel_baggage = mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.baggage"
        )
        mock_set_baggage = mocker.Mock()
        mock_otel_baggage.configure_mock(
            **{
                "set_baggage": mock_set_baggage
            }
        )
        mock_swo_baggage_key = mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.INTL_SWO_CURRENT_TRACE_ENTRY_SPAN_ID"
        )
        mock_w3c = mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.W3CTransformer"
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
        processor = ServiceEntrySpanProcessor()
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
        processor = ServiceEntrySpanProcessor()
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
        processor = ServiceEntrySpanProcessor()
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
        processor = ServiceEntrySpanProcessor()
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
        processor = ServiceEntrySpanProcessor()
        assert processor.on_start(mock_span, None) is None
        mock_set_baggage.assert_called_once_with(
            mock_swo_baggage_key,
            "some-id",
        )
        mock_attach.assert_called_once()

# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from opentelemetry.trace import NoOpTracerProvider

from solarwinds_apm.api import (
    set_transaction_name,
    solarwinds_ready,
)

class TestSetTransactionName:
    def patch_set_name(
        self,
        mocker,
        span_ready=True,
    ):
        mock_pool = mocker.patch(
            "solarwinds_apm.api.get_transaction_name_pool"
        )
        mock_pool_instance = mocker.Mock()
        mock_pool.return_value = mock_pool_instance
        mock_pool_instance.registered.return_value = "mock-registered-name"

        mocker.patch(
            "solarwinds_apm.w3c_transformer.W3CTransformer.trace_and_span_id_from_context",
            return_value="foo",
        )

        mock_context = mocker.patch(
            "solarwinds_apm.api.context"
        )
        mock_current_span = mocker.Mock(context=mock_context)
        mock_current_span.configure_mock(
            **{
                "set_attribute": mocker.Mock()
            }
        )
        mock_get_fn = mocker.Mock(return_value=None)
        if span_ready:
            mock_get_fn = mocker.Mock(return_value=mock_current_span)
   
        mock_context.configure_mock(
            **{
                "get_value": mock_get_fn
            }
        )
        return mock_context, mock_pool_instance, mock_current_span

    def test_empty_string(self, mocker):
        mock_context, mock_pool, mock_current_span = self.patch_set_name(mocker)
        assert set_transaction_name("") == False
        mock_context.get_value.assert_not_called()
        mock_pool.registered.assert_not_called()
        mock_current_span.set_attribute.assert_not_called()

    def test_agent_not_enabled_noop_tracer_provider(self, mocker):
        mock_context, mock_pool, mock_current_span = self.patch_set_name(mocker)
        mocker.patch(
            "solarwinds_apm.api.get_tracer_provider",
            return_value=NoOpTracerProvider()
        )
        assert set_transaction_name("foo") == True
        mock_context.get_value.assert_not_called()
        mock_pool.registered.assert_not_called()
        mock_current_span.set_attribute.assert_not_called()

    def test_span_not_started(self, mocker):
        mock_context, mock_pool, mock_current_span = self.patch_set_name(mocker, span_ready=False)
        assert set_transaction_name("foo") == False
        mock_context.get_value.assert_called_once()
        mock_pool.registered.assert_not_called()
        mock_current_span.set_attribute.assert_not_called()

    def test_agent_enabled(self, mocker):
        mock_context, mock_pool, mock_current_span = self.patch_set_name(mocker)
        assert set_transaction_name("bar") == True
        mock_context.get_value.assert_called_once_with("sw-current-trace-entry-span")
        mock_pool.registered.assert_called_once_with("bar")
        mock_current_span.set_attribute.assert_called_once_with("TransactionName", "mock-registered-name")

# class TestSolarWindsReady:
#     def patch_is_ready(
#         self,
#         mocker,
#         ready_retval,
#     ):
#         mock_is_ready = mocker.Mock(return_value=ready_retval)
#         mock_context = mocker.patch(
#             "solarwinds_apm.api.Context"
#         )
#         mock_context.configure_mock(
#             **{
#                 "isReady": mock_is_ready
#             }
#         )
#         return mock_is_ready
#
#     def test_bad_code_integer_response(self, mocker):
#         mock_is_ready = self.patch_is_ready(mocker, "bad-code")
#         assert solarwinds_ready(
#             integer_response=True
#         ) == 0
#         mock_is_ready.assert_called_once_with(3000)
#
#     def test_bad_code_bool_response(self, mocker):
#         mock_is_ready = self.patch_is_ready(mocker, "bad-code")
#         assert solarwinds_ready() == False
#         mock_is_ready.assert_called_once_with(3000)
#
#     def test_integer_response(self, mocker):
#         mock_is_ready = self.patch_is_ready(mocker, 1)
#         assert solarwinds_ready(
#             integer_response=True
#         ) == 1
#         mock_is_ready.assert_called_once_with(3000)
#
#     def test_bool_response(self, mocker):
#         mock_is_ready = self.patch_is_ready(mocker, 1)
#         assert solarwinds_ready() == True
#         mock_is_ready.assert_called_once_with(3000)
#
#     def test_wait_specified(self, mocker):
#         mock_is_ready = self.patch_is_ready(mocker, 1)
#         solarwinds_ready(999999)
#         mock_is_ready.assert_called_once_with(999999)

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
from solarwinds_apm.trace import TxnNameCalculatorProcessor

class TestSetTransactionName:
    def patch_set_name(
        self,
        mocker,
        processors_ok=True,
        span_ready=True,
    ):
        mock_baggage = mocker.patch(
            "solarwinds_apm.api.baggage"
        )
        if span_ready:
            get_retval = mocker.Mock(return_value="foo")
        else:
            get_retval = mocker.Mock(return_value=None)
        mock_baggage.configure_mock(
            **{
                "get_baggage": get_retval
            }
        )

        mock_txname_manager = mocker.Mock()
        mock_set = mocker.Mock()
        mock_txname_manager.configure_mock(
            **{
                "__setitem__": mock_set,
            }
        )

        if processors_ok:
            processors = [
                TxnNameCalculatorProcessor(mock_txname_manager)
            ]
        else:
            processors = ["foo"]

        mock_active_processor = mocker.Mock()
        mock_active_processor.configure_mock(
            **{
                "_span_processors": processors
            }
        )
        mock_tracer_provider = mocker.Mock()
        mock_tracer_provider.configure_mock(
            **{
                "_active_span_processor": mock_active_processor
            }
        )
        mocker.patch(
            "solarwinds_apm.api.get_tracer_provider",
            return_value=mock_tracer_provider,
        )

        return mock_set

    def test_empty_string(self, mocker):
        mock_set = self.patch_set_name(mocker)
        assert set_transaction_name("") == False
        mock_set.assert_not_called()

    def test_agent_not_enabled_noop_tracer_provider(self, mocker):
        mock_set = self.patch_set_name(mocker)
        mocker.patch(
            "solarwinds_apm.api.get_tracer_provider",
            return_value=NoOpTracerProvider()
        )
        assert set_transaction_name("foo") == True
        mock_set.assert_not_called()

    def test_missing_txn_name_processor(self, mocker):
        mock_set = self.patch_set_name(mocker, processors_ok=False)
        assert set_transaction_name("foo") == False
        mock_set.assert_not_called()

    def test_span_not_started(self, mocker):
        mock_set = self.patch_set_name(mocker, span_ready=False)
        assert set_transaction_name("foo") == False
        mock_set.assert_not_called()

    def test_cached_agent_enabled(self, mocker):
        mock_set = self.patch_set_name(mocker)
        assert set_transaction_name("bar") == True
        mock_set.assert_called_once_with("foo", "bar")

class TestSolarWindsReady:
    def patch_is_ready(
        self,
        mocker,
        ready_retval,
    ):
        mock_is_ready = mocker.Mock(return_value=ready_retval)
        mock_context = mocker.patch(
            "solarwinds_apm.api.Context"
        )
        mock_context.configure_mock(
            **{
                "isReady": mock_is_ready
            }
        )
        return mock_is_ready

    def test_bad_code_integer_response(self, mocker):
        mock_is_ready = self.patch_is_ready(mocker, "bad-code")
        assert solarwinds_ready(
            integer_response=True
        ) == 0
        mock_is_ready.assert_called_once_with(3000)

    def test_bad_code_bool_response(self, mocker):
        mock_is_ready = self.patch_is_ready(mocker, "bad-code")
        assert solarwinds_ready() == False
        mock_is_ready.assert_called_once_with(3000)

    def test_integer_response(self, mocker):
        mock_is_ready = self.patch_is_ready(mocker, 1)
        assert solarwinds_ready(
            integer_response=True
        ) == 1
        mock_is_ready.assert_called_once_with(3000)

    def test_bool_response(self, mocker):
        mock_is_ready = self.patch_is_ready(mocker, 1)
        assert solarwinds_ready() == True
        mock_is_ready.assert_called_once_with(3000)

    def test_wait_specified(self, mocker):
        mock_is_ready = self.patch_is_ready(mocker, 1)
        solarwinds_ready(999999)
        mock_is_ready.assert_called_once_with(999999)

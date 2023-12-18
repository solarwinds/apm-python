# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm.trace import TxnNameCleanupProcessor


class TestTxnNameCleanupProcessor:

    def test_on_end_present(self, mocker):
        mock_w3c = mocker.patch(
            "solarwinds_apm.trace.txnname_cleanup_processor.W3CTransformer"
        )
        mock_ts_id = mocker.Mock(return_value="foo-id")
        mock_w3c.configure_mock(
            **{
                "trace_and_span_id_from_context": mock_ts_id
            }
        )

        mock_txname_manager = mocker.Mock()
        mock_get = mocker.Mock(return_value="not-none")
        mock_del = mocker.Mock()
        mock_txname_manager.configure_mock(
            **{
                "__delitem__": mock_del,
                "get": mock_get,
            }
        )

        processor = TxnNameCleanupProcessor(mock_txname_manager)
        processor.on_end(mocker.Mock())
        # Gets and dels
        mock_get.assert_called_once_with("foo-id")
        mock_del.assert_called_once_with("foo-id")

    def test_on_end_not_present(self, mocker):
        mock_w3c = mocker.patch(
            "solarwinds_apm.trace.txnname_cleanup_processor.W3CTransformer"
        )
        mock_ts_id = mocker.Mock(return_value="foo-id")
        mock_w3c.configure_mock(
            **{
                "trace_and_span_id_from_context": mock_ts_id
            }
        )

        mock_txname_manager = mocker.Mock()
        mock_get = mocker.Mock(return_value=None)
        mock_del = mocker.Mock()
        mock_txname_manager.configure_mock(
            **{
                "__delitem__": mock_del,
                "get": mock_get,
            }
        )

        processor = TxnNameCleanupProcessor(mock_txname_manager)
        processor.on_end(mocker.Mock())
        # Gets but doesn't del
        mock_get.assert_called_once_with("foo-id")
        mock_del.assert_not_called()

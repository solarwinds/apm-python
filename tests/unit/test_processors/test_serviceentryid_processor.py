# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from solarwinds_apm.apm_constants import (
    INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN,
    INTL_SWO_TRANSACTION_ATTR_MAX,
)
from solarwinds_apm.trace import ServiceEntrySpanProcessor

class TestServiceEntrySpanProcessor():

    def patch_for_on_start(self, mocker):
        mock_pool = mocker.Mock()
        mock_registered = mocker.Mock(return_value="mock-registered-name")
        mock_pool.configure_mock(
            **{
                "registered": mock_registered,
            }
        )
        mock_get_transaction_name_pool = mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.get_transaction_name_pool",
            return_value=mock_pool,
        )
        mock_otel_context = mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.context"
        )
        mock_attach = mocker.Mock()
        mock_detach = mocker.Mock()
        mock_set_value = mocker.Mock()
        mock_set_value.return_value = "foo-set-return"
        mock_otel_context.configure_mock(
            **{
                "attach": mock_attach,
                "detach": mock_detach,
                "set_value": mock_set_value,
            }
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
        return mock_get_transaction_name_pool, mock_otel_context

    def test_on_start_valid_local_parent_span(self, mocker):
        """Only scenario to skip context set with entry span"""
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": True,
                "is_remote": False,
            }
        )
        mock_attrs_get = mocker.Mock(return_value=None)
        mock_span.configure_mock(
            **{
                "parent": mock_parent,
                "attributes.get": mock_attrs_get,
            }
        )
        processor = ServiceEntrySpanProcessor()
        assert processor.on_start(mock_span, None) is None
        mock_attrs_get.assert_not_called()
        mock_context.set_value.assert_not_called()
        mock_context.attach.assert_not_called()
        mock_pool.registered.assert_not_called()

    def test_on_start_valid_remote_parent_span(self, mocker):
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": True,
                "is_remote": True,
            }
        )
        mock_attrs_get = mocker.Mock(return_value=None)
        mock_span.configure_mock(
            **{
                "parent": mock_parent,
                "attributes.get": mock_attrs_get,
            }
        )
        processor = ServiceEntrySpanProcessor()
        assert processor.on_start(mock_span, None) is None
        mock_attrs_get.assert_has_calls(
            [
                mocker.call("faas.name", None),
                mocker.call("http.route", None),
                mocker.call("url.path", None)
            ]
        )
        mock_context.set_value.assert_called_once_with(
            INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN,
            mock_span,
        )
        mock_context.attach.assert_called_once_with(
            "foo-set-return",
        )

    def test_on_start_invalid_remote_parent_span(self, mocker):
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": False,
                "is_remote": True,
            }
        )
        mock_attrs_get = mocker.Mock(return_value=None)
        mock_span.configure_mock(
            **{
                "parent": mock_parent,
                "attributes.get": mock_attrs_get,
            }
        )
        processor = ServiceEntrySpanProcessor()
        assert processor.on_start(mock_span, None) is None
        mock_attrs_get.assert_has_calls(
            [
                mocker.call("faas.name", None),
                mocker.call("http.route", None),
                mocker.call("url.path", None)
            ]
        )
        mock_context.set_value.assert_called_once_with(
            INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN,
            mock_span,
        )
        mock_context.attach.assert_called_once_with(
            "foo-set-return",
        )

    def test_on_start_invalid_local_parent_span(self, mocker):
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": False,
                "is_remote": False,
            }
        )
        mock_attrs_get = mocker.Mock(return_value=None)
        mock_span.configure_mock(
            **{
                "parent": mock_parent,
                "attributes.get": mock_attrs_get,
            }
        )
        processor = ServiceEntrySpanProcessor()
        assert processor.on_start(mock_span, None) is None
        mock_attrs_get.assert_has_calls(
            [
                mocker.call("faas.name", None),
                mocker.call("http.route", None),
                mocker.call("url.path", None)
            ]
        )
        mock_context.set_value.assert_called_once_with(
            INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN,
            mock_span,
        )
        mock_context.attach.assert_called_once_with(
            "foo-set-return",
        )

    def test_on_start_missing_parent(self, mocker):
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_attrs_get = mocker.Mock(return_value=None)
        mock_span.configure_mock(
            **{
                "parent": None,
                "attributes.get": mock_attrs_get,
            }
        )
        processor = ServiceEntrySpanProcessor()
        assert processor.on_start(mock_span, None) is None
        mock_attrs_get.assert_has_calls(
            [
                mocker.call("faas.name", None),
                mocker.call("http.route", None),
                mocker.call("url.path", None)
            ]
        )
        mock_context.set_value.assert_called_once_with(
            INTL_SWO_OTEL_CONTEXT_ENTRY_SPAN,
            mock_span,
        )
        mock_context.attach.assert_called_once_with(
            "foo-set-return",
        )

    def test_on_start_faas_name(self, mocker):
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.get_transaction_name_pool",
            return_value=mock_pool,
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "attributes.get": mocker.Mock(
                    side_effect=lambda key, default=None: "faas-value" if key == "faas.name" else default
                )
            }
        )
        processor = ServiceEntrySpanProcessor()
        processor.set_default_transaction_name = mocker.Mock()
        processor.on_start(mock_span, None)
        processor.set_default_transaction_name.assert_called_once_with(
            mock_span, mock_pool, "faas-value"
        )

    def test_on_start_lambda_function_name(self, mocker):
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.get_transaction_name_pool",
            return_value=mock_pool,
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "attributes.get": mocker.Mock(return_value=None)
            }
        )
        mocker.patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "lambda-function"})
        processor = ServiceEntrySpanProcessor()
        processor.set_default_transaction_name = mocker.Mock()
        processor.on_start(mock_span, None)
        processor.set_default_transaction_name.assert_called_once_with(
            mock_span, mock_pool, "lambda-function"[:INTL_SWO_TRANSACTION_ATTR_MAX]
        )

    def test_on_start_http_route(self, mocker):
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.get_transaction_name_pool",
            return_value=mock_pool,
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "attributes.get": mocker.Mock(
                    side_effect=lambda key, default=None: "http-route" if key == "http.route" else default
                )
            }
        )
        processor = ServiceEntrySpanProcessor()
        processor.set_default_transaction_name = mocker.Mock()
        processor.on_start(mock_span, None)
        processor.set_default_transaction_name.assert_called_once_with(
            mock_span, mock_pool, "http-route", resolve=True
        )

    def test_on_start_url_path(self, mocker):
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.get_transaction_name_pool",
            return_value=mock_pool,
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "attributes.get": mocker.Mock(
                    side_effect=lambda key, default=None: "url-path" if key == "url.path" else default
                )
            }
        )
        processor = ServiceEntrySpanProcessor()
        processor.set_default_transaction_name = mocker.Mock()
        processor.on_start(mock_span, None)
        processor.set_default_transaction_name.assert_called_once_with(
            mock_span, mock_pool, "url-path", resolve=True
        )

    def test_on_start_default(self, mocker):
        mock_pool, mock_context = self.patch_for_on_start(mocker)
        mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.get_transaction_name_pool",
            return_value=mock_pool,
        )
        mock_span = mocker.Mock()
        mock_span.configure_mock(
            **{
                "attributes.get": mocker.Mock(return_value=None),
                "name": "default-span-name",
            }
        )
        processor = ServiceEntrySpanProcessor()
        processor.set_default_transaction_name = mocker.Mock()
        processor.on_start(mock_span, None)
        processor.set_default_transaction_name.assert_called_once_with(
            mock_span, mock_pool, "default-span-name"
        )

    def test_on_end_valid_local_parent_span(self, mocker):
        _, mock_context = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": True,
                "is_remote": False,
            }
        )
        mock_attrs_get = mocker.Mock(return_value=None)
        mock_span.configure_mock(
            **{
                "parent": mock_parent,
                "attributes.get": mock_attrs_get,
            }
        )
        processor = ServiceEntrySpanProcessor()
        assert processor.on_end(mock_span) is None
        mock_context.detach.assert_not_called()

    def test_on_end_valid_remote_parent_span(self, mocker):
        _, mock_context = self.patch_for_on_start(mocker)
        mock_span = mocker.Mock()
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": True,
                "is_remote": True,
            }
        )
        mock_attrs_get = mocker.Mock(return_value=None)
        mock_span.configure_mock(
            **{
                "parent": mock_parent,
                "attributes.get": mock_attrs_get,
            }
        )

        mock_w3c = mocker.patch(
            "solarwinds_apm.trace.serviceentry_processor.W3CTransformer.trace_and_span_id_from_context",
            return_value="some-id",
        )
        processor = ServiceEntrySpanProcessor()
        processor.context_tokens = {"some-id": "mock-token"}
        assert processor.on_end(mock_span) is None
        mock_context.detach.assert_called_once_with("mock-token")

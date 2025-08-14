# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ParentBased
from opentelemetry.trace import NoOpTracerProvider

from solarwinds_apm.api import (
    set_transaction_name,
    solarwinds_ready,
)
from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.oboe.http_sampler import HttpSampler
from solarwinds_apm.oboe.json_sampler import JsonSampler
from solarwinds_apm.sampler import ParentBasedSwSampler
from solarwinds_apm.tracer_provider import SolarwindsTracerProvider


class TestSetTransactionName:
    def patch_set_name(
        self,
        mocker,
        span_ready=True,
    ):
        mock_pool = mocker.patch("solarwinds_apm.api.get_transaction_name_pool")
        mock_pool_instance = mocker.Mock()
        mock_pool.return_value = mock_pool_instance
        mock_pool_instance.registered.return_value = "mock-registered-name"

        mocker.patch(
            "solarwinds_apm.w3c_transformer.W3CTransformer.trace_and_span_id_from_context",
            return_value="foo",
        )

        mock_context = mocker.patch("solarwinds_apm.api.context")
        mock_current_span = mocker.Mock(context=mock_context)
        mock_current_span.configure_mock(**{"set_attribute": mocker.Mock()})
        mock_get_fn = mocker.Mock(return_value=None)
        if span_ready:
            mock_get_fn = mocker.Mock(return_value=mock_current_span)

        mock_context.configure_mock(**{"get_value": mock_get_fn})
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
            "solarwinds_apm.api.get_tracer_provider", return_value=NoOpTracerProvider()
        )
        assert set_transaction_name("foo") == True
        mock_context.get_value.assert_not_called()
        mock_pool.registered.assert_not_called()
        mock_current_span.set_attribute.assert_not_called()

    def test_span_not_started(self, mocker):
        mock_context, mock_pool, mock_current_span = self.patch_set_name(
            mocker, span_ready=False
        )
        assert set_transaction_name("foo") == False
        mock_context.get_value.assert_called_once()
        mock_pool.registered.assert_not_called()
        mock_current_span.set_attribute.assert_not_called()

    def test_agent_enabled(self, mocker):
        mock_context, mock_pool, mock_current_span = self.patch_set_name(mocker)
        assert set_transaction_name("bar") == True
        mock_context.get_value.assert_called_once_with("sw-current-trace-entry-span")
        mock_pool.registered.assert_called_once_with("bar")
        mock_current_span.set_attribute.assert_called_once_with(
            "TransactionName", "mock-registered-name"
        )


class TestSolarWindsReady:
    def test_parentbasedsw_sampler_ready(self, mocker):
        def get_side_effect(param):
            if param == "service_key":
                return "foo:bar"
            else:
                return "foo"

        mock_apmconfig = mocker.Mock(spec=SolarWindsApmConfig)
        mock_apmconfig.service_key = "foo:bar"
        mock_apmconfig.configure_mock(
            **{
                "agent_enabled": True,
                "get": mocker.Mock(side_effect=get_side_effect),
                "service_name": "foo-service",
                "is_lambda": False,
            }
        )

        mock_http_sampler = mocker.Mock(spec=HttpSampler)
        mock_http_sampler.configure_mock(
            **{"wait_until_ready": mocker.Mock(return_value=True)}
        )
        mocker.patch(
            "solarwinds_apm.sampler.HttpSampler",
            return_value=mock_http_sampler,
        )
        mock_sampler = ParentBasedSwSampler(mock_apmconfig)
        mock_tracer_provider = mocker.Mock(spec=SolarwindsTracerProvider)
        mock_tracer_provider.configure_mock(
            **{
                "sampler": mock_sampler,
            }
        )
        mocker.patch(
            "solarwinds_apm.configurator.trace.get_tracer_provider",
            return_value=mock_tracer_provider,
        )
        assert solarwinds_ready() == True

    def test_parentbasedsw_not_ready(self, mocker):
        def get_side_effect(param):
            if param == "service_key":
                return "foo:bar"
            else:
                return "foo"

        mock_apmconfig = mocker.Mock(spec=SolarWindsApmConfig)
        mock_apmconfig.service_key = "foo:bar"
        mock_apmconfig.configure_mock(
            **{
                "agent_enabled": True,
                "get": mocker.Mock(side_effect=get_side_effect),
                "service_name": "foo-service",
                "is_lambda": False,
            }
        )

        mock_http_sampler = mocker.Mock(spec=HttpSampler)
        mock_http_sampler.configure_mock(
            **{"wait_until_ready": mocker.Mock(return_value=False)}
        )
        mocker.patch(
            "solarwinds_apm.sampler.HttpSampler",
            return_value=mock_http_sampler,
        )
        mock_sampler = ParentBasedSwSampler(mock_apmconfig)
        mock_tracer_provider = mocker.Mock(spec=SolarwindsTracerProvider)
        mock_tracer_provider.configure_mock(
            **{
                "sampler": mock_sampler,
            }
        )
        mocker.patch(
            "solarwinds_apm.configurator.trace.get_tracer_provider",
            return_value=mock_tracer_provider,
        )
        assert solarwinds_ready() == False

    def test_http_sampler_ready(self, mocker):
        mock_sampler = mocker.Mock(spec=HttpSampler)
        mock_sampler.configure_mock(
            **{"wait_until_ready": mocker.Mock(return_value=True)}
        )
        mock_tracer_provider = mocker.Mock(spec=SolarwindsTracerProvider)
        mock_tracer_provider.configure_mock(
            **{
                "sampler": mock_sampler,
            }
        )
        mocker.patch(
            "solarwinds_apm.configurator.trace.get_tracer_provider",
            return_value=mock_tracer_provider,
        )
        assert solarwinds_ready() == True

    def test_http_sampler_not_ready(self, mocker):
        mock_sampler = mocker.Mock(spec=HttpSampler)
        mock_sampler.configure_mock(
            **{"wait_until_ready": mocker.Mock(return_value=False)}
        )
        mock_tracer_provider = mocker.Mock(spec=SolarwindsTracerProvider)
        mock_tracer_provider.configure_mock(
            **{
                "sampler": mock_sampler,
            }
        )
        mocker.patch(
            "solarwinds_apm.configurator.trace.get_tracer_provider",
            return_value=mock_tracer_provider,
        )
        assert solarwinds_ready() == False

    def test_json_sampler_ready(self, mocker):
        mock_sampler = mocker.Mock(spec=JsonSampler)
        mock_sampler.configure_mock(
            **{"wait_until_ready": mocker.Mock(return_value=True)}
        )
        mock_tracer_provider = mocker.Mock(spec=SolarwindsTracerProvider)
        mock_tracer_provider.configure_mock(
            **{
                "sampler": mock_sampler,
            }
        )
        mocker.patch(
            "solarwinds_apm.configurator.trace.get_tracer_provider",
            return_value=mock_tracer_provider,
        )
        assert solarwinds_ready() == True

    def test_json_sampler_not_ready(self, mocker):
        mock_sampler = mocker.Mock(spec=JsonSampler)
        mock_sampler.configure_mock(
            **{"wait_until_ready": mocker.Mock(return_value=False)}
        )
        mock_tracer_provider = mocker.Mock(spec=SolarwindsTracerProvider)
        mock_tracer_provider.configure_mock(
            **{
                "sampler": mock_sampler,
            }
        )
        mocker.patch(
            "solarwinds_apm.configurator.trace.get_tracer_provider",
            return_value=mock_tracer_provider,
        )
        assert solarwinds_ready() == False

    def test_other_sampler(self, mocker):
        mock_sampler = mocker.Mock(spec=ParentBased)
        mock_tracer_provider = mocker.Mock(spec=SolarwindsTracerProvider)
        mock_tracer_provider.configure_mock(
            **{
                "sampler": mock_sampler,
            }
        )
        mocker.patch(
            "solarwinds_apm.configurator.trace.get_tracer_provider",
            return_value=mock_tracer_provider,
        )
        assert solarwinds_ready() == False

    def test_other_tracer_provider(self, mocker):
        mock_tracer_provider = mocker.Mock(spec=TracerProvider)
        mocker.patch(
            "solarwinds_apm.configurator.trace.get_tracer_provider",
            return_value=mock_tracer_provider,
        )
        assert solarwinds_ready() == False

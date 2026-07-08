# © 2024 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from opentelemetry.sdk.resources import Resource

from solarwinds_apm import apm_config

# pylint: disable=unused-import
from .fixtures.env_vars import fixture_mock_env_vars

class TestSolarWindsApmConfigServiceName:
    def test__calculate_service_name_is_lambda(self, mocker):
        mock_calc_proto = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig._calculate_service_name_apm_proto"
        )
        mock_calc_lambda = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig._calculate_service_name_lambda"
        )
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.calculate_is_lambda",
            return_value=True,
        )
        init_resource = Resource.create()
        test_resource = Resource.create()
        test_config = apm_config.SolarWindsApmConfig(init_resource)
        test_config._calculate_service_name(
            True,
            test_resource,
        )
        mock_calc_proto.assert_not_called()
        # called twice because of init, and we call again
        mock_calc_lambda.assert_has_calls(
            [
                mocker.call(init_resource),
                mocker.call(test_resource),
            ]
        )

    def test__calculate_service_name_not_is_lambda(self, mocker):
        mock_calc_proto = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig._calculate_service_name_apm_proto"
        )
        mock_calc_lambda = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig._calculate_service_name_lambda"
        )
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.calculate_is_lambda",
            return_value=False,
        )
        init_resource = Resource.create()
        test_resource = Resource.create()
        test_config = apm_config.SolarWindsApmConfig(init_resource)
        test_config._calculate_service_name(
            True,
            test_resource,
        )
        # called twice because of init, and we call again
        mock_calc_proto.assert_has_calls(
            [
                mocker.call(False, init_resource),
                mocker.call(True, test_resource),
            ]
        )
        mock_calc_lambda.assert_not_called()


class TestSolarWindsApmConfigServiceNameApmProto:
    def test__calculate_service_name_apm_proto_agent_disabled(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name_apm_proto(
            False,
            {}
        )
        assert result == ""

    def test__calculate_service_name_apm_proto_no_otel_service_name(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name_apm_proto(
            True,
            Resource.create({"service.name": None})
        )
        assert result == "sw_service_name"

    def test__calculate_service_name_apm_proto_default_unknown_otel_service_name(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name_apm_proto(
            True,
            # default is unknown_service
            Resource.create()
        )
        assert result == "sw_service_name"

    def test__calculate_service_name_apm_proto_use_otel_service_name(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name_apm_proto(
            True,
            Resource.create({"service.name": "foobar"})
        )
        assert result == "foobar"

    def test__calculate_service_name_apm_proto_malformed_service_key_only_token(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "token:",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name_apm_proto(
            True,
            Resource.create()  # default is unknown_service
        )
        assert result == ""

    def test__calculate_service_name_apm_proto_non_string_service_key(
        self,
        mocker,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._SolarWindsApmConfig__config["service_key"] = 123
        result = test_config._calculate_service_name_apm_proto(
            True,
            Resource.create()  # default is unknown_service
        )
        assert result == ""

class TestSolarWindsApmConfigServiceNameLambda:
    def test__calculate_service_name_lambda_no_otel_name(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "AWS_LAMBDA_FUNCTION_NAME": "foo-fn",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name_lambda(
            Resource.create({})
        )
        assert result == "foo-fn"

    def test__calculate_service_name_lambda_empty_otel_name(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "AWS_LAMBDA_FUNCTION_NAME": "foo-fn",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name_lambda(
            Resource.create({"service.name": ""})
        )
        assert result == "foo-fn"

    def test__calculate_service_name_lambda_otel_name_unknown(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "AWS_LAMBDA_FUNCTION_NAME": "foo-fn",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name_lambda(
            Resource.create({"service.name": "unknown_service"})
        )
        assert result == "foo-fn"

    def test__calculate_service_name_lambda_otel_name_ok(
        self,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name_lambda(
            Resource.create({"service.name": "foo-service-name"})
        )
        assert result == "foo-service-name"


class TestSolarWindsApmConfigLazyResourceEvaluation:
    """Test lazy evaluation of otel_resource parameter for Resource Detector setting of service name."""

    def test_init_with_none_resource_calls_create(self, mocker, mock_env_vars):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "token:ignored-service-key",
        })
        mock_resource = Resource.create({"service.name": "test-service"})
        mock_create = mocker.patch(
            "solarwinds_apm.apm_config.Resource.create",
            return_value=mock_resource
        )
        test_config = apm_config.SolarWindsApmConfig()
        
        # Verify Resource.create() was called during init
        mock_create.assert_called_once()
        # Verify service name was calculated from the created resource
        assert test_config.service_name == "test-service"

    def test_init_with_explicit_resource_no_create_call(self, mocker, mock_env_vars):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "token:ignored-service-key",
        })
        explicit_resource = Resource.create({"service.name": "explicit-service"})
        mock_create = mocker.patch(
            "solarwinds_apm.apm_config.Resource.create",
            return_value=Resource.create()
        )
        test_config = apm_config.SolarWindsApmConfig(otel_resource=explicit_resource)
        
        # Verify Resource.create() was NOT called
        mock_create.assert_not_called()
        # Verify service name was calculated from the explicit resource
        assert test_config.service_name == "explicit-service"

    def test_init_with_azure_detector_attributes(self, mocker, mock_env_vars):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "token:ignored-service-key",
        })
        # Simulate what Azure detector would set
        azure_resource = Resource.create({
            "service.name": "my-azure-app-service",
            "cloud.provider": "azure",
            "cloud.platform": "azure_app_service",
            "cloud.resource_id": "/subscriptions/abc/resourceGroups/rg/providers/Microsoft.Web/sites/my-azure-app-service",
        })
        test_config = apm_config.SolarWindsApmConfig(otel_resource=azure_resource)
        
        # Verify service name came from Azure detector
        assert test_config.service_name == "my-azure-app-service"

    def test_init_fallback_to_service_key_when_unknown_service(self, mocker, mock_env_vars):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "token:fallback-service-name",
        })
        unknown_resource = Resource.create({"service.name": "unknown_service"})
        test_config = apm_config.SolarWindsApmConfig(otel_resource=unknown_resource)
        assert test_config.service_name == "fallback-service-name"

    def test_init_no_fallback_when_detector_sets_name(self, mocker, mock_env_vars):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "token:should-not-be-used",
        })
        detector_resource = Resource.create({"service.name": "detector-set-name"})
        
        test_config = apm_config.SolarWindsApmConfig(otel_resource=detector_resource)
        # Verify service name came from detector, not service key
        assert test_config.service_name == "detector-set-name"

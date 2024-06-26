# © 2024 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from typing import Any

from solarwinds_apm.sampler import _SwSampler


class Test_SwSampler_calculate_otlp_tname():

    def test_calculate_otlp_name_env_var(self, mocker):

        def config_get(param) -> Any:
            if param == "transaction_name":
                return "foo-txn"
            else:
                return "foo"

        mock_get = mocker.Mock(
            side_effect=config_get
        )
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get,
                "lambda_function_name": "foo-lambda",
            }
        )
        mock_reporter = mocker.Mock()
        mock_oboe_api = mocker.Mock()
        sampler = _SwSampler(mock_apm_config, mock_reporter, mock_oboe_api)
        assert sampler.calculate_otlp_transaction_name("foo-span") == "foo-txn"

    def test_calculate_otlp_name_env_var_truncated(self, mocker):

        def config_get(param) -> Any:
            if param == "transaction_name":
                return "foo-txn-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofoooooofooofoooofoo"
            else:
                return "foo"

        mock_get = mocker.Mock(
            side_effect=config_get
        )
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get,
                "lambda_function_name": "foo-lambda",
            }
        )
        mock_reporter = mocker.Mock()
        mock_oboe_api = mocker.Mock()
        sampler = _SwSampler(mock_apm_config, mock_reporter, mock_oboe_api)
        assert sampler.calculate_otlp_transaction_name("foo-span") == "foo-txn-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofoooooo"

    def test_calculate_otlp_name_lambda(self, mocker):

        def config_get(param) -> Any:
            return None

        mock_get = mocker.Mock(
            side_effect=config_get
        )
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get,
                "lambda_function_name": "foo-lambda",
            }
        )
        mock_reporter = mocker.Mock()
        mock_oboe_api = mocker.Mock()
        sampler = _SwSampler(mock_apm_config, mock_reporter, mock_oboe_api)
        assert sampler.calculate_otlp_transaction_name("foo-span") == "foo-lambda"

    def test_calculate_otlp_name_lambda_truncated(self, mocker):

        def config_get(param) -> Any:
            return None

        mock_get = mocker.Mock(
            side_effect=config_get
        )
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get,
                "lambda_function_name": "foo-lambda-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofoooooofooofoooofoo",
            }
        )
        mock_reporter = mocker.Mock()
        mock_oboe_api = mocker.Mock()
        sampler = _SwSampler(mock_apm_config, mock_reporter, mock_oboe_api)
        assert sampler.calculate_otlp_transaction_name("foo-span") == "foo-lambda-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofooo"

    def test_calculate_otlp_name_span_name(self, mocker):

        def config_get(param) -> Any:
            return None

        mock_get = mocker.Mock(
            side_effect=config_get
        )
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get,
                "lambda_function_name": None,
            }
        )
        mock_reporter = mocker.Mock()
        mock_oboe_api = mocker.Mock()
        sampler = _SwSampler(mock_apm_config, mock_reporter, mock_oboe_api)
        assert sampler.calculate_otlp_transaction_name("foo-span") == "foo-span"

    def test_calculate_otlp_name_span_name_truncated(self, mocker):

        def config_get(param) -> Any:
            return None

        mock_get = mocker.Mock(
            side_effect=config_get
        )
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get,
                "lambda_function_name": None,
            }
        )
        mock_reporter = mocker.Mock()
        mock_oboe_api = mocker.Mock()
        sampler = _SwSampler(mock_apm_config, mock_reporter, mock_oboe_api)
        assert sampler.calculate_otlp_transaction_name(
            "foo-span-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofoooooofooofoooofoo"
        ) == "foo-span-ffoooofofooooooofooofooooofofofofoooooofoooooooooffoffooooooffffofooooofffooooooofoooooffoofofoooooofffofooofoffoooofooofoooooooooooooofooffoooofofooofoooofoofooffooooofoofooooofoooooffoofffoffoooooofoooofoooffooffooofofooooooffffooofoooooofooooo"

    def test_calculate_otlp_name_empty(self, mocker):

        def config_get(param) -> Any:
            return None

        mock_get = mocker.Mock(
            side_effect=config_get
        )
        mock_apm_config = mocker.Mock()
        mock_apm_config.configure_mock(
            **{
                "get": mock_get,
                "lambda_function_name": None,
            }
        )
        mock_reporter = mocker.Mock()
        mock_oboe_api = mocker.Mock()
        sampler = _SwSampler(mock_apm_config, mock_reporter, mock_oboe_api)
        assert sampler.calculate_otlp_transaction_name("") == "unknown"

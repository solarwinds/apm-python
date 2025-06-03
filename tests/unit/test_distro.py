# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest

from opentelemetry.environment_variables import (
    OTEL_LOGS_EXPORTER,
    OTEL_METRICS_EXPORTER,
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)
from opentelemetry.sdk.environment_variables import (
    OTEL_EXPORTER_OTLP_COMPRESSION,
    OTEL_EXPORTER_OTLP_ENDPOINT,
    OTEL_EXPORTER_OTLP_HEADERS,
    OTEL_EXPORTER_OTLP_METRICS_DEFAULT_HISTOGRAM_AGGREGATION,
    OTEL_EXPORTER_OTLP_PROTOCOL,
)

from solarwinds_apm import distro


class TestDistro:
    @pytest.fixture(autouse=True)
    def before_and_after_each(self):
        # Save the current environment
        original_env = os.environ.copy()

        yield

        # Restore the original environment
        os.environ.clear()
        os.environ.update(original_env)

    def test_new_initializes_class_variables(self, mocker):
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.distro.SolarWindsApmConfig.get_cnf_dict",
            return_value={"foo": "bar"},
        )
        mock_calculate_metrics_enabled = mocker.patch(
            "solarwinds_apm.distro.SolarWindsApmConfig.calculate_metrics_enabled", return_value="qux",
        )

        instance = distro.SolarWindsDistro()
        assert instance._cnf_dict == {"foo": "bar"}
        assert instance._instrumentor_metrics_enabled == "qux"
        mock_get_cnf_dict.assert_called_once()
        mock_calculate_metrics_enabled.assert_called_once_with({"foo": "bar"})

    def test__log_python_runtime(self, mocker):
        mock_plat = mocker.patch(
            "solarwinds_apm.distro.platform"
        )
        mock_py_vers = mocker.Mock()
        mock_plat.configure_mock(
            **{
                "python_version": mock_py_vers
            }
        )
        mock_sys = mocker.patch(
            "solarwinds_apm.distro.sys"
        )
        mock_version_info = mocker.Mock()
        mock_version_info.configure_mock(
            **{
                "major": 3,
                "minor": 8,
            }
        )
        type(mock_sys).version_info = mock_version_info
        mock_logger = mocker.patch(
            "solarwinds_apm.distro.logger"
        )
        mock_info = mocker.Mock()
        mock_warning = mocker.Mock()
        mock_logger.configure_mock(
            **{
                "info": mock_info,
                "warning": mock_warning,
            }
        )

        distro.SolarWindsDistro()._log_python_runtime()
        mock_py_vers.assert_called_once()
        mock_info.assert_called_once()
        mock_warning.assert_not_called()

    def test__log_python_runtime_warning(self, mocker):
        mock_plat = mocker.patch(
            "solarwinds_apm.distro.platform"
        )
        mock_py_vers = mocker.Mock()
        mock_plat.configure_mock(
            **{
                "python_version": mock_py_vers
            }
        )
        mock_sys = mocker.patch(
            "solarwinds_apm.distro.sys"
        )
        mock_version_info = mocker.Mock()
        mock_version_info.configure_mock(
            **{
                "major": 3,
                "minor": 7,
            }
        )
        type(mock_sys).version_info = mock_version_info
        mock_logger = mocker.patch(
            "solarwinds_apm.distro.logger"
        )
        mock_info = mocker.Mock()
        mock_error = mocker.Mock()
        mock_logger.configure_mock(
            **{
                "info": mock_info,
                "error": mock_error,
            }
        )

        distro.SolarWindsDistro()._log_python_runtime()
        mock_py_vers.assert_called_once()
        mock_info.assert_called_once()
        mock_error.assert_called_once()

    def test__log_runtime(self, mocker):
        mocker.patch(
            "solarwinds_apm.distro.apm_version",
            "foo-version",
        )
        mocker.patch(
            "solarwinds_apm.distro.sdk_version",
            "bar-version",
        )
        mocker.patch(
            "solarwinds_apm.distro.inst_version",
            "baz-version",
        )
        mock_logger = mocker.patch(
            "solarwinds_apm.distro.logger"
        )
        mock_info = mocker.Mock()
        mock_logger.configure_mock(
            **{
                "info": mock_info,
            }
        )
        mock_pytime = mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro._log_python_runtime"
        )

        distro.SolarWindsDistro()._log_runtime()
        mock_pytime.assert_called_once()
        mock_info.assert_has_calls(
            [
                mocker.call(
                    "SolarWinds APM Python %s",
                    "foo-version",
                ),
                mocker.call(
                    "OpenTelemetry %s/%s",
                    "bar-version",
                    "baz-version",
                ),
            ]
        )

    def test__get_token_from_service_key_missing(self, mocker):
        os.environ.pop("SW_APM_SERVICE_KEY", None)
        assert distro.SolarWindsDistro()._get_token_from_service_key() is None

    def test__get_token_from_service_key_bad_format(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "missing-service-name"
            }
        )
        assert distro.SolarWindsDistro()._get_token_from_service_key() is None

    def test__get_token_from_service_key_ok(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar-name"
            }
        )
        assert distro.SolarWindsDistro()._get_token_from_service_key() == "foo-token"

    def test_configure_no_env(self, mocker):
        os.environ.pop("SW_APM_SERVICE_KEY", "")
        mocker.patch.dict(os.environ, {})
        distro.SolarWindsDistro()._configure()
        # No env vars set, so uses all these defaults
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_EXPORTER_OTLP_COMPRESSION] == "gzip"
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp"
        assert os.environ[OTEL_METRICS_EXPORTER] == "otlp"
        assert os.environ[OTEL_LOGS_EXPORTER] == "otlp"
        assert os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] == "http/protobuf"
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20None"
        assert os.environ[OTEL_EXPORTER_OTLP_METRICS_DEFAULT_HISTOGRAM_AGGREGATION] == "base2_exponential_bucket_histogram"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_exporter(self, mocker):
        mocker.patch.dict(
            os.environ, 
                {
                    "SW_APM_SERVICE_KEY": "foo-token:bar",
                    "OTEL_TRACES_EXPORTER": "foobar",
                    "OTEL_METRICS_EXPORTER": "baz",
                    "OTEL_LOGS_EXPORTER": "qux",
                }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"
        assert os.environ[OTEL_METRICS_EXPORTER] == "baz"
        assert os.environ[OTEL_LOGS_EXPORTER] == "qux"
        assert os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] == "http/protobuf"
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_invalid_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                OTEL_EXPORTER_OTLP_PROTOCOL: "foo"
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        # Invalid protocol still set; let upstream Configurator handle it
        assert os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] == "foo"
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp"
        assert os.environ[OTEL_METRICS_EXPORTER] == "otlp"
        assert os.environ[OTEL_LOGS_EXPORTER] == "otlp"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_valid_protocol_http(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                OTEL_EXPORTER_OTLP_PROTOCOL: "http/protobuf"
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] == "http/protobuf"
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp"
        assert os.environ[OTEL_METRICS_EXPORTER] == "otlp"
        assert os.environ[OTEL_LOGS_EXPORTER] == "otlp"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_valid_protocol_grpc(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                OTEL_EXPORTER_OTLP_PROTOCOL: "grpc"
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        # Distro will only setdefault PROTOCOL as grpc
        # and will still setdefault EXPORTERS as http like default distro
        assert os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] == "grpc"
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp"
        assert os.environ[OTEL_METRICS_EXPORTER] == "otlp"
        assert os.environ[OTEL_LOGS_EXPORTER] == "otlp"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_exporter_and_valid_protocol_http(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
                "OTEL_TRACES_EXPORTER": "foobar",
                "OTEL_METRICS_EXPORTER": "baz",
                "OTEL_LOGS_EXPORTER": "qux",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] == "http/protobuf"
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"
        assert os.environ[OTEL_METRICS_EXPORTER] == "baz"
        assert os.environ[OTEL_LOGS_EXPORTER] == "qux"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_exporter_and_valid_protocol_grpc(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
                "OTEL_TRACES_EXPORTER": "foobar",
                "OTEL_METRICS_EXPORTER": "baz",
                "OTEL_LOGS_EXPORTER": "qux",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] == "grpc"
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"
        assert os.environ[OTEL_METRICS_EXPORTER] == "baz"
        assert os.environ[OTEL_LOGS_EXPORTER] == "qux"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_endpoint(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://foo.bar.com:443",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] == "http/protobuf"
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://foo.bar.com:443"
        assert os.environ.get(OTEL_EXPORTER_OTLP_HEADERS) is None
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp"
        assert os.environ[OTEL_METRICS_EXPORTER] == "otlp"
        assert os.environ[OTEL_LOGS_EXPORTER] == "otlp"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_service_key_only(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"

    def test_configure_env_service_key_and_collector_only(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "apm.collector.na-02.cloud.solarwinds.com",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-02.cloud.solarwinds.com:443"

    def test_configure_env_service_key_and_collector_only_dev(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "apm.collector.na-01.dev-ssp.solarwinds.com",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.dev-ssp.solarwinds.com:443"

    def test_configure_env_service_key_and_collector_only_stg(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "apm.collector.na-02.st-ssp.solarwinds.com",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-02.st-ssp.solarwinds.com:443"

    def test_configure_env_service_key_and_collector_only_invalid(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "www.google.com",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"

    def test_configure_env_service_key_and_collector_only_invalid_otel(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "otel.collector.na-02.cloud.solarwinds.com",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"

    def test_configure_env_service_key_and_collector_and_otel_exporter(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "apm.collector.na-02.cloud.solarwinds.com",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.collector.na-03.cloud.solarwinds.com:443",
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-03.cloud.solarwinds.com:443"

    def test_configure_env_service_key_and_collector_from_file_no_env(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_COLLECTOR": "",
            },
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsApmConfig.get_cnf_dict",
            return_value={
                "collector": "apm.collector.eu-01.st-ssp.solarwinds.com"
            },
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.eu-01.st-ssp.solarwinds.com:443"

    def test_configure_env_service_key_and_collector_from_env_no_file(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_COLLECTOR": "apm.collector.jp-01.st-ssp.solarwinds.com",
            },
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsApmConfig.get_cnf_dict",
            return_value={},
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.jp-01.st-ssp.solarwinds.com:443"

    def test_configure_env_service_key_and_collector_from_env_and_file(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_COLLECTOR": "apm.collector.jp-01.st-ssp.solarwinds.com",
            },
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsApmConfig.get_cnf_dict",
            return_value={
                "collector": "apm.collector.eu-01.st-ssp.solarwinds.com"
            },
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.jp-01.st-ssp.solarwinds.com:443"

    def test_configure_env_headers_otel_endpoint_none(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"

    def test_configure_env_headers_otel_endpoint_default(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.collector.na-01.cloud.solarwinds.com:443",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"

    def test_configure_env_headers_otel_endpoint_resolved(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.collector.eu-01.st-ssp.solarwinds.com:443",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.eu-01.st-ssp.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"

    def test_configure_env_headers_otel_endpoint_non_swo(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://my-collector/",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://my-collector/"
        assert os.environ.get(OTEL_EXPORTER_OTLP_HEADERS) is None

    def test_configure_env_headers_otel_endpoint_fake_swo(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.collector.solarwinds.com",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.solarwinds.com"
        assert os.environ.get(OTEL_EXPORTER_OTLP_HEADERS) is None

    def test_configure_env_headers_otel_headers(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_HEADERS": "foo=bar,baz=qux",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_EXPORTER_OTLP_PROTOCOL] == "http/protobuf"
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "foo=bar,baz=qux"
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp"
        assert os.environ[OTEL_METRICS_EXPORTER] == "otlp"
        assert os.environ[OTEL_LOGS_EXPORTER] == "otlp"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_headers_otel_headers_endpoint_default(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_HEADERS": "foo=bar,baz=qux",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.collector.na-01.cloud.solarwinds.com:443",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "foo=bar,baz=qux"

    def test_configure_env_headers_otel_headers_endpoint_resolved(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_HEADERS": "foo=bar,baz=qux",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.collector.eu-01.st-ssp.solarwinds.com:443",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.eu-01.st-ssp.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "foo=bar,baz=qux"

    def test_configure_env_headers_otel_headers_endpoint_non_swo(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "OTEL_EXPORTER_OTLP_HEADERS": "foo=bar,baz=qux",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://my-collector/",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://my-collector/"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "foo=bar,baz=qux"

    def test_configure_env_headers_swo_collector_invalid(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "https://not-valid-will-default-exporter/",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"

    def test_configure_env_headers_swo_collector_invalid_not_apm(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "https://otel.collector.eu-01.st-ssp.solarwinds.com:443",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"

    def test_configure_env_headers_swo_collector_valid_resolved(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "apm.collector.eu-01.st-ssp.solarwinds.com",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.eu-01.st-ssp.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"

    def test_configure_env_headers_otel_headers_swo_collector_invalid(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "https://not-valid-will-default-exporter/",
                "OTEL_EXPORTER_OTLP_HEADERS": "foo=bar,baz=qux",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "foo=bar,baz=qux"

    def test_configure_env_headers_otel_headers_swo_collector_invalid_not_apm(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "https://otel.collector.eu-01.st-ssp.solarwinds.com:443",
                "OTEL_EXPORTER_OTLP_HEADERS": "foo=bar,baz=qux",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.na-01.cloud.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "foo=bar,baz=qux"

    def test_configure_env_headers_otel_headers_swo_collector_valid_resolved(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "apm.collector.eu-01.st-ssp.solarwinds.com",
                "OTEL_EXPORTER_OTLP_HEADERS": "foo=bar,baz=qux",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.eu-01.st-ssp.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "foo=bar,baz=qux"

    def test_configure_env_headers_otel_endpoint_vs_swo_collector_both_valid(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "apm.collector.eu-01.st-ssp.solarwinds.com",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.collector.jp-01.st-dev.solarwinds.com:443",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "https://otel.collector.jp-01.st-dev.solarwinds.com:443"
        assert os.environ[OTEL_EXPORTER_OTLP_HEADERS] == "authorization=Bearer%20foo-token"

    def test_configure_env_headers_otel_endpoint_non_swo_vs_swo_collector(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar",
                "SW_APM_COLLECTOR": "apm.collector.eu-01.st-ssp.solarwinds.com",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "http://my-export-endpoint",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_ENDPOINT] == "http://my-export-endpoint"
        assert os.environ.get(OTEL_EXPORTER_OTLP_HEADERS) is None

    def test_configure_env_metrics_default_histogram_aggregation(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_METRICS_DEFAULT_HISTOGRAM_AGGREGATION": "foo",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_EXPORTER_OTLP_METRICS_DEFAULT_HISTOGRAM_AGGREGATION] == "foo"

    def test_configure_env_propagators(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "tracecontext,solarwinds_propagator,foobar"})
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,solarwinds_propagator,foobar"
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_load_instrumentor_aws_lambda_not_lambda_env(self, mocker):
        mock_apm_config = mocker.patch(
            "solarwinds_apm.distro.SolarWindsApmConfig"
        )
        mock_apm_config.configure_mock(
            **{
                "calculate_is_lambda": mocker.Mock(return_value=False)
            }
        )

        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "load": mock_load,
                "name": "aws-lambda",
            }
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        mock_instrument.assert_called_once_with(
            **{
                "foo": "bar",
            }
        )  

    def test_load_instrumentor_aws_lambda_lambda_env(self, mocker):
        mock_apm_config = mocker.patch(
            "solarwinds_apm.distro.SolarWindsApmConfig"
        )
        mock_apm_config.configure_mock(
            **{
                "calculate_is_lambda": mocker.Mock(return_value=True)
            }
        )

        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "load": mock_load,
                "name": "aws-lambda",
            }
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        mock_instrument.assert_not_called()

    def test_load_instrumentor_no_commenting_configured(self, mocker):
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "load": mock_load
            }
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        mock_instrument.assert_called_once_with(
            **{
                "foo": "bar",
            }
        )  

    def test_load_instrumentor_enable_commenting_not_on_list(self, mocker):
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "name": "not-on-list",
                "load": mock_load,
            }
        )
        mocker.patch(
            "solarwinds_apm.distro._SQLCOMMENTERS",
            [
                "this-is-on-the-list"
            ]
        )       
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.get_enable_commenter_env_map",
            return_value={
                "not-on-list": {
                    "enable_commenter": True,
                    "enable_attribute_commenter": False,
                }
            }
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.detect_commenter_options",
            return_value="foo-options"
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        # Commenting not enabled because not on list
        mock_instrument.assert_called_once_with(
            foo="bar",
        )

    def test_load_instrumentor_enable_commenting_false(self, mocker):
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "name": "foo-instrumentor",
                "load": mock_load,
            }
        )
        mocker.patch(
            "solarwinds_apm.distro._SQLCOMMENTERS",
            [
                "foo-instrumentor"
            ]
        )   
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.get_enable_commenter_env_map",
            return_value={
                "foo-instrumentor": {
                    "enable_commenter": False,
                    "enable_attribute_commenter": True,
                }
            }
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.detect_commenter_options",
            return_value="foo-options"
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        mock_instrument.assert_called_once_with(
            foo="bar",
            # If passed without enable_commenter=True, this does nothing
            enable_attribute_commenter=True,
        )

    def test_load_instrumentor_enable_commenting_true(self, mocker):
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "name": "foo-instrumentor",
                "load": mock_load,
            }
        )
        mocker.patch(
            "solarwinds_apm.distro._SQLCOMMENTERS",
            [
                "foo-instrumentor"
            ]
        )   
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.get_enable_commenter_env_map",
            return_value={
                "foo-instrumentor": {
                    "enable_commenter": True,
                    "enable_attribute_commenter": False,
                }
            }
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.detect_commenter_options",
            return_value="foo-options"
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        mock_instrument.assert_called_once_with(
            commenter_options="foo-options",
            enable_commenter=True,
            foo="bar",
        )

    def test_load_instrumentor_enable_commenting_not_django(self, mocker):
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "name": "foo-instrumentor",
                "load": mock_load,
            }
        )
        mocker.patch(
            "solarwinds_apm.distro._SQLCOMMENTERS",
            [
                "foo-instrumentor"
            ]
        )       
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.get_enable_commenter_env_map",
            return_value={
                "foo-instrumentor": {
                    "enable_commenter": True,
                    "enable_attribute_commenter": False,
                }
            }
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.detect_commenter_options",
            return_value="foo-options"
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        mock_instrument.assert_called_once_with(
            commenter_options="foo-options",
            enable_commenter=True,
            foo="bar",
        )

    def test_load_instrumentor_enable_commenting_django(self, mocker):
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "name": "django",
                "load": mock_load,
            }
        )
        mocker.patch(
            "solarwinds_apm.distro._SQLCOMMENTERS",
            [
                "django"
            ]
        )       
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.get_enable_commenter_env_map",
            return_value={
                "django": {
                    "enable_commenter": True,
                    "enable_attribute_commenter": False,
                }
            }
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.detect_commenter_options",
            return_value="foo-options"
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        # No commenter_options because Django reads settings.py instead
        mock_instrument.assert_called_once_with(
            is_sql_commentor_enabled=True,
            foo="bar",
        )

    def test_load_instrumentor_metrics_enabled(self, mocker):
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsApmConfig.calculate_metrics_enabled",
            return_value=True,
        )
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "name": "foo-instrumentor",
                "load": mock_load,
            }
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        # No custom meter_provider set
        mock_instrument.assert_called_once_with(
            foo="bar",
        )

    def test_load_instrumentor_metrics_disabled(self, mocker):
        mocker.patch(
            "solarwinds_apm.distro.NoOpMeterProvider",
            return_value="noop"
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsApmConfig.calculate_metrics_enabled",
            return_value=False,
        )
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "name": "foo-instrumentor",
                "load": mock_load,
            }
        )
        distro.SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        # passed custom meter_provider as no-op
        mock_instrument.assert_called_once_with(
            foo="bar",
            meter_provider="noop",
        )

    def test_get_enable_commenter_env_map_none(self, mocker):
        mocker.patch.dict(os.environ, {})
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "flask": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "sqlalchemy": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
        }

    def test_get_enable_commenter_env_map_invalid_just_a_comma(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_ENABLED_SQLCOMMENT": ",",
                "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE": ",",
            }
        )
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "flask": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "sqlalchemy": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
        }

    def test_get_enable_commenter_env_map_invalid_missing_equals_sign_single_val(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_ENABLED_SQLCOMMENT": "django",
                "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE": "django",
            }
        )
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "flask": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "sqlalchemy": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
        }

    def test_get_enable_commenter_env_map_invalid_missing_equals_sign_multiple_first(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_ENABLED_SQLCOMMENT": "django,flask=true",
                "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE": "django,flask=false",
            }
        )
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "flask": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "psycopg": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "sqlalchemy": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
        }

    def test_get_enable_commenter_env_map_invalid_missing_equals_sign_multiple_last(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_ENABLED_SQLCOMMENT": "flask=true,django",
                "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE": "flask=false,django",
            }
        )
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "flask": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "psycopg": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "sqlalchemy": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
        }

    def test_get_enable_commenter_env_map_valid_ignored_values(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_ENABLED_SQLCOMMENT": "django=true,flask=foobar,psycopg=123",
                "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE": "django=false,flask=foobar,psycopg=123",
            }
        )
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "flask": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "sqlalchemy": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
        }

    def test_get_enable_commenter_env_map_valid_mixed_case(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_ENABLED_SQLCOMMENT": "dJAnGO=tRuE,FlaSK=TrUe",
                "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE": "dJAnGO=fAlSe,FlaSK=FaLsE",
            }
        )
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "flask": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "psycopg": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "sqlalchemy": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
        }

    def test_get_enable_commenter_env_map_valid_whitespace_stripped(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_ENABLED_SQLCOMMENT": "django  =  true  ,  flask=  true  ",
                "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE": "django  =  false  ,  flask=  false  ",
            }
        )
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "flask": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "psycopg": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "sqlalchemy": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
        }

    def test_get_enable_commenter_env_map_valid_update_existing(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_ENABLED_SQLCOMMENT": "django=true,flask=true,psycopg=true,psycopg2=true,sqlalchemy=true",
                "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE": "django=false,flask=false,psycopg=false,psycopg2=false,sqlalchemy=false",
            }
        )
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "flask": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "psycopg": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "psycopg2": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "sqlalchemy": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
        }

    def test_get_enable_commenter_env_map_valid_ignores_if_not_on_list(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_ENABLED_SQLCOMMENT": "flask=true,foobar=true",
                "SW_APM_ENABLED_SQLCOMMENT_ATTRIBUTE": "flask=false,foobar=false",
            }
        )
        assert distro.SolarWindsDistro().get_enable_commenter_env_map() == {
            "django": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "flask": {
                "enable_commenter": True,
                "enable_attribute_commenter": False,
            },
            "psycopg": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "psycopg2": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
            "sqlalchemy": {
                "enable_commenter": False,
                "enable_attribute_commenter": True,
            },
        }

    def test_detect_commenter_options_not_set(self, mocker):
        mocker.patch.dict(os.environ, {})
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result == {}

    def test_detect_commenter_options_strip_mixed(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_OPTIONS_SQLCOMMENT": "invalid-kv,   foofoo=TrUe   ,barbar  =  faLSE,   bazbaz=qux  "})
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result.get("foofoo") == True
        assert result.get("barbar") == False
        assert result.get("bazbaz") is None

    def test_detect_commenter_options_invalid_kv_ignored(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_OPTIONS_SQLCOMMENT": "invalid-kv,foo=bar"})
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result == {}

    def test_detect_commenter_options_valid_kvs(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_OPTIONS_SQLCOMMENT": "foo=true,bar=FaLSe"})
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result == {
            "foo": True,
            "bar": False,
        }

    def test_detect_commenter_options_strip_whitespace_ok(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_OPTIONS_SQLCOMMENT": "   foo   =   tRUe   , bar = falsE "
            }
        )
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result.get("foo") == True
        assert result.get("bar") == False

    def test_detect_commenter_options_strip_mix(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_OPTIONS_SQLCOMMENT": "invalid-kv,   foo=TrUe   ,bar  =  faLSE,   baz=qux  "})
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result.get("foo") == True
        assert result.get("bar") == False
        assert result.get("baz") is None

    def test_get_semconv_opt_in(self):
        # TODO: Support other signal types when available
        assert distro.SolarWindsDistro().get_semconv_opt_in() == "http"
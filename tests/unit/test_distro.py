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
    OTEL_BSP_EXPORT_TIMEOUT,
    OTEL_EXPORTER_OTLP_LOGS_ENDPOINT,
    OTEL_EXPORTER_OTLP_LOGS_HEADERS,
    OTEL_EXPORTER_OTLP_LOGS_PROTOCOL,
)

from solarwinds_apm import distro


class TestDistro:
    @pytest.fixture(autouse=True)
    def before_and_after_each(self):
        # Save any env vars for later just in case
        # Save any env vars for later just in case
        old_otel_ev = os.environ.get("OTEL_EXPORTER_OTLP_LOGS_HEADERS", None)
        if old_otel_ev:
            del os.environ["OTEL_EXPORTER_OTLP_LOGS_HEADERS"]
        old_key = os.environ.get("SW_APM_SERVICE_KEY", None)
        if old_key:
            del os.environ["SW_APM_SERVICE_KEY"]

        # Wait for test
        yield

        # Restore old env vars
        if old_key:
            os.environ["SW_APM_SERVICE_KEY"] = old_key
        if old_otel_ev:
            os.environ["OTEL_EXPORTER_OTLP_LOGS_HEADERS"] = old_otel_ev

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
        mocker.patch.dict(os.environ, {})
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

    def test_configure_set_otlp_log_defaults(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar-name"
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ.get(OTEL_EXPORTER_OTLP_LOGS_HEADERS) == f"authorization=Bearer%20foo-token"
        assert os.environ.get(OTEL_EXPORTER_OTLP_LOGS_PROTOCOL) == "http/protobuf"
        assert os.environ.get(OTEL_EXPORTER_OTLP_LOGS_ENDPOINT) == "https://otel.collector.na-01.cloud.solarwinds.com:443/v1/logs"
        assert os.environ.get(OTEL_LOGS_EXPORTER) == "otlp_proto_http"

    def test_configure_set_otlp_log_defaults_lambda(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "SW_APM_SERVICE_KEY": "foo-token:bar-name",
                "AWS_LAMBDA_FUNCTION_NAME": "foo",
                "LAMBDA_TASK_ROOT": "foo",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ.get(OTEL_EXPORTER_OTLP_LOGS_HEADERS) is None
        assert os.environ.get(OTEL_EXPORTER_OTLP_LOGS_PROTOCOL) == "http/protobuf"
        assert os.environ.get(OTEL_EXPORTER_OTLP_LOGS_ENDPOINT) == "https://otel.collector.na-01.cloud.solarwinds.com:443/v1/logs"
        assert os.environ.get(OTEL_LOGS_EXPORTER) == "otlp_proto_http"

    def test_configure_set_bsp_timeout_default_lambda(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "AWS_LAMBDA_FUNCTION_NAME": "foo",
                "LAMBDA_TASK_ROOT": "foo",
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_BSP_EXPORT_TIMEOUT] == "250"

    def test_configure_set_bsp_timeout_default_not_lambda(self, mocker):
        mocker.patch.dict(os.environ, {})
        distro.SolarWindsDistro()._configure()
        assert os.environ.get(OTEL_BSP_EXPORT_TIMEOUT) is None

    def test_configure_no_env(self, mocker):
        mocker.patch.dict(os.environ, {})
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"
        assert not os.environ.get(OTEL_METRICS_EXPORTER)
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_exporter(self, mocker):
        mocker.patch.dict(
            os.environ, 
                {
                    "OTEL_TRACES_EXPORTER": "foobar",
                    "OTEL_METRICS_EXPORTER": "baz"
                }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"
        assert os.environ[OTEL_METRICS_EXPORTER] == "baz"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_no_env_non_otel_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "foo"
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"
        assert os.environ.get(OTEL_METRICS_EXPORTER) is None
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_no_env_http(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf"
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp_proto_http"
        assert os.environ[OTEL_METRICS_EXPORTER] == "otlp_proto_http"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_no_env_grpc(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc"
            },
            clear=True
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp_proto_grpc"
        assert os.environ[OTEL_METRICS_EXPORTER] == "otlp_proto_grpc"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_exporter_http(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
                "OTEL_TRACES_EXPORTER": "foobar",
                "OTEL_METRICS_EXPORTER": "baz"
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"
        assert os.environ[OTEL_METRICS_EXPORTER] == "baz"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_exporter_grpc(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
                "OTEL_TRACES_EXPORTER": "foobar",
                "OTEL_METRICS_EXPORTER": "baz"
            }
        )
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"
        assert os.environ[OTEL_METRICS_EXPORTER] == "baz"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_configure_env_propagators(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "tracecontext,solarwinds_propagator,foobar"})
        distro.SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,solarwinds_propagator,foobar"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"
        assert os.environ.get("OTEL_SEMCONV_STABILITY_OPT_IN") == "http"

    def test_load_instrumentor_no_commenting(self, mocker):
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

    def test_load_instrumentor_enable_commenting(self, mocker):
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
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.enable_commenter",
            return_value=True
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
            is_sql_commentor_enabled=True,
        )

    def test_enable_commenter_none(self, mocker):
        mocker.patch.dict(os.environ, {})
        assert distro.SolarWindsDistro().enable_commenter() == False

    def test_enable_commenter_non_bool_value(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "foo"})
        assert distro.SolarWindsDistro().enable_commenter() == False

    def test_enable_commenter_false(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "false"})
        assert distro.SolarWindsDistro().enable_commenter() == False
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "False"})
        assert distro.SolarWindsDistro().enable_commenter() == False
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "faLsE"})
        assert distro.SolarWindsDistro().enable_commenter() == False

    def test_enable_commenter_true(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "true"})
        assert distro.SolarWindsDistro().enable_commenter() == True
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "True"})
        assert distro.SolarWindsDistro().enable_commenter() == True
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "tRuE"})
        assert distro.SolarWindsDistro().enable_commenter() == True

    def test_detect_commenter_options_not_set(self, mocker):
        mocker.patch.dict(os.environ, {})
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result == {}

    def test_detect_commenter_options_invalid_kv_ignored(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_OPTIONS": "invalid-kv,foo=bar"})
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result == {}

    def test_detect_commenter_options_valid_kvs(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_OPTIONS": "foo=true,bar=FaLSe"})
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result == {
            "foo": True,
            "bar": False,
        }

    def test_detect_commenter_options_strip_whitespace_ok(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_SQLCOMMENTER_OPTIONS": "   foo   =   tRUe   , bar = falsE "
            }
        )
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result.get("foo") == True
        assert result.get("bar") == False

    def test_detect_commenter_options_strip_mix(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_OPTIONS": "invalid-kv,   foo=TrUe   ,bar  =  faLSE,   baz=qux  "})
        result = distro.SolarWindsDistro().detect_commenter_options()
        assert result.get("foo") == True
        assert result.get("bar") == False
        assert result.get("baz") is None

    def test_get_semconv_opt_in(self):
        # TODO: Support other signal types when available
        assert distro.SolarWindsDistro().get_semconv_opt_in() == "http"
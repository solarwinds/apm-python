# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest

from solarwinds_apm import configurator

class TestConfiguratorSwapLegacySpanExporter:
    @pytest.fixture(autouse=True)
    def clear_env_vars(self):
        original_env = dict(os.environ)
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def mocks(self, mocker):
        mock_exporter_class = mocker.Mock()
        mock_exporter_entry_point = mocker.Mock()
        mock_exporter_entry_point.load.return_value = mock_exporter_class
        mock_points = iter(
            [
                mock_exporter_entry_point,
                mock_exporter_entry_point,
            ]
        )
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(
            return_value=mock_points
        )
        return {
            "mock_exporter_class": mock_exporter_class,
            "mock_entry_points": mock_entry_points,
        }

    def test_swap_legacy_span_exporter_none(self, mocker):
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        assert test_configurator._swap_legacy_span_exporter({}) == {}
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_otlp_http_only(self, mocker):
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        assert test_configurator._swap_legacy_span_exporter(
            {"otlp_proto_http": "foo"}
        ) == {"otlp_proto_http": "foo"}
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_otlp_grpc_only(self, mocker):
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        assert test_configurator._swap_legacy_span_exporter(
            {"otlp_proto_grpc": "foo"}
        ) == {"otlp_proto_grpc": "foo"}
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_otlp_http_and_legacy(self, mocker):
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        assert test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_http": "foo",
                "solarwinds_exporter": "bar",
            }
        ) == {
            "otlp_proto_http": "foo",
        }
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_otlp_grpc_and_legacy(self, mocker):
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        assert test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_grpc": "foo",
                "solarwinds_exporter": "bar",
            }
        ) == {
            "otlp_proto_grpc": "foo",
        }
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_sw_only_no_protocol(self, mocker):
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        assert test_configurator._swap_legacy_span_exporter(
            {
                "solarwinds_exporter": "foo",
            }
        ) == {
            "otlp_proto_http": mocks["mock_exporter_class"],
        }
        mocks["mock_entry_points"].assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_traces_exporter", 
                    name="otlp_proto_http",
                ),
            ]
        )

    def test_swap_legacy_span_exporter_sw_only_invalid_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "invalid-proto"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "solarwinds_exporter": "foo",
            }
        )
        assert result == {
            "otlp_proto_http": mocks["mock_exporter_class"]
        }
        mocks["mock_entry_points"].assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_traces_exporter", 
                    name="otlp_proto_http",
                ),
            ]
        )

    def test_swap_legacy_span_exporter_sw_only_http_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "solarwinds_exporter": "foo",
            }
        )
        assert result == {
            "otlp_proto_http": mocks["mock_exporter_class"]
        }
        mocks["mock_entry_points"].assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_traces_exporter", 
                    name="otlp_proto_http",
                ),
            ]
        )

    def test_swap_legacy_span_exporter_sw_only_grpc_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "solarwinds_exporter": "foo",
            }
        )
        assert result == {
            "otlp_proto_grpc": mocks["mock_exporter_class"]
        }
        mocks["mock_entry_points"].assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_traces_exporter", 
                    name="otlp_proto_grpc",
                ),
            ]
        )

    def test_swap_legacy_span_exporter_otlp_and_sw_no_protocol(self, mocker):
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_http": "foo",
                "solarwinds_exporter": "bar",
            }
        )
        assert result == {
            "otlp_proto_http": "foo"
        }
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_otlp_and_sw_invalid_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "invalid-protocol"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_http": "foo",
                "solarwinds_exporter": "bar",
            }
        )
        assert result == {
            "otlp_proto_http": "foo"
        }
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_otlp_and_sw_http_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_grpc": "foo",
                "solarwinds_exporter": "bar",
            }
        )
        assert result == {
            "otlp_proto_grpc": "foo"
        }
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_otlp_and_sw_grpc_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_http": "foo",
                "solarwinds_exporter": "bar",
            }
        )
        assert result == {
            "otlp_proto_http": "foo"
        }
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_sw_only_no_traces_protocol(self, mocker):
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        assert test_configurator._swap_legacy_span_exporter(
            {
                "solarwinds_exporter": "foo",
            }
        ) == {
            "otlp_proto_http": mocks["mock_exporter_class"],
        }
        mocks["mock_entry_points"].assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_traces_exporter", 
                    name="otlp_proto_http",
                ),
            ]
        )

    def test_swap_legacy_span_exporter_sw_only_invalid_traces_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "invalid-protocol"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        assert test_configurator._swap_legacy_span_exporter(
            {
                "solarwinds_exporter": "foo",
            }
        ) == {
            "otlp_proto_http": mocks["mock_exporter_class"],
        }
        mocks["mock_entry_points"].assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_traces_exporter", 
                    name="otlp_proto_http",
                ),
            ]
        )

    def test_swap_legacy_span_exporter_sw_only_http_traces_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "http/protobuf"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "solarwinds_exporter": "foo",
            }
        )
        assert result == {
            "otlp_proto_http": mocks["mock_exporter_class"]
        }
        mocks["mock_entry_points"].assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_traces_exporter", 
                    name="otlp_proto_http",
                ),
            ]
        )

    def test_swap_legacy_span_exporter_sw_only_grpc_traces_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "grpc"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "solarwinds_exporter": "foo",
            }
        )
        assert result == {
            "otlp_proto_grpc": mocks["mock_exporter_class"]
        }
        mocks["mock_entry_points"].assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_traces_exporter", 
                    name="otlp_proto_grpc",
                ),
            ]
        )

    def test_swap_legacy_span_exporter_otlp_and_sw_invalid_traces_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "invalid-protocol"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_http": "foo",
                "solarwinds_exporter": "bar",
            }
        )
        assert result == {
            "otlp_proto_http": "foo"
        }
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_otlp_and_sw_http_traces_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "http/protobuf"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_grpc": "foo",
                "solarwinds_exporter": "bar",
            }
        )
        assert result == {
            "otlp_proto_grpc": "foo"
        }
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_otlp_and_sw_grpc_traces_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "grpc"
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_http": "foo",
                "solarwinds_exporter": "bar",
            }
        )
        assert result == {
            "otlp_proto_http": "foo"
        }
        mocks["mock_entry_points"].assert_not_called()

    def test_swap_legacy_span_exporter_sw_only_general_and_traces_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
                "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "grpc",
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "solarwinds_exporter": "foo",
            }
        )
        assert result == {
            "otlp_proto_grpc": mocks["mock_exporter_class"]
        }
        mocks["mock_entry_points"].assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_traces_exporter", 
                    name="otlp_proto_grpc",
                ),
            ]
        )

    def test_swap_legacy_span_exporter_otlp_and_sw_grpc_general_and_traces_protocol(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
                "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "grpc",
            },
            clear=True,
        )
        mocks = self.mocks(mocker)
        test_configurator = configurator.SolarWindsConfigurator()
        result = test_configurator._swap_legacy_span_exporter(
            {
                "otlp_proto_grpc": "foo",
                "solarwinds_exporter": "bar",
            }
        )
        assert result == {
            "otlp_proto_grpc": "foo"
        }
        mocks["mock_entry_points"].assert_not_called()
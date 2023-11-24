# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm import configurator

from .fixtures.trace import get_trace_mocks

class TestConfiguratorReportInitEvent:
    def test_configurator_report_init_is_lambda(
        self,
        mocker,
        mock_extension,
        mock_apmconfig_enabled_is_lambda,
    ):
        trace_mocks = get_trace_mocks(mocker)
        mock_fw_versions = mocker.patch(
            "solarwinds_apm.configurator.SolarWindsConfigurator._add_all_instrumented_python_framework_versions"
        )

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._report_init_event(
            mock_extension.Reporter,
            mock_apmconfig_enabled_is_lambda,
        )

        # Extension methods not called
        mock_extension.Reporter.sendStatus.assert_not_called()
        mock_apmconfig_enabled_is_lambda.extension.Config.getVersionString.assert_not_called()
        mock_apmconfig_enabled_is_lambda.extension.Context.set.assert_not_called()
        assert mocker.call(True,) not in mock_apmconfig_enabled_is_lambda.extension.Metadata.makeRandom.mock_calls     

        # Otel and APM methods not called
        trace_mocks.get_tracer_provider().get_tracer().resource.attributes.items.assert_not_called()
        mock_fw_versions.assert_not_called()

    def test_configurator_report_init_bad_init_status_disabled(
        self,
        mocker,
        mock_extension,
        mock_apmconfig_disabled,
    ):
        # TODO
        pass

    def test_configurator_report_init_good_init_status_disabled(
        self,
        mocker,
        mock_extension,
        mock_apmconfig_disabled,
    ):
        # TODO
        pass

    def test_configurator_report_init_error_python_version(
        self,
        mocker,
        mock_extension,
        mock_apmconfig_enabled,
    ):
        # TODO
        pass

    def test_configurator_report_init_invalid_md_from_extension(
        self,
        mocker,
        mock_extension,
        mock_apmconfig_enabled,
    ):
        # TODO
        pass

    def test_configurator_report_init(
        self,
        mocker,
        mock_extension,
        mock_apmconfig_enabled,
    ):
        trace_mocks = get_trace_mocks(mocker)

        # TODO mv APM fixtures to conftest
        def add_fw_versions(input_dict):
            input_dict.update({"foo-fw": "bar-version"})
            return input_dict

        mock_fw_versions = mocker.patch(
            "solarwinds_apm.configurator.SolarWindsConfigurator._add_all_instrumented_python_framework_versions",
            side_effect=add_fw_versions
        )

        mock_apm_version= mocker.patch(
            "solarwinds_apm.configurator.__version__",
            new="0.0.0",
        )

        # TODO mv sys fixtures to conftest
        mock_version_info = mocker.PropertyMock()
        mock_version_info.return_value = [3, 11, 12]
        mock_version = mocker.PropertyMock()
        mock_version.return_value = "foo-runtime"
        mock_exec = mocker.PropertyMock()
        mock_exec.return_value = "/foo/path"

        mock_sys = mocker.patch(
            "solarwinds_apm.configurator.sys"
        )
        type(mock_sys).version_info = mock_version_info
        type(mock_sys).version = mock_version
        type(mock_sys).executable = mock_exec
        type(mock_sys).implementation = mocker.PropertyMock()
        type(mock_sys).implementation.name = "foo-name"

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._report_init_event(
            mock_extension.Reporter,
            mock_apmconfig_enabled,
        )

        # Extension methods called
        mock_extension.Reporter.sendStatus.assert_called_once()
        mock_apmconfig_enabled.extension.Config.getVersionString.assert_called_once()
        mock_apmconfig_enabled.extension.Context.set.assert_called_once()
        mock_apmconfig_enabled.extension.Metadata.makeRandom.assert_has_calls(
            [
                mocker.call(True,),  # makeRandom(True)
            ]
        )
        mock_apmconfig_enabled.extension.Metadata.makeRandom().createEvent().addInfo.assert_has_calls(
            [
                mocker.call("Layer", "Python"),
                mocker.call("__Init", True),
                mocker.call("process.runtime.version", "3.11.12"),
                mocker.call("process.runtime.name", "foo-name"),
                mocker.call("process.runtime.description", "foo-runtime"),
                mocker.call("process.executable.path", "/foo/path"),
                mocker.call("APM.Version", "0.0.0"),
                mocker.call("APM.Extension.Version", "1.1.1"),
                mocker.call("foo-fw", "bar-version")
            ]
        )
        
        # Otel and APM methods called
        trace_mocks.get_tracer_provider().get_tracer().resource.attributes.items.assert_called_once()
        mock_fw_versions.assert_called_once()

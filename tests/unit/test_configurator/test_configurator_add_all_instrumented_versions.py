# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from solarwinds_apm import configurator

class TestConfiguratorAddAllInstrumentedFrameworkVersions:
    def set_up_mocks(
        self,
        mocker,
        entry_point_name,
        module_name,
        module_version="foo-version",
        conflicts=None,
        conflicts_exception=False,
        importlib_exception=False,
    ):
        # (1) Mock importlib
        if importlib_exception:
            mock_importlib_import_module = mocker.Mock(
                side_effect=AttributeError("mock error")
            )
        else:
            mock_importlib_import_module = mocker.Mock()
        mock_importlib = mocker.patch(
            "solarwinds_apm.configurator.importlib"
        )
        mock_importlib.configure_mock(
            **{
                "import_module": mock_importlib_import_module
            }
        )

        # (2) Mock entry point
        mock_instrumentor_entry_point = mocker.Mock()
        mock_instrumentor_entry_point.configure_mock(
            **{
                "name": entry_point_name,
                "dist": "foo",
            }
        )
        mock_points = iter([mock_instrumentor_entry_point])
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

        # (3) Mock otel dep conflicts
        if not conflicts_exception:
            mocker.patch(
                "solarwinds_apm.configurator.get_dist_dependency_conflicts",
                return_value=conflicts,
            )
        else:
            mocker.patch(
                "solarwinds_apm.configurator.get_dist_dependency_conflicts",
                side_effect=Exception("mock conflict")
            )
        
        # (4) Mock sys module
        mock_sys_module = mocker.Mock()
        mock_sys_module.configure_mock(
            **{
                "__version__": module_version,
                "sqlite_version": module_version,
                "version": module_version,  # for tornado
            }
        )
        mock_sys = mocker.patch(
            "solarwinds_apm.configurator.sys"
        )
        mock_sys.configure_mock(
            **{
                "modules": {
                    module_name: mock_sys_module
                }
            }
        )

    def test_add_all_instr_versions_skip_disabled_instrumentors(
        self,
        mocker,
    ):
        # Save any DISABLED env var for later
        old_disabled = os.environ.get("OTEL_PYTHON_DISABLED_INSTRUMENTATIONS", None)
        if old_disabled:
            del os.environ["OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"]

        mocker.patch.dict(
            os.environ,
            {
                "OTEL_PYTHON_DISABLED_INSTRUMENTATIONS": "foo-bar-module"
            }
        )

        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="foo-bar-module",
            module_name="foo"
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Foo-bar-module.Version" not in test_versions

        # Restore old DISABLED
        if old_disabled:
            os.environ["OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"] = old_disabled

    def test_add_all_instr_versions_skip_dependency_conflict(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="foo-bar-module",
            module_name="foo",
            conflicts="not-none",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Foo-bar-module.Version" not in test_versions

    def test_add_all_instr_versions_skip_conflict_check_exception(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="foo-bar-module",
            module_name="foo",
            conflicts_exception=True,
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Foo-bar-module.Version" not in test_versions

    def test_add_all_instr_versions_skip_module_lookup_exception(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="foo-bar-module",
            module_name="foo",
            importlib_exception=True,
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Foo-bar-module.Version" not in test_versions

    def test_add_all_instr_versions_aiohttp_client(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="aiohttp_client",
            module_name="aiohttp",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Aiohttp.Version" in test_versions
        assert test_versions["Python.Aiohttp.Version"] == "foo-version"

    def test_add_all_instr_versions_grpc(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="grpc_some_module",
            module_name="grpc",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Grpc.Version" in test_versions
        assert test_versions["Python.Grpc.Version"] == "foo-version"

    def test_add_all_instr_versions_system_metrics(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="system_metrics",
            module_name="psutil",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Psutil.Version" in test_versions
        assert test_versions["Python.Psutil.Version"] == "foo-version"

    def test_add_all_instr_versions_tortoiseorm(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="tortoiseorm",
            module_name="tortoise",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Tortoise.Version" in test_versions
        assert test_versions["Python.Tortoise.Version"] == "foo-version"

    def test_add_all_instr_versions_mysql(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="mysql",
            module_name="mysql.connector",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Mysql.Version" in test_versions
        assert test_versions["Python.Mysql.Version"] == "foo-version"

    def test_add_all_instr_versions_elasticsearch(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="elasticsearch",
            module_name="elasticsearch",
            module_version=("elastic", "version", "tuple"),
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Elasticsearch.Version" in test_versions
        assert test_versions["Python.Elasticsearch.Version"] == "elastic.version.tuple"

    def test_add_all_instr_versions_pyramid(
        self,
        mocker,
    ):
        # mock get_distribution
        mock_dist = mocker.Mock()
        mock_dist.configure_mock(
            **{
                "version": "foo-version"
            }
        )
        mocker.patch(
            "solarwinds_apm.configurator.get_distribution",
            return_value=mock_dist,
        )

        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="pyramid",
            module_name="pyramid",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Pyramid.Version" in test_versions
        assert test_versions["Python.Pyramid.Version"] == "foo-version"

    def test_add_all_instr_versions_sqlite3(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="sqlite3",
            module_name="sqlite3",
            module_version="foo-version",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Sqlite3.Version" in test_versions
        assert test_versions["Python.Sqlite3.Version"] == "foo-version"

    def test_add_all_instr_versions_tornado(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="tornado",
            module_name="tornado",
            module_version="foo-version",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Tornado.Version" in test_versions
        assert test_versions["Python.Tornado.Version"] == "foo-version"

    def test_add_all_instr_versions_urllib(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="urllib",
            module_name="urllib.request",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Urllib.Version" in test_versions
        assert test_versions["Python.Urllib.Version"] == "foo-version"

    def test_add_all_instr_versions_nonspecial_case(
        self,
        mocker,
    ):
        self.set_up_mocks(
            mocker=mocker,
            entry_point_name="foo-bar-module",
            module_name="foo-bar-module",
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.Foo-bar-module.Version" in test_versions
        assert test_versions["Python.Foo-bar-module.Version"] == "foo-version"

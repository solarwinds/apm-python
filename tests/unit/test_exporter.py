from enum import Enum

import pytest

import solarwinds_apm.exporter
import solarwinds_apm.extension.oboe


# Little helper =====================================================

class FooNum(Enum):
    FOO = "foo"


# Mock Fixtures =====================================================

def get_mock_spans(mocker, valid_parent=False):
    """Helper to get mock OTel spans (len 1)."""
    mock_info_event = mocker.Mock()
    mock_info_event.configure_mock(
        **{
            "name": "info",
            "kind": FooNum.FOO,
            "timestamp": 1100,
            "attributes": {"foo": "bar"},
        }
    )
    mock_exception_event = mocker.Mock()
    mock_exception_event.configure_mock(
        **{
            "name": "exception",
            "kind": FooNum.FOO,
            "timestamp": 1200,
            "attributes": {"foo": "bar"},
        }
    )

    mock_instrumentation_scope = mocker.Mock()
    mock_instrumentation_scope.configure_mock(
        **{
            "name": "foo-bar",
            "version": "foo.bar.baz",
        }
    )
    mock_span = mocker.Mock()
    span_config = {
        "get_span_context.return_value": "my_span_context",
        "start_time": 1000,
        "end_time": 2000,
        "name": "foo",
        "kind": FooNum.FOO,
        "attributes": {"foo": "bar"},
        "events": [
            mock_info_event,
            mock_exception_event,
        ],
        "instrumentation_scope": mock_instrumentation_scope,
    }
    mock_parent = None
    if valid_parent:
        mock_parent = mocker.Mock()
        mock_parent.configure_mock(
            **{
                "is_valid": True,
            }
        )
    span_config.update({
        "parent": mock_parent,
    })
    mock_span.configure_mock(
        **span_config
    )
    return([mock_span])

@pytest.fixture(name="mock_spans_root")
def fixture_mock_spans_root(mocker):
    return get_mock_spans(mocker)

@pytest.fixture(name="mock_spans_parent_valid")
def fixture_mock_spans_parent_valid(mocker):
    return get_mock_spans(mocker, True)

@pytest.fixture(name="mock_md")
def fixture_mock_md(mocker):
    mock_md = mocker.Mock()
    mock_md.configure_mock(
        **{
            "toString.return_value": "foo"
        }
    )
    return mock_md

@pytest.fixture(name="mock_create_entry")
def fixture_mock_create_entry(mocker):
    return mocker.patch(
        "solarwinds_apm.extension.oboe.Context.createEntry"
    )

@pytest.fixture(name="mock_create_exit")
def fixture_mock_create_exit(mocker):
    return mocker.patch(
        "solarwinds_apm.extension.oboe.Context.createExit"
    )

@pytest.fixture(name="mock_create_event")
def fixture_mock_create_event(mocker):
    return mocker.patch(
        "solarwinds_apm.extension.oboe.Context.createEvent"
    )

@pytest.fixture(name="mock_event")
def fixture_mock_event(mocker):
    return mocker.patch(
        "solarwinds_apm.extension.oboe.Event"
    )

@pytest.fixture(name="mock_add_info_instr_fwork")
def fixture_mock_add_info_instr_fwork(mocker):
    return mocker.patch(
        "solarwinds_apm.exporter.SolarWindsSpanExporter._add_info_instrumented_framework",
    )

@pytest.fixture(name="mock_add_info_instr_scope")
def fixture_mock_add_info_instr_scope(mocker):
    return mocker.patch(
        "solarwinds_apm.exporter.SolarWindsSpanExporter._add_info_instrumentation_scope",
    )

@pytest.fixture(name="mock_report_exception")
def fixture_mock_report_exception(mocker):
    return mocker.patch(
        "solarwinds_apm.exporter.SolarWindsSpanExporter._report_exception_event",
    )

@pytest.fixture(name="mock_report_info")
def fixture_mock_report_info(mocker):
    return mocker.patch(
        "solarwinds_apm.exporter.SolarWindsSpanExporter._report_info_event",
    )

def configure_entry_mocks(
    mocker,
    mock_event,
    mock_create_entry,
    mock_create_exit,
):
    """Helper to configure liboboe Entry mocks"""
    mock_add_info = mocker.Mock()
    mock_event.configure_mock(
        **{
            "addInfo": mock_add_info
        }
    )
    mock_create_entry.configure_mock(return_value=mock_event)
    mock_create_exit.configure_mock(return_value=mock_event)
    return mock_event, mock_add_info, mock_create_entry, mock_create_exit

def configure_event_mocks(
    mocker,
    mock_event,
    mock_create_event,
    is_exception=False,
):
    """Helper to configure liboboe Event mocks"""
    mock_add_info = mocker.Mock()
    event_config = {
            "addInfo": mock_add_info
        }
    if is_exception:
        event_config.update({
            "attributes": {
                "exception.type": "foo",
                "exception.message": "bar",
                "exception.stacktrace": "baz",
                "some": "other",
            }
        })
    mock_event.configure_mock(**event_config)
    mock_create_event.configure_mock(return_value=mock_event)
    return mock_event, mock_add_info, mock_create_event


# Other Fixtures ====================================================

@pytest.fixture(name="exporter")
def fixture_exporter(mocker):
    mock_reporter = mocker.Mock()
    mock_apm_txname_manager = mocker.patch(
        "solarwinds_apm.apm_txname_manager.SolarWindsTxnNameManager",
        return_value=mocker.Mock()
    )
    mock_apm_txname_manager.configure_mock(
        **{
            "__delitem__": mocker.Mock()
        }
    )
    mock_apm_fkwv_manager = mocker.patch(
        "solarwinds_apm.apm_fwkv_manager.SolarWindsFrameworkKvManager",
        return_value=mocker.Mock()
    )
    # mocks empty cache for framework KVs
    mock_get = mocker.Mock()
    mock_get.configure_mock(return_value=None)
    mock_apm_fkwv_manager.configure_mock(
        **{
            "get": mock_get
        }
    )

    mock_reporter.configure_mock(
        **{
            "sendReport": mocker.Mock()
        }
    )
    mock_from_string = mocker.MagicMock()
    mock_metadata = mocker.patch(
        "solarwinds_apm.extension.oboe.Metadata",
    )
    mock_metadata.configure_mock(
        **{
            "fromString": mock_from_string,
        }
    )
    return solarwinds_apm.exporter.SolarWindsSpanExporter(
        mock_reporter,
        mock_apm_txname_manager,
        mock_apm_fkwv_manager,
        True
    )


# Tests =============================================================

class Test_SolarWindsSpanExporter():

    def assert_export_add_info_and_report(
        self,
        mocker,
        mock_spans,
        mock_event,
        mock_report_info,
        mock_report_exception,
        mock_add_info,
        mock_add_info_instr_scope,
        mock_add_info_instr_fwork,        
        exporter
    ):
        # mock_spans has one info event, one exception event
        mock_report_info.assert_called_once_with(
            mock_spans[0].events[0]
        )
        mock_report_exception.assert_called_once_with(
            mock_spans[0].events[1]
        )

        # addInfo calls for entry and exit events
        mock_add_info.assert_has_calls([
            mocker.call("Layer", "foo"),
            mocker.call(solarwinds_apm.exporter.SolarWindsSpanExporter._SW_SPAN_KIND, FooNum.FOO.name),
            mocker.call("Language", "Python"),
            mocker.call("foo", "bar"),
            mocker.call("Layer", "foo"),
        ])

        # _add_info_instrumentation_scope call
        mock_add_info_instr_scope.assert_called_once_with(
            mock_spans[0],
            mock_event,
        )
        # _add_info_instrumented_framework call
        mock_add_info_instr_fwork.assert_called_once_with(
            mock_spans[0],
            mock_event,
        )

        # sendReport for entry and exit events
        exporter.reporter.sendReport.assert_has_calls([
            mocker.call(mock_event, False),
            mocker.call(mock_event, False),
        ])

    def test_init_agent_enabled_true(self, mocker):
        mock_reporter = mocker.Mock()
        mock_apm_txname_manager = mocker.Mock()
        mock_apm_fkwv_manager = mocker.Mock()
        mock_ext_context = mocker.patch(
            "solarwinds_apm.exporter.Context",      
        )
        mock_ext_metadata = mocker.patch(
            "solarwinds_apm.exporter.Metadata",
        )
        exporter = solarwinds_apm.exporter.SolarWindsSpanExporter(
            mock_reporter,
            mock_apm_txname_manager,
            mock_apm_fkwv_manager,
            True,
        )
        assert exporter.reporter == mock_reporter
        assert exporter.context == mock_ext_context
        assert exporter.metadata == mock_ext_metadata

    def test_init_agent_enabled_false(self, mocker):
        mock_reporter = mocker.Mock()
        mock_apm_txname_manager = mocker.Mock()
        mock_apm_fkwv_manager = mocker.Mock()
        mock_noop_context = mocker.patch(
            "solarwinds_apm.exporter.NoopContext",      
        )
        mock_noop_metadata = mocker.patch(
            "solarwinds_apm.exporter.NoopMetadata",
        )
        exporter = solarwinds_apm.exporter.SolarWindsSpanExporter(
            mock_reporter,
            mock_apm_txname_manager,
            mock_apm_fkwv_manager,
            False,
        )
        assert exporter.reporter == mock_reporter
        assert exporter.context == mock_noop_context
        assert exporter.metadata == mock_noop_metadata

    def test_export_root_span(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_entry,
        mock_create_exit,
        mock_report_info,
        mock_report_exception,
        mock_add_info_instr_scope,
        mock_add_info_instr_fwork,
        mock_md,
        mock_spans_root
    ):
        mock_event, mock_add_info, mock_create_entry, \
            mock_create_exit = configure_entry_mocks(
                    mocker,
                    mock_event,
                    mock_create_entry,
                    mock_create_exit,
                )
        mock_build_md = mocker.patch(
            "solarwinds_apm.exporter.SolarWindsSpanExporter._build_metadata",
            return_value=mock_md
        )

        exporter.export(mock_spans_root)

        mock_build_md.assert_has_calls([
            mocker.call(exporter.metadata, "my_span_context")
        ])
        mock_create_entry.assert_called_once_with(
            mock_md,
            1,
        )
        mock_create_exit.assert_called_once_with(2)

        self.assert_export_add_info_and_report(
            mocker,
            mock_spans_root,
            mock_event,
            mock_report_info,
            mock_report_exception,
            mock_add_info,
            mock_add_info_instr_scope,
            mock_add_info_instr_fwork,
            exporter
        )

    def test_export_parent_valid(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_entry,
        mock_create_exit,
        mock_report_info,
        mock_report_exception,
        mock_add_info_instr_scope,
        mock_add_info_instr_fwork,
        mock_md,
        mock_spans_parent_valid
    ):
        mock_event, mock_add_info, mock_create_entry, \
            mock_create_exit = configure_entry_mocks(
                    mocker,
                    mock_event,
                    mock_create_entry,
                    mock_create_exit,
                )
        mock_build_md = mocker.patch(
            "solarwinds_apm.exporter.SolarWindsSpanExporter._build_metadata",
            return_value=mock_md
        )

        exporter.export(mock_spans_parent_valid)

        mock_span_parent = mock_spans_parent_valid[0].parent
        mock_build_md.assert_has_calls([
            mocker.call(exporter.metadata, "my_span_context"),
            mocker.call(exporter.metadata, mock_span_parent)
        ])
        mock_create_entry.assert_called_once_with(
            mock_md,
            1,
            mock_md,
        )
        mock_create_exit.assert_called_once_with(2)

        self.assert_export_add_info_and_report(
            mocker,
            mock_spans_parent_valid,
            mock_event,
            mock_report_info,
            mock_report_exception,
            mock_add_info,
            mock_add_info_instr_scope,
            mock_add_info_instr_fwork,
            exporter
        )

    def test__add_info_instrumentation_scope_none(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock liboboe event
        mock_event, mock_add_info, _ \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )
        # mock span without InstrumentationScope
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": None,
            }
        )

        exporter._add_info_instrumentation_scope(
            test_span,
            mock_event,
        )
        mock_add_info.assert_has_calls([
            mocker.call("otel.scope.name", ""),
            mocker.call("otel.scope.version", ""),
        ])

    def test__add_info_instrumentation_scope_name_only(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        pass
        # mock liboboe event
        mock_event, mock_add_info, _ \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )
        # mock span with InstrumentationScope
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": "foo",
                "version": None,
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )

        exporter._add_info_instrumentation_scope(
            test_span,
            mock_event,
        )
        mock_add_info.assert_has_calls([
            mocker.call("otel.scope.name", "foo"),
            mocker.call("otel.scope.version", ""),
        ])

    def test__add_info_instrumentation_scope_name_and_version(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock liboboe event
        mock_event, mock_add_info, _ \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )
        # mock span with InstrumentationScope
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": "foo",
                "version": "bar",
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )

        exporter._add_info_instrumentation_scope(
            test_span,
            mock_event,
        )
        mock_add_info.assert_has_calls([
            mocker.call("otel.scope.name", "foo"),
            mocker.call("otel.scope.version", "bar"),
        ])

    def test__add_info_instrumented_framework_no_scope_name(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # patch importlib so foo "importable"
        mock_importlib = mocker.Mock()
        mock_importlib.configure_mock(
            **{
                "import_module": mocker.Mock()
            }
        )
        mocker.patch(
            "solarwinds_apm.exporter.importlib",
            return_value=mock_importlib
        )
        # mock foo and sys.modules
        mock_foo = mocker.Mock()
        mock_foo.configure_mock(
            **{
                "__version__": "1.2.3"
            }
        )
        mock_sys = mocker.patch(
            "solarwinds_apm.exporter.sys",
        )
        mock_sys.configure_mock(
            **{
                "modules": {
                    "foo": mock_foo
                }
            }
        )
        # mock liboboe event
        mock_event, mock_add_info, mock_create_event \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )

        # mock span without InstrumentationScope.name
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": None,
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )

        exporter._add_info_instrumented_framework(
            test_span,
            mock_event,
        )
        assert not mock_create_event.called
        assert not mock_add_info.called

    def test__add_info_instrumented_framework_name_not_otel(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # patch importlib so foo "importable"
        mock_importlib = mocker.Mock()
        mock_importlib.configure_mock(
            **{
                "import_module": mocker.Mock()
            }
        )
        mocker.patch(
            "solarwinds_apm.exporter.importlib",
            return_value=mock_importlib
        )
        # mock foo and sys.modules
        mock_foo = mocker.Mock()
        mock_foo.configure_mock(
            **{
                "__version__": "1.2.3"
            }
        )
        mock_sys = mocker.patch(
            "solarwinds_apm.exporter.sys",
        )
        mock_sys.configure_mock(
            **{
                "modules": {
                    "foo": mock_foo
                }
            }
        )
        # mock liboboe event
        mock_event, mock_add_info, mock_create_event \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )

        # mock span with InstrumentationScope but not otel
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": "foo",
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )

        exporter._add_info_instrumented_framework(
            test_span,
            mock_event,
        )
        assert not mock_create_event.called
        assert not mock_add_info.called

    def test__add_info_instrumented_framework_cached_version(
        self,
        mocker,
        mock_event,
        mock_create_event,
    ):
        mock_reporter = mocker.Mock()
        mock_apm_txname_manager = mocker.patch(
            "solarwinds_apm.apm_txname_manager.SolarWindsTxnNameManager",
            return_value=mocker.Mock()
        )
        mock_apm_fkwv_manager = mocker.patch(
            "solarwinds_apm.apm_fwkv_manager.SolarWindsFrameworkKvManager",
            return_value=mocker.Mock()
        )
        # mocks cache with existing framework KV
        mock_get = mocker.Mock()
        mock_get.configure_mock(return_value="foo.bar")
        mock_apm_fkwv_manager.configure_mock(
            **{
                "get": mock_get
            }
        )

        exporter = solarwinds_apm.exporter.SolarWindsSpanExporter(
            mock_reporter,
            mock_apm_txname_manager,
            mock_apm_fkwv_manager,
            True
        )

        # mock liboboe event
        mock_event, mock_add_info, mock_create_event \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )

        # mock span with InstrumentationScope of foo
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": "opentelemetry.instrumentation.foo",
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )

        exporter._add_info_instrumented_framework(
            test_span,
            mock_event,
        )
        mock_add_info.assert_called_once_with(
            "Python.foo.Version",
            "foo.bar",
        )

    def test__add_info_instrumented_framework_attributeerror(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # patch importlib so foo "importable"
        mock_importlib = mocker.Mock()
        mock_importlib.configure_mock(
            **{
                "import_module": mocker.Mock()
            }
        )
        mocker.patch(
            "solarwinds_apm.exporter.importlib",
            return_value=mock_importlib
        )
        # mock foo and sys.modules, but foo has no __version__
        mock_foo = mocker.Mock()
        mock_foo.configure_mock(
            **{
                "foo": "bar"
            }
        )
        mock_sys = mocker.patch(
            "solarwinds_apm.exporter.sys",
        )
        mock_sys.configure_mock(
            **{
                "modules": {
                    "foo": mock_foo
                }
            }
        )
        # mock liboboe event
        mock_event, mock_add_info, mock_create_event \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )

        # mock span with InstrumentationScope of foo
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": "opentelemetry.instrumentation.foo",
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )

        exporter._add_info_instrumented_framework(
            test_span,
            mock_event,
        )
        assert not mock_create_event.called
        assert not mock_add_info.called

    def test__add_info_instrumented_framework_importerror(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # do not patch importlib, so cannot "import" foo

        # mock liboboe event
        mock_event, mock_add_info, mock_create_event \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )

        # mock span with InstrumentationScope of foo
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": "opentelemetry.instrumentation.foo",
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )

        exporter._add_info_instrumented_framework(
            test_span,
            mock_event,
        )
        assert not mock_create_event.called
        assert not mock_add_info.called

    def test__add_info_instrumented_framework_ok(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # patch importlib so foo "importable"
        mock_importlib = mocker.Mock()
        mock_importlib.configure_mock(
            **{
                "import_module": mocker.Mock()
            }
        )
        mocker.patch(
            "solarwinds_apm.exporter.importlib",
            return_value=mock_importlib
        )
        # mock foo and sys.modules
        mock_foo = mocker.Mock()
        mock_foo.configure_mock(
            **{
                "__version__": "1.2.3"
            }
        )
        mock_sys = mocker.patch(
            "solarwinds_apm.exporter.sys",
        )
        mock_sys.configure_mock(
            **{
                "modules": {
                    "foo": mock_foo
                }
            }
        )
        # mock liboboe event
        mock_event, mock_add_info, mock_create_event \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )

        # mock span with InstrumentationScope of foo
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": "opentelemetry.instrumentation.foo",
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )

        exporter._add_info_instrumented_framework(
            test_span,
            mock_event,
        )
        assert not mock_create_event.called
        mock_add_info.assert_called_once_with(
            "Python.foo.Version",
            "1.2.3",
        )

    def mock_and_assert_addinfo_for_instrumented_framework(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
        mock_sys_modules,
        instrumentation_scope_name,
        expected_k,
        expected_v,
    ):
        """Shared logic for testing individual cases of _add_info_instrumented_framework"""
        # patch importlib so mock sys modules "importable"
        mock_importlib = mocker.Mock()
        mock_importlib.configure_mock(
            **{
                "import_module": mocker.Mock()
            }
        )
        mocker.patch(
            "solarwinds_apm.exporter.importlib",
            return_value=mock_importlib
        )
        # mock sys modules as provided
        mock_sys = mocker.patch(
            "solarwinds_apm.exporter.sys",
        )
        mock_sys.configure_mock(
            **{
                "modules": mock_sys_modules
            }
        )
        # mock liboboe event
        mock_event, mock_add_info, _ \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )
        # mock span with instrumentation_scope_name as provided
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": instrumentation_scope_name,
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )

        # Test _add_info_instrumented_framework
        exporter._add_info_instrumented_framework(
            test_span,
            mock_event,
        )
        mock_add_info.assert_called_once_with(
            expected_k,
            expected_v,
        )

    def test__add_info_instrumented_framework_aiohttp(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock module and sys.modules
        mock_module = mocker.Mock()
        mock_module.configure_mock(
            **{
                "__version__": "4.5.6"
            }
        )
        mock_sys_modules = {
            "aiohttp": mock_module
        }

        self.mock_and_assert_addinfo_for_instrumented_framework(
            mocker,
            exporter,
            mock_event,
            mock_create_event,
            mock_sys_modules,
            "opentelemetry.instrumentation.aiohttp-client",
            "Python.aiohttp.Version",
            "4.5.6",
        )

    def test__add_info_instrumented_framework_grpc(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock module and sys.modules
        mock_module = mocker.Mock()
        mock_module.configure_mock(
            **{
                "__version__": "4.5.6"
            }
        )
        mock_sys_modules = {
            "grpc_aio_client": mock_module
        }

        self.mock_and_assert_addinfo_for_instrumented_framework(
            mocker,
            exporter,
            mock_event,
            mock_create_event,
            mock_sys_modules,
            "opentelemetry.instrumentation.grpc_aio_client",
            "Python.grpc.Version",
            "4.5.6",
        )

    def test__add_info_instrumented_framework_psutil(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock module and sys.modules
        mock_module = mocker.Mock()
        mock_module.configure_mock(
            **{
                "__version__": "4.5.6"
            }
        )
        mock_sys_modules = {
            "psutil": mock_module
        }

        self.mock_and_assert_addinfo_for_instrumented_framework(
            mocker,
            exporter,
            mock_event,
            mock_create_event,
            mock_sys_modules,
            "opentelemetry.instrumentation.system_metrics",
            "Python.psutil.Version",
            "4.5.6",
        )

    def test__add_info_instrumented_framework_tortoise(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock module and sys.modules
        mock_module = mocker.Mock()
        mock_module.configure_mock(
            **{
                "__version__": "4.5.6"
            }
        )
        mock_sys_modules = {
            "tortoise": mock_module
        }

        self.mock_and_assert_addinfo_for_instrumented_framework(
            mocker,
            exporter,
            mock_event,
            mock_create_event,
            mock_sys_modules,
            "opentelemetry.instrumentation.tortoiseorm",
            "Python.tortoise.Version",
            "4.5.6",
        )

    def test__add_info_instrumented_framework_mysql(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock module and sys.modules
        mock_module = mocker.Mock()
        mock_module.configure_mock(
            **{
                "__version__": "4.5.6"
            }
        )
        mock_sys_modules = {
            "mysql.connector": mock_module
        }

        self.mock_and_assert_addinfo_for_instrumented_framework(
            mocker,
            exporter,
            mock_event,
            mock_create_event,
            mock_sys_modules,
            "opentelemetry.instrumentation.mysql",
            "Python.mysql.Version",
            "4.5.6",
        )

    def test__add_info_instrumented_framework_elasticsearch(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock module and sys.modules
        mock_module = mocker.Mock()
        mock_module.configure_mock(
            **{
                "__version__": (4, 5, 6)
            }
        )
        mock_sys_modules = {
            "elasticsearch": mock_module
        }

        self.mock_and_assert_addinfo_for_instrumented_framework(
            mocker,
            exporter,
            mock_event,
            mock_create_event,
            mock_sys_modules,
            "opentelemetry.instrumentation.elasticsearch",
            "Python.elasticsearch.Version",
            "4.5.6",
        )

    def test__add_info_instrumented_framework_tornado(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock module and sys.modules
        mock_module = mocker.Mock()
        mock_module.configure_mock(
            **{
                "version": "4.5.6"
            }
        )
        mock_sys_modules = {
            "tornado": mock_module
        }

        self.mock_and_assert_addinfo_for_instrumented_framework(
            mocker,
            exporter,
            mock_event,
            mock_create_event,
            mock_sys_modules,
            "opentelemetry.instrumentation.tornado",
            "Python.tornado.Version",
            "4.5.6",
        )

    def test__add_info_instrumented_framework_urllib(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock urllib.request and sys.modules
        mock_request = mocker.Mock()
        mock_request.configure_mock(
            **{
                "__version__": "4.5.6"
            }
        )
        mock_sys_modules = {
            "urllib.request": mock_request
        }

        self.mock_and_assert_addinfo_for_instrumented_framework(
            mocker,
            exporter,
            mock_event,
            mock_create_event,
            mock_sys_modules,
            "opentelemetry.instrumentation.urllib",
            "Python.urllib.Version",
            "4.5.6",
        )

    def test__add_info_instrumented_framework_sqlite3(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # mock sqlite3 and sys.modules
        mock_sqlite3 = mocker.Mock()
        mock_sqlite3.configure_mock(
            **{
                "sqlite_version": "4.5.6"
            }
        )
        mock_sys_modules = {
            "sqlite3": mock_sqlite3
        }

        self.mock_and_assert_addinfo_for_instrumented_framework(
            mocker,
            exporter,
            mock_event,
            mock_create_event,
            mock_sys_modules,
            "opentelemetry.instrumentation.sqlite3",
            "Python.sqlite3.Version",
            "4.5.6",
        )

    def test__add_info_instrumented_framework_pyramid(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        # patch importlib so mock sys modules "importable"
        mock_importlib = mocker.Mock()
        mock_importlib.configure_mock(
            **{
                "import_module": mocker.Mock()
            }
        )
        mocker.patch(
            "solarwinds_apm.exporter.importlib",
            return_value=mock_importlib
        )
        # mock sys modules
        mock_sys_modules = {
            "pyramid": mocker.Mock()
        }
        mock_sys = mocker.patch(
            "solarwinds_apm.exporter.sys",
        )
        mock_sys.configure_mock(
            **{
                "modules": mock_sys_modules
            }
        )
        # mock get_distribution for pyramid for actual version check
        mock_dist = mocker.Mock()
        mock_dist.configure_mock(
            **{
                "version": "4.5.6"
            }
        )
        mocker.patch(
            "solarwinds_apm.exporter.get_distribution",
            return_value=mock_dist
        )

        # mock liboboe event
        mock_event, mock_add_info, _ \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )
        # mock span with instrumentation_scope_name as provided
        mock_instrumentation_scope = mocker.Mock()
        mock_instrumentation_scope.configure_mock(
            **{
                "name": "opentelemetry.instrumentation.pyramid",
            }
        )
        test_span = mocker.Mock()
        test_span.configure_mock(
            **{
                "instrumentation_scope": mock_instrumentation_scope,
            }
        )
        # Test _add_info_instrumented_framework
        exporter._add_info_instrumented_framework(
            test_span,
            mock_event,
        )
        mock_add_info.assert_called_once_with(
            "Python.pyramid.Version",
            "4.5.6",
        )

    def test__report_exception_event(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        mock_event, mock_add_info, mock_create_event \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
                True,
             )

        exporter._report_exception_event(mock_event)

        mock_create_event.assert_called_once_with(1)
        mock_add_info.assert_has_calls([
            mocker.call("Label", "error"),
            mocker.call("Spec", "error"),
            mocker.call("ErrorClass", "foo"),
            mocker.call("ErrorMsg", "bar"),
            mocker.call("Backtrace", "baz"),
            mocker.call("some", "other")
        ])
        exporter.reporter.sendReport.assert_has_calls([
            mocker.call(mock_event, False),
        ])

    def test__report_info_event(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_event,
    ):
        mock_event, mock_add_info, mock_create_event \
             = configure_event_mocks(
                mocker,
                mock_event,
                mock_create_event,
             )

        exporter._report_info_event(mock_event)

        mock_create_event.assert_called_once_with(1)
        mock_add_info.assert_has_calls([
            mocker.call("Label", "info"),
        ])
        exporter.reporter.sendReport.assert_has_calls([
            mocker.call(mock_event, False),
        ])

    def test__build_metadata(self, mocker, exporter):
        mocker.patch(
            "solarwinds_apm.extension.oboe.Metadata.fromString"
        )
        mocker.patch(
            "solarwinds_apm.exporter.W3CTransformer.traceparent_from_context",
            return_value="foo"
        )
        mock_span_context = mocker.MagicMock()
        mock_from_string = mocker.MagicMock()
        mock_metadata = mocker.Mock()
        mock_metadata.configure_mock(
            **{
                "fromString": mock_from_string,
            }
        )
        exporter._build_metadata(mock_metadata, mock_span_context)
        solarwinds_apm.exporter.W3CTransformer \
            .traceparent_from_context.assert_called_once_with(
                mock_span_context
            )
        mock_metadata.fromString.assert_called_once_with("foo")
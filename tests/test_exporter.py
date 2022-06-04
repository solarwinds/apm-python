import pytest

import solarwinds_apm.exporter
import solarwinds_apm.extension.oboe


# Mock Fixtures =====================================================

def get_mock_spans(mocker, valid_parent=False):
    """Helper to get mock OTel spans (len 1)."""
    mock_info_event = mocker.Mock()
    mock_info_event.configure_mock(
        **{
            "name": "info",
            "timestamp": 1100,
            "attributes": {"foo": "bar"},
        }
    )
    mock_exception_event = mocker.Mock()
    mock_exception_event.configure_mock(
        **{
            "name": "exception",
            "timestamp": 1200,
            "attributes": {"foo": "bar"},
        }
    )

    mock_span = mocker.Mock()
    span_config = {
        "get_span_context.return_value": "my_span_context",
        "start_time": 1000,
        "end_time": 2000,
        "name": "foo",
        "attributes": {"foo": "bar"},
        "events": [
            mock_info_event,
            mock_exception_event,
        ],
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
    mock_reporter.configure_mock(
        **{
            "sendReport": mocker.Mock()
        }
    )
    return solarwinds_apm.exporter.SolarWindsSpanExporter(mock_reporter)


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
            mocker.call("Language", "Python"),
            mocker.call("foo", "bar"),
            mocker.call("Layer", "foo"),
        ])

        # sendReport for entry and exit events
        exporter.reporter.sendReport.assert_has_calls([
            mocker.call(mock_event, False),
            mocker.call(mock_event, False),
        ])


    def test_export_root_span(
        self,
        mocker,
        exporter,
        mock_event,
        mock_create_entry,
        mock_create_exit,
        mock_report_info,
        mock_report_exception,
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
            mocker.call("my_span_context")
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
            mocker.call("my_span_context"),
            mocker.call(mock_span_parent)
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
            exporter
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
        exporter._build_metadata(mock_span_context)
        solarwinds_apm.exporter.W3CTransformer \
            .traceparent_from_context.assert_called_once_with(
                mock_span_context
            )
        solarwinds_apm.extension.oboe \
            .Metadata.fromString.assert_called_once_with("foo")
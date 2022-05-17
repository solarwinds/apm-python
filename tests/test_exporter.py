import pytest

import solarwinds_apm.exporter
import solarwinds_apm.extension.oboe


# Fixtures ==========================================================

def get_mock_spans(mocker, span_context_val=None, valid_parent=False):
    """Helper to get mock spans (len 1)."""
    mock_info_event = mocker.Mock()
    mock_info_event.configure_mock(
        **{
            "name": "info",
            "timestamp": 2000,
            "attributes": {"foo": "bar"},
        }
    )
    mock_exception_event = mocker.Mock()
    mock_exception_event.configure_mock(
        **{
            "name": "exception",
            "timestamp": 2000,
            "attributes": {"foo": "bar"},
        }
    )

    mock_span = mocker.Mock()
    span_config = {
        "get_span_context.return_value": span_context_val,
        
        "start_time": 1000,
        "end_time": 3000,
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
    return get_mock_spans(mocker, "valid_span_context", True)

@pytest.fixture(name="exporter")
def fixture_exporter(mocker):
    mock_reporter = mocker.Mock()
    mock_reporter.configure_mock(
        **{
            "sendReport": mocker.Mock()
        }
    )
    return solarwinds_apm.exporter.SolarWindsSpanExporter(mock_reporter)

@pytest.fixture(name="mock_md")
def fixture_mock_md(mocker):
    mock_md = mocker.Mock()
    mock_md.configure_mock(
        **{
            "toString.return_value": "foo"
        }
    )
    return mock_md


# Tests =============================================================

class Test_SolarWindsSpanExporter():

    def test_export_root_span(self, mocker, exporter):
        # assert _build_metadata called
        # assert Context.createEntry called with div1000 timestamp
        # assert Context.addInfo called n times
        # assert self.exporter.reporter called twice
        pass


    def test_export_parent_valid(self,
        mocker,
        exporter,
        mock_md,
        mock_spans_parent_valid
    ):
        mock_create_entry = mocker.patch(
            "solarwinds_apm.extension.oboe.Context.createEntry"
        )
        mock_event = mocker.patch(
            "solarwinds_apm.extension.oboe.Event"
        )
        mock_add_info = mocker.Mock()
        mock_event.configure_mock(
            **{
                "addInfo": mock_add_info
            }
        )
        mock_create_entry.configure_mock(return_value=mock_event)

        mock_build_md = mocker.patch(
            "solarwinds_apm.exporter.SolarWindsSpanExporter._build_metadata",
            return_value=mock_md
        )
        mock_report_exception = mocker.patch(
            "solarwinds_apm.exporter.SolarWindsSpanExporter._report_exception_event",
        )
        mock_report_info = mocker.patch(
            "solarwinds_apm.exporter.SolarWindsSpanExporter._report_info_event",
        )

        exporter.export(mock_spans_parent_valid)

        mock_span_parent = mock_spans_parent_valid[0].parent
        mock_build_md.assert_has_calls([
            mocker.call("valid_span_context"),
            mocker.call(mock_span_parent)
        ])
        mock_create_entry.assert_called_once_with(
            mock_md,
            1,
            mock_md,
        )

    def test__report_exception_event(self, mocker, exporter):
        mocker.patch(
            "solarwinds_apm.extension.oboe.Context.createEvent"
        )
        mock_event = mocker.Mock()
        mock_event.configure_mock(
            **{
                "timestamp": 5000,
                "attributes": {"foo": "bar"}
            }
        )
        exporter._report_exception_event(mock_event)
        solarwinds_apm.extension.oboe \
            .Context.createEvent.assert_called_once_with(5)
        exporter.reporter.sendReport.assert_called_once()

    def test__report_info_event(self, mocker, exporter):
        mocker.patch(
            "solarwinds_apm.extension.oboe.Context.createEvent"
        )
        mock_event = mocker.Mock()
        mock_event.configure_mock(
            **{
                "timestamp": 5000,
                "attributes": {"foo": "bar"}
            }
        )
        exporter._report_info_event(mock_event)
        solarwinds_apm.extension.oboe \
            .Context.createEvent.assert_called_once_with(5)
        exporter.reporter.sendReport.assert_called_once()


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
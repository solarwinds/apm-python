import pytest

import solarwinds_apm.exporter
import solarwinds_apm.extension.oboe


@pytest.fixture(name="exporter")
def fixture_exporter(mocker):
    mock_reporter = mocker.Mock()
    mock_reporter.configure_mock(
        **{
            "sendReport": mocker.Mock()
        }
    )
    return solarwinds_apm.exporter.SolarWindsSpanExporter(mock_reporter)


class Test_SolarWindsSpanExporter():   
    def test_export_root_span(self, mocker, exporter):
        # assert Context.createEntry called with div1000 timestamp
        # assert Context.addInfo called n times
        # assert self.exporter.reporter called twice
        pass

    def test_export_parent_valid(self, mocker, exporter):
        # assert _build_metadata called
        # assert Context.createEntry called with div1000 timestamp
        # assert Context.addInfo called n times
        # assert self.exporter.reporter called twice
        pass

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
        solarwinds_apm.extension.oboe.Context.createEvent.assert_called_once_with(5)
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
        solarwinds_apm.extension.oboe.Context.createEvent.assert_called_once_with(5)
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
        solarwinds_apm.exporter.W3CTransformer.traceparent_from_context.assert_called_once_with(mock_span_context)
        solarwinds_apm.extension.oboe.Metadata.fromString.assert_called_once_with("foo")
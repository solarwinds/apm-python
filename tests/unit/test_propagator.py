# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from unittest.mock import call

from opentelemetry.context.context import Context
from opentelemetry.propagators import textmap
from opentelemetry.trace.span import TraceState

from solarwinds_apm.apm_constants import INTL_SWO_X_OPTIONS_KEY
from solarwinds_apm.propagator import SolarWindsPropagator


class TestSolarWindsPropagator():

    def test_extract_new_context_no_xtraceoptions(self):
        mock_carrier = dict()
        result = SolarWindsPropagator().extract(mock_carrier)
        assert isinstance(result, Context)

    def test_extract_new_context_xtraceoptions_and_signature(self):
        mock_carrier = {
            "x-trace-options": "foo",
            "x-trace-options-signature": "bar"
        }
        result = SolarWindsPropagator().extract(mock_carrier)
        actual_xto = result.get(INTL_SWO_X_OPTIONS_KEY)
        assert actual_xto.options_header == "foo"
        assert actual_xto.signature == "bar"

    def test_extract_new_context_no_xtraceoptions_yes_signature(self):
        mock_carrier = {
            "x-trace-options-signature": "bar"
        }
        result = SolarWindsPropagator().extract(mock_carrier)
        actual_xto = result.get(INTL_SWO_X_OPTIONS_KEY)
        assert actual_xto.options_header == ""
        assert actual_xto.signature == "bar"

    def test_extract_existing_context(self):
        mock_carrier = {
            "x-trace-options": "foo",
            "x-trace-options-signature": "bar"
        }
        mock_otel_context = {
            "foo_key": "foo_value",
            "sw_xtraceoptions": "dont_know_why_this_here_but_will_be_replaced",
        }
        result = SolarWindsPropagator().extract(mock_carrier, mock_otel_context)

        # This one is kept as-is
        assert result.get("foo_key") == "foo_value"
        # This one is replaced
        actual_xto = result.get(INTL_SWO_X_OPTIONS_KEY)
        assert actual_xto.options_header == "foo"
        assert actual_xto.signature == "bar"

    def mock_otel_context(self, mocker, valid_span_id=True, trace_flags=0x01, trace_state=None):
        """Shared mocks for OTel trace context

        Parameters:
        mocker: pytest-mock fixture
        valid_span_id: Whether to use a valid or invalid span_id
        trace_flags: Trace flags value
        trace_state: TraceState object or None
        """
        # Mock OTel trace API and current span context
        mock_get_span_context = mocker.Mock()
        if valid_span_id:
            mock_get_span_context.configure_mock(
                **{
                    "trace_id": 0x3A02F8A392478C3700000000DEADBEEF,
                    "span_id": 0x1000100010001000,
                    "trace_flags": trace_flags,
                    "trace_state": trace_state,
                    "is_valid": True,
                }
            )
        else:
            mock_get_span_context.configure_mock(
                **{
                    "trace_id": 0x0000000000000000000000000000000,
                    "span_id": 0x0000000000000000,
                    "trace_flags": 0x00,
                    "trace_state": trace_state,
                    "is_valid": False,
                }
            )
        mock_get_current_span = mocker.Mock()
        mock_get_current_span.configure_mock(
            **{
                "get_span_context.return_value": mock_get_span_context
            }
        )
        mock_trace = mocker.patch(
            "solarwinds_apm.propagator.trace"
        )
        # Create a unique INVALID_SPAN_CONTEXT sentinel that won't match valid mocks
        mock_invalid_span_context = mocker.Mock()
        mock_trace.configure_mock(
            **{
                "get_current_span.return_value": mock_get_current_span,
                "INVALID_SPAN_CONTEXT": mock_invalid_span_context,
            }
        )

    def test_inject_no_tracestate_invalid_span_id(self, mocker):
        """No tracestate set in carrier"""
        self.mock_otel_context(mocker, False)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x0000000000000000, trace_flags 0x00
        mock_set.assert_not_called()

    def test_inject_no_tracestate_new_tracestate(self, mocker):
        """New tracestate with sw added to start"""
        self.mock_otel_context(mocker, True)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x1000100010001000, trace_flags 0x01
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "traceparent",
                "00-3a02f8a392478c3700000000deadbeef-1000100010001000-01",
            ),
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-01")]).to_header(),
            ),
        ])

    def test_inject_no_tracestate_new_tracestate_random_not_sampled_flag(
        self, mocker
    ):
        """New tracestate preserves non-sampled random flag 02"""
        self.mock_otel_context(mocker, True, trace_flags=0x02)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "traceparent",
                "00-3a02f8a392478c3700000000deadbeef-1000100010001000-02",
            ),
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-02")]).to_header(),
            ),
        ])

    def test_inject_no_tracestate_new_tracestate_random_sampled_flag(
        self, mocker
    ):
        """New tracestate preserves sampled random flag 03"""
        self.mock_otel_context(mocker, True, trace_flags=0x03)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "traceparent",
                "00-3a02f8a392478c3700000000deadbeef-1000100010001000-03",
            ),
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-03")]).to_header(),
            ),
        ])

    def test_inject_existing_tracestate_no_sw(self, mocker):
        """sw added to start, foo=bar kept, xtrace_options_response removed"""
        trace_state = TraceState([("xtrace_options_response", "abc123"), ("foo", "bar")])
        self.mock_otel_context(mocker, True, trace_state=trace_state)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x1000100010001000, trace_flags 0x01
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "traceparent",
                "00-3a02f8a392478c3700000000deadbeef-1000100010001000-01",
            ),
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-01"), ("foo", "bar")]).to_header(),
            ),
        ])

    def test_inject_existing_tracestate_existing_sw(self, mocker):
        """sw updated and moved to start, foo=bar kept, xtrace_options_response removed"""
        trace_state = TraceState([("xtrace_options_response", "abc123"), ("foo", "bar"), ("sw", "some-existing-value")])
        self.mock_otel_context(mocker, True, trace_state=trace_state)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x1000100010001000, trace_flags 0x01
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "traceparent",
                "00-3a02f8a392478c3700000000deadbeef-1000100010001000-01",
            ),
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-01"), ("foo", "bar")]).to_header(),
            ),
        ])

    def test_inject_existing_tracestate_dict_no_stringvalue(self, mocker):
        """No tracestate creates new one"""
        self.mock_otel_context(mocker, True, trace_state=None)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x1000100010001000, trace_flags 0x01
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "traceparent",
                "00-3a02f8a392478c3700000000deadbeef-1000100010001000-01",
            ),
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-01")]).to_header(),
            ),
        ])

    def test_inject_existing_tracestate_dict_no_sw(self, mocker):
        """sw added to start, foo=bar kept, xtrace_options_response removed"""
        trace_state = TraceState([("xtrace_options_response", "abc123"), ("foo", "bar")])
        self.mock_otel_context(mocker, True, trace_state=trace_state)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x1000100010001000, trace_flags 0x01
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "traceparent",
                "00-3a02f8a392478c3700000000deadbeef-1000100010001000-01",
            ),
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-01"), ("foo", "bar")]).to_header(),
            ),
        ])

    def test_inject_existing_tracestate_dict_existing_sw(self, mocker):
        """sw updated and moved to start, foo=bar kept, xtrace_options_response removed"""
        trace_state = TraceState([("xtrace_options_response", "abc123"), ("foo", "bar"), ("sw", "some-existing-value")])
        self.mock_otel_context(mocker, True, trace_state=trace_state)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x1000100010001000, trace_flags 0x01
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "traceparent",
                "00-3a02f8a392478c3700000000deadbeef-1000100010001000-01",
            ),
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-01"), ("foo", "bar")]).to_header(),
            ),
        ])


class TestSolarWindsPropagatorNonDictCarriers:
    """Test SolarWindsPropagator with non-dict carriers from heterogeneous instrumentors"""

    def mock_otel_context_with_tracestate(self, mocker, trace_state=None):
        """Mock OTel trace context with optional existing tracestate"""
        mock_get_span_context = mocker.Mock()
        mock_get_span_context.configure_mock(
            **{
                "trace_id": 0x3A02F8A392478C3700000000DEADBEEF,
                "span_id": 0x1000100010001000,
                "trace_flags": 0x01,
                "trace_state": trace_state,
            }
        )
        mock_get_current_span = mocker.Mock()
        mock_get_current_span.configure_mock(
            **{
                "get_span_context.return_value": mock_get_span_context
            }
        )
        mock_trace = mocker.patch(
            "solarwinds_apm.propagator.trace"
        )
        # Create a unique INVALID_SPAN_CONTEXT sentinel that won't match valid mocks
        mock_invalid_span_context = mocker.Mock()
        mock_trace.configure_mock(
            **{
                "get_current_span.return_value": mock_get_current_span,
                "INVALID_SPAN_CONTEXT": mock_invalid_span_context,
            }
        )

    def test_inject_list_carrier_no_existing_tracestate(self, mocker):
        """Test injection into list-based carrier (like ConfluentKafka) with no existing tracestate"""
        self.mock_otel_context_with_tracestate(mocker, None)
        mock_carrier = []
        mock_context = mocker.Mock()
        # Custom setter for list-based carrier (simulates KafkaContextSetter)
        class ListSetter(textmap.Setter):
            def set(self, carrier, key, value):
                carrier.append((key, value))
        mock_setter = ListSetter()

        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )

        tracestate_entries = [item for item in mock_carrier if item[0] == "tracestate"]
        assert len(tracestate_entries) == 1
        assert tracestate_entries[0][1] == "sw=1000100010001000-01"

    def test_inject_list_carrier_with_existing_tracestate(self, mocker):
        """Test injection into list carrier with existing tracestate in span_context"""
        existing_trace_state = TraceState([("foo", "bar")])
        self.mock_otel_context_with_tracestate(mocker, existing_trace_state)
        mock_carrier = []
        mock_context = mocker.Mock()

        class ListSetter(textmap.Setter):
            def set(self, carrier, key, value):
                carrier.append((key, value))

        mock_setter = ListSetter()
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )

        tracestate_entries = [item for item in mock_carrier if item[0] == "tracestate"]
        assert len(tracestate_entries) == 1
        assert tracestate_entries[0][1] == "sw=1000100010001000-01,foo=bar"

    def test_inject_list_carrier_updates_existing_sw(self, mocker):
        """Test injection updates existing sw in span_context.trace_state"""
        existing_trace_state = TraceState([("sw", "old-value"), ("foo", "bar")])
        self.mock_otel_context_with_tracestate(mocker, existing_trace_state)
        mock_carrier = []
        mock_context = mocker.Mock()

        class ListSetter(textmap.Setter):
            def set(self, carrier, key, value):
                carrier.append((key, value))

        mock_setter = ListSetter()
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # Verify sw was updated and moved to front
        tracestate_entries = [item for item in mock_carrier if item[0] == "tracestate"]
        assert len(tracestate_entries) == 1
        assert tracestate_entries[0][1] == "sw=1000100010001000-01,foo=bar"

    def test_inject_list_carrier_no_attributeerror(self, mocker):
        """Verify that list carrier doesn't raise AttributeError"""
        self.mock_otel_context_with_tracestate(mocker, None)
        mock_carrier = []
        mock_context = mocker.Mock()

        class ListSetter(textmap.Setter):
            def set(self, carrier, key, value):
                # Simulates KafkaContextSetter behavior
                if isinstance(carrier, list):
                    carrier.append((key, value))

        mock_setter = ListSetter()
        try:
            SolarWindsPropagator().inject(
                mock_carrier,
                mock_context,
                mock_setter,
            )
            assert True
        except AttributeError as e:
            if "'list' object has no attribute 'get'" in str(e):
                raise AssertionError("Propagator incorrectly called carrier.get() on list carrier")
            raise

    def test_inject_custom_carrier_type(self, mocker):
        """Test injection with a completely custom carrier type"""
        existing_trace_state = TraceState([("existing", "value")])
        self.mock_otel_context_with_tracestate(mocker, existing_trace_state)

        class CustomCarrier:
            def __init__(self):
                self.headers = {}

        mock_carrier = CustomCarrier()
        mock_context = mocker.Mock()

        class CustomSetter(textmap.Setter):
            def set(self, carrier, key, value):
                carrier.headers[key] = value

        mock_setter = CustomSetter()
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        assert "tracestate" in mock_carrier.headers
        assert mock_carrier.headers["tracestate"] == "sw=1000100010001000-01,existing=value"

    def test_inject_tuple_carrier(self, mocker):
        """Test that immutable carriers work with appropriate setter"""
        self.mock_otel_context_with_tracestate(mocker, None)
        mock_carrier = ()
        mock_context = mocker.Mock()
        injected_values = {}

        class TupleSetter(textmap.Setter):
            def set(self, carrier, key, value):
                # Since tuples are immutable, store in external dict
                injected_values[key] = value

        mock_setter = TupleSetter()

        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        assert "tracestate" in injected_values
        assert injected_values["tracestate"] == "sw=1000100010001000-01"

    def test_inject_list_carrier_no_duplicate_tracestate(self, mocker):
        """Verify no duplicate tracestate with real span context"""
        from opentelemetry import trace as otel_trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
            InMemorySpanExporter,
        )

        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        tracer = provider.get_tracer(__name__)
        existing_trace_state = TraceState([("foo", "bar")])

        with tracer.start_as_current_span(
            "test_span",
            attributes={"test": "value"},
        ) as span:
            original_context = span.get_span_context()
            new_span_context = otel_trace.SpanContext(
                trace_id=original_context.trace_id,
                span_id=original_context.span_id,
                is_remote=original_context.is_remote,
                trace_flags=original_context.trace_flags,
                trace_state=existing_trace_state,
            )
            span._context = new_span_context
            carrier = []

            class TrackingListSetter(textmap.Setter):
                def __init__(self):
                    self.calls = []

                def set(self, carrier, key, value):
                    self.calls.append((key, value))
                    carrier.append((key, value))

            tracking_setter = TrackingListSetter()
            propagator = SolarWindsPropagator()
            propagator.inject(carrier, setter=tracking_setter)
            tracestate_writes = [
                call for call in tracking_setter.calls if call[0] == "tracestate"
            ]
            assert (
                len(tracestate_writes) == 1
            ), f"Expected 1 tracestate write, got {len(tracestate_writes)}: {tracestate_writes}"
            tracestate_entries = [item for item in carrier if item[0] == "tracestate"]
            assert (
                len(tracestate_entries) == 1
            ), f"Expected 1 tracestate in carrier, got {len(tracestate_entries)}: {tracestate_entries}"
            tracestate_value = tracestate_entries[0][1]
            assert "sw=" in tracestate_value
            assert "foo=bar" in tracestate_value

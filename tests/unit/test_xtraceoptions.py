import pytest  # pylint: disable=unused-import

from solarwinds_apm.traceoptions import XTraceOptions
from solarwinds_apm.apm_constants import (
    INTL_SWO_X_OPTIONS_KEY,   # "sw_xtraceoptions"
    INTL_SWO_SIGNATURE_KEY,   # "sw_signature"
)


class TestXTraceOptions():
    def test_init_empty_otel_context_defaults(self):
        xto = XTraceOptions()
        assert xto.ignored == []
        assert xto.options_header == ""
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_no_options_header_defaults(self, mocker):
        mock_otel_context = {
            "traceparent": "foo",
            "tracestate": "bar",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == ""
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_skip_option_no_key_no_value(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "=",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "="
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_skip_option_no_key(self):
        """Equals sign with no left hand side"""
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "=oops",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "=oops"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_tt_key_valid(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "trigger-trace",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 1
        assert xto.ts == 0

    def test_init_tt_key_ignored(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "trigger-trace=1",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["trigger-trace"]
        assert xto.options_header == "trigger-trace=1"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_swkeys_key_value_strip(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "sw-keys=   foo:key   ",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "sw-keys=   foo:key   "
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == "foo:key"
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_custom_key_match_stored_in_options_header_and_custom_kvs(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "custom-awesome-key=foo",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "custom-awesome-key=foo"
        assert xto.signature == None
        assert xto.custom_kvs == {"custom-awesome-key": "foo"}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_custom_key_match_stored_in_options_header_and_custom_kvs_strip(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "custom-awesome-key=   foo  ",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "custom-awesome-key=   foo  "
        assert xto.signature == None
        assert xto.custom_kvs == {"custom-awesome-key": "foo"}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_custom_key_match_but_no_value_ignored(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "custom-no-value",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["custom-no-value"]
        assert xto.options_header == "custom-no-value"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_custom_key_match_but_multiple_values_ignored(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "custom-but=too-many=values-nuoo",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["custom-but"]
        assert xto.options_header == "custom-but=too-many=values-nuoo"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_ts_valid(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "ts=12345",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "ts=12345"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 12345

    def test_init_ts_ignored(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "ts=incorrect",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["ts"]
        assert xto.options_header == "ts=incorrect"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_other_key_ignored(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "customer-key=foo",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["customer-key"]
        assert xto.options_header == "customer-key=foo"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

    def test_init_signature_stored_if_options(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "trigger-trace",
            INTL_SWO_SIGNATURE_KEY: "my-foo-signature",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace"
        assert xto.signature == "my-foo-signature"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 1
        assert xto.ts == 0

    def test_init_signature_not_stored_without_options(self):
        mock_otel_context = {
            INTL_SWO_SIGNATURE_KEY: "my-foo-signature",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == ""
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.ts == 0

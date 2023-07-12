# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest  # pylint: disable=unused-import

from solarwinds_apm.traceoptions import XTraceOptions
from solarwinds_apm.apm_constants import (
    INTL_SWO_X_OPTIONS_KEY,   # "sw_xtraceoptions"
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
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

    def test_init_swkeys_containing_semicolon_ignore_after(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "sw-keys=check-id:check-1013,website-id;booking-demo",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["booking-demo"]
        assert xto.options_header == "sw-keys=check-id:check-1013,website-id;booking-demo"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == "check-id:check-1013,website-id"
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

    def test_init_custom_key_match_equals_in_value_ok(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "custom-and=a-value=12345containing_equals=signs",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "custom-and=a-value=12345containing_equals=signs"
        assert xto.signature == None
        assert xto.custom_kvs == {"custom-and": "a-value=12345containing_equals=signs"}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0

    def test_init_custom_key_spaces_in_key_not_allowed(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "custom- key=this_is_bad;custom-key 7=this_is_bad_too",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["custom- key", "custom-key 7"]
        assert xto.options_header == "custom- key=this_is_bad;custom-key 7=this_is_bad_too"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0

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
        assert xto.timestamp == 12345

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
        assert xto.timestamp == 0

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
        assert xto.timestamp == 0

    def test_init_signature_stored_if_options(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "trigger-trace",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace"
        assert xto.signature == "my-foo-signature"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0

    def test_init_signature_still_stored_without_options(self):
        mock_otel_context = {
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == ""
        assert xto.signature == "my-foo-signature"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0

    def test_init_xtraceoptions_documented_example_1(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo"
        assert xto.signature == None
        assert xto.custom_kvs == {}
        assert xto.sw_keys == "check-id:check-1013,website-id:booking-demo"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0

    def test_init_xtraceoptions_documented_example_2(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "trigger-trace;custom-key1=value1",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace;custom-key1=value1"
        assert xto.signature == None
        assert xto.custom_kvs == {"custom-key1": "value1"}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0

    def test_init_xtraceoptions_documented_example_3(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;ts=1564432370",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;ts=1564432370"
        assert xto.signature == "5c7c733c727e5038d2cd537630206d072bbfc07c"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == "check-id:check-1013,website-id:booking-demo"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 1564432370

    def test_init_all_options_strip(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: " trigger-trace ;  custom-something=value; custom-OtherThing = other val ;  sw-keys = 029734wr70:9wqj21,0d9j1   ; ts = 12345 ; foo = bar ",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["foo"]
        assert xto.options_header == " trigger-trace ;  custom-something=value; custom-OtherThing = other val ;  sw-keys = 029734wr70:9wqj21,0d9j1   ; ts = 12345 ; foo = bar "
        assert xto.signature == None
        assert xto.custom_kvs == {
            "custom-something": "value",
            "custom-OtherThing": "other val",
        }
        assert xto.sw_keys == "029734wr70:9wqj21,0d9j1"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 12345

    def test_init_all_options_handle_sequential_semis(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: ";foo=bar;;;custom-something=value_thing;;sw-keys=02973r70:1b2a3;;;;custom-key=val;ts=12345;;;;;;;trigger-trace;;;",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["foo"]
        assert xto.options_header == ";foo=bar;;;custom-something=value_thing;;sw-keys=02973r70:1b2a3;;;;custom-key=val;ts=12345;;;;;;;trigger-trace;;;"
        assert xto.signature == None
        assert xto.custom_kvs == {
            "custom-something": "value_thing",
            "custom-key": "val",
        }
        assert xto.sw_keys == "02973r70:1b2a3"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 12345

    def test_init_keep_first_repeated_key_value(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "ts=123;custom-something=keep_this_0;sw-keys=keep_this;sw-keys=029734wrqj21,0d9;custom-something=otherval;ts=456",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "ts=123;custom-something=keep_this_0;sw-keys=keep_this;sw-keys=029734wrqj21,0d9;custom-something=otherval;ts=456"
        assert xto.signature == None
        assert xto.custom_kvs == {
            "custom-something": "keep_this_0",
        }
        assert xto.sw_keys == "keep_this"
        assert xto.trigger_trace == 0
        assert xto.timestamp == 123

    def test_init_keep_values_containing_equals_char(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "trigger-trace;custom-something=value_thing=4;custom-OtherThing=other val;sw-keys=g049sj345=0spd",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace;custom-something=value_thing=4;custom-OtherThing=other val;sw-keys=g049sj345=0spd"
        assert xto.signature == None
        assert xto.custom_kvs == {
            "custom-something": "value_thing=4",
            "custom-OtherThing": "other val",
        }
        assert xto.sw_keys == "g049sj345=0spd"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0

    def test_init_single_quotes_are_ok(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: "trigger-trace;custom-foo='bar;bar';custom-bar=foo",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["bar'"]
        assert xto.options_header == "trigger-trace;custom-foo='bar;bar';custom-bar=foo"
        assert xto.signature == None
        assert xto.custom_kvs == {
            "custom-foo": "'bar",
            "custom-bar": "foo",
        }
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0

    def test_init_multiple_missing_values_and_semis(self):
        mock_otel_context = {
            INTL_SWO_X_OPTIONS_KEY: ";trigger-trace;custom-something=value_thing;sw-keys=02973r70:9wqj21,0d9j1;1;2;3;4;5;=custom-key=val?;=",
        }
        xto = XTraceOptions(mock_otel_context)
        assert xto.ignored == ["1", "2", "3", "4", "5"]
        assert xto.options_header == ";trigger-trace;custom-something=value_thing;sw-keys=02973r70:9wqj21,0d9j1;1;2;3;4;5;=custom-key=val?;="
        assert xto.signature == None
        assert xto.custom_kvs == {
            "custom-something": "value_thing",
        }
        assert xto.sw_keys == "02973r70:9wqj21,0d9j1"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0

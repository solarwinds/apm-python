# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm.traceoptions import XTraceOptions


class TestXTraceOptions():
    def test_init_no_headers_defaults(self):
        xto = XTraceOptions()
        assert xto.ignored == []
        assert xto.options_header == ""
        assert xto.signature == ""
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert not xto.include_response

    # options_header NOT stored unless signature provided
    def test_init_xtraceoptions_only(self):
        xto = XTraceOptions("foo")
        assert xto.ignored == ["foo"]
        assert xto.options_header == ""
        assert xto.signature == ""
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    # include_response is False if no x-trace-options header
    # signature is still stored
    def test_init_signature_only(self):
        xto = XTraceOptions("", "bar")
        assert xto.ignored == []
        assert xto.options_header == ""
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert not xto.include_response

    def test_init_xtraceoption_and_signature(self):
        xto = XTraceOptions("foo", "bar")
        assert xto.ignored == ["foo"]
        assert xto.options_header == "foo"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_tt_key_valid(self):
        xto = XTraceOptions("trigger-trace", "bar")
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_tt_key_ignored(self):
        xto = XTraceOptions("trigger-trace=1", "bar")
        assert xto.ignored == ["trigger-trace"]
        assert xto.options_header == "trigger-trace=1"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_swkeys_key_value_strip(self):
        xto = XTraceOptions("sw-keys=   foo:key   ", "bar")
        assert xto.ignored == []
        assert xto.options_header == "sw-keys=   foo:key   "
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == "foo:key"
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_swkeys_containing_semicolon_ignore_after(self):
        xto = XTraceOptions(
            "sw-keys=check-id:check-1013,website-id;booking-demo" ,
            "bar",
        )
        assert xto.ignored == ["booking-demo"]
        assert xto.options_header == "sw-keys=check-id:check-1013,website-id;booking-demo"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == "check-id:check-1013,website-id"
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_custom_key_match_stored_in_options_header_and_custom_kvs(self):
        xto = XTraceOptions("custom-awesome-key=foo", "bar")
        assert xto.ignored == []
        assert xto.options_header == "custom-awesome-key=foo"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {"custom-awesome-key": "foo"}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_custom_key_match_stored_in_options_header_and_custom_kvs_strip(self):
        xto = XTraceOptions(
            "custom-awesome-key=   foo  ",
            "bar"
        )
        assert xto.ignored == []
        assert xto.options_header == "custom-awesome-key=   foo  "
        assert xto.signature == "bar"
        assert xto.custom_kvs == {"custom-awesome-key": "foo"}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_custom_key_match_but_no_value_ignored(self):
        xto = XTraceOptions("custom-no-value", "bar")
        assert xto.ignored == ["custom-no-value"]
        assert xto.options_header == "custom-no-value"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_custom_key_match_equals_in_value_ok(self):
        xto = XTraceOptions(
            "custom-and=a-value=12345containing_equals=signs",
            "bar",
        )
        assert xto.ignored == []
        assert xto.options_header == "custom-and=a-value=12345containing_equals=signs"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {"custom-and": "a-value=12345containing_equals=signs"}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_custom_key_spaces_in_key_not_allowed(self):
        xto = XTraceOptions(
            "custom- key=this_is_bad;custom-key 7=this_is_bad_too",
            "bar",
        )
        assert xto.ignored == ["custom- key", "custom-key 7"]
        assert xto.options_header == "custom- key=this_is_bad;custom-key 7=this_is_bad_too"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_ts_valid(self):
        xto = XTraceOptions("ts=12345", "bar")
        assert xto.ignored == []
        assert xto.options_header == "ts=12345"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 12345
        assert xto.include_response

    def test_init_ts_ignored(self):
        xto = XTraceOptions("ts=incorrect", "bar")
        assert xto.ignored == ["ts"]
        assert xto.options_header == "ts=incorrect"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_other_key_ignored(self):
        xto = XTraceOptions("customer-key=foo", "bar")
        assert xto.ignored == ["customer-key"]
        assert xto.options_header == "customer-key=foo"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 0
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_xtraceoptions_documented_example_1(self):
        xto = XTraceOptions(
            "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo",
            "bar",
        )
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == "check-id:check-1013,website-id:booking-demo"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_xtraceoptions_documented_example_2(self):
        xto = XTraceOptions(
            "trigger-trace;custom-key1=value1",
            "bar",
        )
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace;custom-key1=value1"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {"custom-key1": "value1"}
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_xtraceoptions_documented_example_3(self):
        xto = XTraceOptions(
            "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;ts=1564432370",
            "bar",
        )
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;ts=1564432370"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {}
        assert xto.sw_keys == "check-id:check-1013,website-id:booking-demo"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 1564432370
        assert xto.include_response

    def test_init_all_options_strip(self):
        xto = XTraceOptions(
            " trigger-trace ;  custom-something=value; custom-OtherThing = other val ;  sw-keys = 029734wr70:9wqj21,0d9j1   ; ts = 12345 ; foo = bar ",
            "bar",
        )
        assert xto.ignored == ["foo"]
        assert xto.options_header == " trigger-trace ;  custom-something=value; custom-OtherThing = other val ;  sw-keys = 029734wr70:9wqj21,0d9j1   ; ts = 12345 ; foo = bar "
        assert xto.signature == "bar"
        assert xto.custom_kvs == {
            "custom-something": "value",
            "custom-OtherThing": "other val",
        }
        assert xto.sw_keys == "029734wr70:9wqj21,0d9j1"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 12345
        assert xto.include_response

    def test_init_all_options_handle_sequential_semis(self):
        xto = XTraceOptions(
            ";foo=bar;;;custom-something=value_thing;;sw-keys=02973r70:1b2a3;;;;custom-key=val;ts=12345;;;;;;;trigger-trace;;;",
            "bar",
        )
        assert xto.ignored == ["foo"]
        assert xto.options_header == ";foo=bar;;;custom-something=value_thing;;sw-keys=02973r70:1b2a3;;;;custom-key=val;ts=12345;;;;;;;trigger-trace;;;"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {
            "custom-something": "value_thing",
            "custom-key": "val",
        }
        assert xto.sw_keys == "02973r70:1b2a3"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 12345
        assert xto.include_response

    def test_init_keep_first_repeated_key_value(self):
        xto = XTraceOptions(
            "ts=123;custom-something=keep_this_0;sw-keys=keep_this;sw-keys=029734wrqj21,0d9;custom-something=otherval;ts=456",
            "bar",
        )
        assert xto.ignored == []
        assert xto.options_header == "ts=123;custom-something=keep_this_0;sw-keys=keep_this;sw-keys=029734wrqj21,0d9;custom-something=otherval;ts=456"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {
            "custom-something": "keep_this_0",
        }
        assert xto.sw_keys == "keep_this"
        assert xto.trigger_trace == 0
        assert xto.timestamp == 123
        assert xto.include_response

    def test_init_keep_values_containing_equals_char(self):
        xto = XTraceOptions(
            "trigger-trace;custom-something=value_thing=4;custom-OtherThing=other val;sw-keys=g049sj345=0spd",
            "bar",
        )
        assert xto.ignored == []
        assert xto.options_header == "trigger-trace;custom-something=value_thing=4;custom-OtherThing=other val;sw-keys=g049sj345=0spd"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {
            "custom-something": "value_thing=4",
            "custom-OtherThing": "other val",
        }
        assert xto.sw_keys == "g049sj345=0spd"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_single_quotes_are_ok(self):
        xto = XTraceOptions(
            "trigger-trace;custom-foo='bar;bar';custom-bar=foo",
            "bar",
        )
        assert xto.ignored == ["bar'"]
        assert xto.options_header == "trigger-trace;custom-foo='bar;bar';custom-bar=foo"
        assert xto.signature == "bar"
        assert xto.custom_kvs == {
            "custom-foo": "'bar",
            "custom-bar": "foo",
        }
        assert xto.sw_keys == ""
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0
        assert xto.include_response

    def test_init_multiple_missing_values_and_semis(self):
        xto = XTraceOptions(
            ";trigger-trace;custom-something=value_thing;sw-keys=02973r70:9wqj21,0d9j1;1;2;3;4;5;=custom-key=val?;=",
            "bar",
        )
        assert xto.ignored == ["1", "2", "3", "4", "5"]
        assert xto.options_header == ";trigger-trace;custom-something=value_thing;sw-keys=02973r70:9wqj21,0d9j1;1;2;3;4;5;=custom-key=val?;="
        assert xto.signature == "bar"
        assert xto.custom_kvs == {
            "custom-something": "value_thing",
        }
        assert xto.sw_keys == "02973r70:9wqj21,0d9j1"
        assert xto.trigger_trace == 1
        assert xto.timestamp == 0
        assert xto.include_response

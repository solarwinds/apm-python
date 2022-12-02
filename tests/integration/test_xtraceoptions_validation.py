import re
import json

from opentelemetry import trace as trace_api
from unittest import mock

from .test_base_sw_headers_attrs import TestBaseSwHeadersAndAttributes


class TestXtraceoptionsValidation(TestBaseSwHeadersAndAttributes):
    """
    Test class for x-trace-options header validation as part of
    unsigned requests.
    """

    def test_remove_leading_trailing_spaces(self):
        pass

    def test_handle_sequential_semicolons(self):
        pass

    def test_keep_first_of_repeated_key(self):
        pass

    def test_keep_values_with_equals_signs(self):
        pass

    def test_ignore_tt_with_value(self):
        pass

    def test_single_quotes_ok(self):
        pass

    def test_multiple_missing_values_and_semis(self):
        pass

    def test_custom_key_spaces_not_allowed(self):
        pass

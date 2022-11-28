import re
import json

from opentelemetry import trace as trace_api
from unittest import mock

from .test_base_sw_headers_attrs import TestBaseSwHeadersAndAttributes


class TestSignedWithOrWithoutTt(TestBaseSwHeadersAndAttributes):
    def test_signed_with_tt_auth_ok(self):
        # TODO
        pass

    def test_signed_without_tt_auth_ok(self):
        # TODO
        pass

    def test_signed_auth_fail(self):
        # TODO
        pass

    def test_signed_no_xtraceoptions_header(self):
        # TODO
        pass


from solarwinds_apm import apm_logging

class TestApmLoggingLevel:

    def test_is_valid_level_ok(self):
        assert apm_logging.ApmLoggingLevel.is_valid_level("6")

    def test_is_valid_level_not_int(self):
        assert not apm_logging.ApmLoggingLevel.is_valid_level("abc")

    def test_is_valid_level_int_out_of_range(self):
        assert not apm_logging.ApmLoggingLevel.is_valid_level(9999)

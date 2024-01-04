# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm import apm_logging

class TestApmLoggingType:
    def test_default_type(self):
        assert apm_logging.ApmLoggingType.default_type() == 0
    
    def test_disabled_type(self):
        assert apm_logging.ApmLoggingType.disabled_type() == 4

    def test_file_type(self):
        assert apm_logging.ApmLoggingType.file_type() == 2

    def test_is_valid_type_ok(self):
        assert apm_logging.ApmLoggingType.is_valid_log_type(0)
        assert apm_logging.ApmLoggingType.is_valid_log_type(2)
        assert apm_logging.ApmLoggingType.is_valid_log_type(4)

    def test_is_valid_type_not_int_ret_default(self):
        assert apm_logging.ApmLoggingType.is_valid_log_type("abc") == 0

    def test_is_valid_type_int_out_of_range_ret_default(self):
        assert apm_logging.ApmLoggingType.is_valid_log_type(-9999) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(-1) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(1) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(3) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(5) == 0
        assert apm_logging.ApmLoggingType.is_valid_log_type(9999) == 0

class TestApmLoggingLevel:
    def test_default_level(self):
        assert apm_logging.ApmLoggingLevel.default_level() == 2

    def test_is_valid_level_ok(self):
        assert apm_logging.ApmLoggingLevel.is_valid_level(-1)
        assert apm_logging.ApmLoggingLevel.is_valid_level(0)
        assert apm_logging.ApmLoggingLevel.is_valid_level(1)
        assert apm_logging.ApmLoggingLevel.is_valid_level(2)
        assert apm_logging.ApmLoggingLevel.is_valid_level(3)
        assert apm_logging.ApmLoggingLevel.is_valid_level(4)
        assert apm_logging.ApmLoggingLevel.is_valid_level(5)
        assert apm_logging.ApmLoggingLevel.is_valid_level(6)

    def test_is_valid_level_not_int(self):
        assert not apm_logging.ApmLoggingLevel.is_valid_level("abc")

    def test_is_valid_level_int_out_of_range(self):
        assert not apm_logging.ApmLoggingLevel.is_valid_level(-9999)
        assert not apm_logging.ApmLoggingLevel.is_valid_level(-2)
        assert not apm_logging.ApmLoggingLevel.is_valid_level(7)
        assert not apm_logging.ApmLoggingLevel.is_valid_level(9999)

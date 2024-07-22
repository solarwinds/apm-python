# © 2024 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest

def get_logging_mocks(mocker):
    mock_logger = mocker.Mock()
    mock_logger.configure_mock(
        **{
            "addHandler": mocker.Mock()
        }
    )
    mock_get_logger = mocker.Mock(return_value=mock_logger)
    mock_logging = mocker.patch(
        "solarwinds_apm.configurator.logging"
    )
    mock_logging.configure_mock(
        **{
            "getLogger": mock_get_logger
        }
    )
    return mock_logging

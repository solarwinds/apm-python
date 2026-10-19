# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0


def get_logging_mocks(mocker):
    mock_logger = mocker.Mock()
    mock_logger.configure_mock(addHandler=mocker.Mock())
    mock_get_logger = mocker.Mock(return_value=mock_logger)
    mock_logging = mocker.patch("solarwinds_apm.configurator.logging")
    mock_logging.configure_mock(getLogger=mock_get_logger)
    return mock_logging

# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0


import os
import tempfile
import uuid
from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.semconv.resource import ResourceAttributes

from solarwinds_apm.uams import ATTR_UAMS_CLIENT_ID, UamsResourceDetector

UAMS_FILE_ID = str(uuid.uuid4())
UAMS_API_ID = str(uuid.uuid4())

UAMS_FILE = os.path.join(tempfile.gettempdir(), "uamsclientid")


@pytest.fixture
def setup_file():
    os.makedirs(os.path.dirname(UAMS_FILE), exist_ok=True)
    with open(UAMS_FILE, "w") as f:
        f.write(UAMS_FILE_ID)
    yield
    os.remove(UAMS_FILE)


@patch("requests.get")
def test_detects_id_from_file_when_file_present_and_api_running(
    mock_get, setup_file
):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "uamsclient_id": UAMS_API_ID,
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    detector = UamsResourceDetector(UAMS_FILE)
    resource = detector.detect()
    assert resource.attributes == {
        ATTR_UAMS_CLIENT_ID: UAMS_FILE_ID,
        ResourceAttributes.HOST_ID: UAMS_FILE_ID,
    }
    # Ensure the API was not called
    mock_get.assert_not_called()


def test_detects_id_from_file_when_file_present_and_api_not_running(
    setup_file,
):
    detector = UamsResourceDetector(UAMS_FILE)
    resource = detector.detect()
    assert resource.attributes == {
        ATTR_UAMS_CLIENT_ID: UAMS_FILE_ID,
        ResourceAttributes.HOST_ID: UAMS_FILE_ID,
    }


@patch("requests.get")
def test_detects_id_from_file_when_file_present_and_unrelated_running(
    mock_get, setup_file
):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "unrelated": "unrelated_value",
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    detector = UamsResourceDetector(UAMS_FILE)
    resource = detector.detect()
    assert resource.attributes == {
        ATTR_UAMS_CLIENT_ID: UAMS_FILE_ID,
        ResourceAttributes.HOST_ID: UAMS_FILE_ID,
    }
    # Ensure the API was not called
    mock_get.assert_not_called()


@patch("requests.get")
def test_detects_id_from_api_when_file_not_present_and_api_running(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "uamsclient_id": UAMS_API_ID,
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    detector = UamsResourceDetector(UAMS_FILE)
    resource = detector.detect()
    assert resource.attributes == {
        ATTR_UAMS_CLIENT_ID: UAMS_API_ID,
        ResourceAttributes.HOST_ID: UAMS_API_ID,
    }
    # Ensure the API was called
    mock_get.assert_called_once()


def test_detects_nothing_when_file_not_present_and_api_not_running():
    detector = UamsResourceDetector(UAMS_FILE)
    resource = detector.detect()
    assert resource.attributes == {}


@patch("requests.get")
def test_detects_nothing_when_file_not_present_and_unrelated_running(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "unrelated": "unrelated_value",
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    detector = UamsResourceDetector(UAMS_FILE)
    resource = detector.detect()
    assert resource.attributes == {}
    # Ensure the unrelated API was called
    mock_get.assert_called_once()

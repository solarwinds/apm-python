# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import os

import requests
from opentelemetry.context import (
    _SUPPRESS_INSTRUMENTATION_KEY,
    attach,
    detach,
    set_value,
)
from opentelemetry.sdk.resources import Resource, ResourceDetector
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)

ATTR_UAMS_CLIENT_ID = "sw.uams.client.id"

UAMS_CLIENT_PATH = (
    "C:\\ProgramData\\SolarWinds\\UAMSClient\\uamsclientid"
    if os.name == "nt"
    else "/opt/solarwinds/uamsclient/var/uamsclientid"
)

UAMS_CLIENT_URL = "http://127.0.0.1:2113/info/uamsclient"
UAMS_CLIENT_ID_FIELD = "uamsclient_id"


def _read_from_file(uams_file: str) -> dict:
    """
    Read UAMS client ID from file.

    Parameters:
    uams_file (str): Path to UAMS client ID file.

    Returns:
    dict: Dictionary with UAMS client ID and host ID attributes, or empty dict on error.
    """
    try:
        with open(uams_file, encoding="utf-8") as file:
            uams_id = file.read().strip()
            return {
                ATTR_UAMS_CLIENT_ID: uams_id,
                ResourceAttributes.HOST_ID: uams_id,
            }
    # pylint: disable=broad-except
    except Exception as error:
        logger.debug("file error", exc_info=error)
        return {}


def _read_from_api() -> dict:
    """
    Read UAMS client ID from local API endpoint.

    Returns:
    dict: Dictionary with UAMS client ID and host ID attributes, or empty dict on error.
    """
    try:
        token = attach(set_value(_SUPPRESS_INSTRUMENTATION_KEY, True))
        response = requests.get(UAMS_CLIENT_URL, timeout=1)
        detach(token)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict) or UAMS_CLIENT_ID_FIELD not in data:
            raise ValueError("Invalid response format")

        id = data[UAMS_CLIENT_ID_FIELD]
        return {
            ATTR_UAMS_CLIENT_ID: id,
            ResourceAttributes.HOST_ID: id,
        }
    # pylint: disable=broad-except
    except Exception as error:
        logger.debug("api response error", exc_info=error)
        return {}


class UamsResourceDetector(ResourceDetector):
    """Detect UAMS client attributes for SolarWinds APM resource identification."""

    def __init__(self, uams: str = UAMS_CLIENT_PATH) -> None:
        """
        Initialize UAMS Resource Detector.

        Parameters:
        uams (str): Path to UAMS client ID file. Defaults to UAMS_CLIENT_PATH.
        """
        super().__init__()
        self._uams = uams

    def detect(self) -> Resource:
        """
        Detect UAMS resource attributes.

        Returns:
        Resource: Resource with UAMS client ID and host ID attributes if available.
        """
        attributes = _read_from_file(self._uams) or _read_from_api() or {}
        return Resource(attributes)

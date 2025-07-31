# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
from __future__ import annotations

import logging
import socket
import threading
from typing import Any

import requests
from opentelemetry.context import (
    _SUPPRESS_INSTRUMENTATION_KEY,
    attach,
    detach,
    set_value,
)
from opentelemetry.sdk.metrics import MeterProvider

from solarwinds_apm.oboe.configuration import Configuration
from solarwinds_apm.oboe.sampler import Sampler

REQUEST_TIMEOUT = 10  # 10s

DAEMON_THREAD_JOIN_TIMEOUT = 10  # 10s
REQUEST_INTERVAL = 60  # 60s

logger = logging.getLogger(__name__)


class HttpSampler(Sampler):
    def __init__(
        self,
        meter_provider: MeterProvider,
        config: Configuration,
        initial: dict[str, Any] | None,
    ):
        super().__init__(
            meter_provider=meter_provider,
            config=config,
            initial=initial,
        )
        self._url = config.collector
        if not self._url.startswith("https://"):
            self._url = f"https://{self._url}"
        self._service = config.service
        self._headers = config.headers
        self._hostname = socket.gethostname()
        self._last_warning_message = None
        self._shutdown_event = threading.Event()
        self._daemon_thread = threading.Thread(
            name="HttpSampler", target=self._loop, daemon=True
        )
        self._daemon_thread.start()

    def __str__(self) -> str:
        return f"HTTP Sampler ({self._url})"

    def _warn(self, message: str, *args: Any):
        if message != self._last_warning_message:
            logger.warning("%s %s", message, str(*args))
            self._last_warning_message = message
        else:
            logger.debug("%s %s", message, str(*args))

    def shutdown(self):
        """
        Shutdown the daemon thread.
        """
        self._shutdown_event.set()
        if self._daemon_thread:
            self._daemon_thread.join(timeout=DAEMON_THREAD_JOIN_TIMEOUT)

    def _loop(self):
        """
        Main loop of the daemon thread.
        """
        # Initial fetch
        self._task()
        while not self._shutdown_event.wait(timeout=REQUEST_INTERVAL):
            self._task()

    def _task(self):
        """
        Fetch sampling settings from the collector and update the settings in the sampler.
        """
        try:
            unparsed = self._fetch_from_collector()
            parsed = self.update_settings(unparsed)
            if not parsed:
                self._warn("Retrieved sampling settings are invalid.")
            else:
                self._last_warning_message = None
        except requests.RequestException as error:
            message = "Failed to retrieve sampling settings"
            message += f" ({error})"
            message += ", tracing will be disabled after time-to-live of the previous settings expired, until valid ones are available."
            self._warn(message, error)

    def _fetch_from_collector(self):
        """
        Fetch sampling settings from the collector.
        """
        url = f"{self._url}/v1/settings/{self._service}/{self._hostname}"
        logger.debug("retrieving sampling settings from %s", url)
        token = attach(set_value(_SUPPRESS_INSTRUMENTATION_KEY, True))
        response = requests.get(
            url, headers=self._headers, timeout=REQUEST_TIMEOUT
        )
        detach(token)
        response.raise_for_status()
        logger.debug("received sampling settings response %s", response.text)
        return response.json()

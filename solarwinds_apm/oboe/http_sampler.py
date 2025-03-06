import http
import os
import json
import logging
import asyncio
import threading
import time
from asyncio import events
from datetime import datetime, timedelta
import socket
from typing import Optional, Any, Dict
from urllib.parse import quote

from requests.adapters import HTTPAdapter, Retry

import requests

from opentelemetry.context import Context
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider

from opentelemetry.trace import SpanKind, Link

from solarwinds_apm.oboe.configuration import Configuration
from solarwinds_apm.oboe.sampler import Sampler

REQUEST_TIMEOUT = 10  # 10s
RETRY_INITIAL_TIMEOUT = 0.5  # 500ms
RETRY_MAX_TIMEOUT = 60  # 60s
RETRY_MAX_ATTEMPTS = 20
MULTIPLIER = 1.5

DAEMON_THREAD_JOIN_TIMEOUT = 10 # 10s
REQUEST_INTERVAL = 60 # 60s

class HttpSampler(Sampler):
    def __init__(self, meter_provider: MeterProvider, config: Configuration, initial: Optional[Dict[str, Any]],):
        super().__init__(meter_provider=meter_provider, config=config, logger=logging.getLogger(__name__), initial=initial)
        self._url = config.collector
        self._service = config.service
        self._headers = config.headers
        self._hostname = socket.gethostname()
        self._last_warning_message = None
        self._shutdown_event = threading.Event()
        self._daemon_thread = threading.Thread(name="HttpSampler", target=self._loop, daemon=True)
        self._daemon_thread.start()

    def __str__(self) -> str:
        return f"HTTP Sampler ({self._url})"

    def _warn(self, message: str, *args: Any):
        if message != self._last_warning_message:
            self.logger.warn(message, *args)
            self._last_warning_message = message
        else:
            self.logger.debug(message, *args)

    def shutdown(self):
        self._shutdown_event.set()
        if self._daemon_thread:
            self._daemon_thread.join(timeout=DAEMON_THREAD_JOIN_TIMEOUT)

    def _loop(self):
        # Initial fetch
        self._task()
        while not self._shutdown_event.wait(timeout=REQUEST_INTERVAL):
            self._task()

    def _task(self):
        try:
            unparsed = self._fetch_from_collector()
            parsed = self.update_settings(unparsed)
            if not parsed:
                self._warn("Retrieved sampling settings are invalid.")
        except Exception as error:
            message = "Failed to retrieve sampling settings"
            if isinstance(error, Exception):
                message += f" ({error})"
            message += ", tracing will be disabled after time-to-live of the previous settings expired, until valid ones are available."
            self._warn(message, error)

    def _fetch_from_collector(self):
        url = f"{self._url}/v1/settings/{self._service}/{self._hostname}"
        self.logger.debug(f"retrieving sampling settings from {url}")
        response = requests.get(url, headers=self._headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        self.logger.debug(f"received sampling settings response {response.text}")
        return response.json()
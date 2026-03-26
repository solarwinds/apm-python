# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""JSON file-based sampler that reads sampling settings from a local file."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from collections.abc import Sequence

from opentelemetry.context import Context
from opentelemetry.metrics import MeterProvider
from opentelemetry.sdk.resources import Attributes
from opentelemetry.sdk.trace.sampling import SamplingResult
from opentelemetry.trace import Link, SpanKind, TraceState
from typing_extensions import override

from solarwinds_apm.oboe.configuration import Configuration
from solarwinds_apm.oboe.sampler import Sampler

logger = logging.getLogger(__name__)

PATH = os.path.join(tempfile.gettempdir(), "solarwinds-apm-settings.json")


class JsonSampler(Sampler):
    """
    Sampler that reads sampling settings from a JSON file.

    Monitors a local JSON file and updates settings based on its contents.
    """

    def __init__(
        self,
        meter_provider: MeterProvider,
        config: Configuration,
        path: str = PATH,
    ):
        """
        Initialize the JsonSampler.

        Parameters:
        meter_provider (MeterProvider): The OpenTelemetry meter provider for metrics.
        config (Configuration): The APM configuration.
        path (str): Path to the JSON settings file. Defaults to PATH.
        """
        super().__init__(
            meter_provider=meter_provider,
            config=config,
            initial=None,
        )
        self._path = path
        self._expiry = time.time()
        self._loop()

    @override
    def should_sample(
        self,
        parent_context: Context | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        trace_state: TraceState | None = None,
    ) -> SamplingResult:
        self._loop()
        return super().should_sample(
            parent_context,
            trace_id,
            name,
            kind,
            attributes,
            links,
            trace_state,
        )

    def __str__(self) -> str:
        return f"JSON Sampler ({self._path})"

    def _loop(self):
        """
        Check and update settings from the JSON file if needed.

        Updates settings if within 10 seconds of expiry time.
        """
        # update if we're within 10s of expiry
        if time.time() + 10 < self._expiry:
            return
        try:
            unparsed = self._read()
        except (FileNotFoundError, json.JSONDecodeError) as error:
            logger.debug("missing or invalid settings file %s", str(error))
            return

        if not isinstance(unparsed, list) or len(unparsed) != 1:
            logger.debug("invalid settings file %s", str(unparsed))
            return

        parsed = self.update_settings(unparsed[0])
        if parsed:
            self._expiry = parsed.timestamp + parsed.ttl

    def _read(self):
        """
        Read and parse the JSON settings file.

        Returns:
        dict: The parsed JSON contents.

        Raises:
        FileNotFoundError: If the settings file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        """
        with open(self._path, encoding="utf-8") as file:
            contents = file.read()
        return json.loads(contents)

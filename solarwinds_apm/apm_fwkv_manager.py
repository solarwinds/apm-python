# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SolarWindsFrameworkKvManager:
    """SolarWinds Python framework KV Manager
    Stores Python framework name with version"""

    def __init__(self, **kwargs: int) -> None:
        self.__cache = {}

    def __delitem__(self, key: str) -> None:
        del self.__cache[key]

    def __getitem__(self, key: str) -> Any:
        return self.__cache[key]

    def __setitem__(self, key: str, value: str) -> None:
        self.__cache[key] = value

    def __str__(self) -> str:
        return f"{self.__cache}"

    def get(self, key: str, default: Any = None) -> Any:
        return self.__cache.get(key, default)

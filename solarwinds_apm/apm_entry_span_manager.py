import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class SolarwindsEntrySpanManager:
    def __init__(self, **kwargs: int) -> None:
        self.__cache = {}

    def __delitem__(self, key: str) -> None:
        del self.__cache[key]

    def __getitem__(self, key: str) -> Any:
        return self.__cache[key]

    def __setitem__(self, key: str, value: str) -> None:
        self.__cache[key] = value

    def __str__(self) -> str:
        return json.dumps(self.__cache)

    def get(self, key: str, default: Any = None) -> Any:
        return self.__cache.get(key, default)

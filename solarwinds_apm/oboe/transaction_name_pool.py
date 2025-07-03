import heapq
import time
from functools import total_ordering


@total_ordering
class NameItem:
    def __init__(self, name: str, timestamp: int):
        self._name = name
        self._timestamp = timestamp

    @property
    def name(self) -> str:
        return self._name

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: int):
        self._timestamp = value

    def __lt__(self, other):
        return self._timestamp < other.timestamp

    def __eq__(self, other):
        if isinstance(other, NameItem):
            return (
                self._timestamp == other.timestamp and self._name == other.name
            )
        return NotImplemented


TRANSACTION_NAME_POOL_TTL = 60  # 1 minute
TRANSACTION_NAME_POOL_MAX = 200
TRANSACTION_NAME_MAX_LENGTH = 256
TRANSACTION_NAME_DEFAULT = "other"


class TransactionNamePool:
    def __init__(
        self,
        max_size: int = TRANSACTION_NAME_POOL_MAX,
        ttl: int = TRANSACTION_NAME_POOL_TTL,
        max_length: int = TRANSACTION_NAME_MAX_LENGTH,
        default: str = TRANSACTION_NAME_DEFAULT,
    ):
        self._min_heap: list[NameItem] = []
        self._pool: dict[str, NameItem] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._max_length = max_length
        self._default = default

    def _housekeep(self):
        now = int(time.time())
        while (
            len(self._min_heap) > 0
            and self._min_heap[0].timestamp + self._ttl < now
        ):
            item = heapq.heappop(self._min_heap)
            if isinstance(item, NameItem):
                del self._pool[item.name]

    def registered(self, name: str) -> str:
        # housekeep pool for every call
        self._housekeep()
        name = name[: self._max_length]
        if name in self._pool:
            # update timestamp and heapify
            item = self._pool[name]
            item.timestamp = int(time.time())
            heapq.heapify(self._min_heap)
            return name
        if len(self._pool) >= self._max_size:
            return self._default
        item = NameItem(name=name, timestamp=int(time.time()))
        self._pool[name] = item
        heapq.heappush(self._min_heap, item)
        return name

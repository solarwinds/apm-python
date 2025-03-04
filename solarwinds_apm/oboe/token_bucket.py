import time

class _TokenBucket(object):
    def __init__(self, capacity : float = 0, rate : float = 0):
        self._capacity = capacity
        self._rate = rate
        self._tokens = capacity
        self._last_used = time.time()

    @property
    def capacity(self):
        return self._capacity

    @property
    def rate(self):
        return self._rate

    @property
    def tokens(self):
        self._calculate_tokens()
        return self._tokens

    def _calculate_tokens(self):
        now = time.time()
        elapsed = now - self._last_used
        self._last_used = now
        self._tokens += (elapsed * self.rate)
        self._tokens = min(self._tokens, self.capacity)

    def update(self, new_capacity = None, new_rate = None):
        self._calculate_tokens()
        if new_capacity is not None:
            # negative means reset to 0
            new_capacity = max(0, new_capacity)
            diff = new_capacity - self.capacity
            self._capacity = new_capacity
            self._tokens += diff
            self._tokens = max(float(0), self._tokens)
        if new_rate is not None:
            new_rate = max(0, new_rate)
            self._rate = new_rate

    def consume(self, tokens = 1):
        self._calculate_tokens()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def __str__(self):
        return f"_TokenBucket(capacity={self._capacity}, rate={self._rate})"
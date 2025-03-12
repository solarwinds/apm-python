# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import time


class _TokenBucket:
    def __init__(self, capacity: float = 0, rate: float = 0):
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
        self._tokens += elapsed * self.rate
        self._tokens = min(self._tokens, self.capacity)

    def update(self, new_capacity=None, new_rate=None):
        """
        Update the capacity and rate of the token bucket.
        """
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

    def consume(self, tokens=1):
        """
        Consume the specified number of tokens from the bucket.
        """
        self._calculate_tokens()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def __str__(self):
        return f"_TokenBucket(capacity={self._capacity}, rate={self._rate})"

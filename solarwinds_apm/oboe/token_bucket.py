# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Token bucket algorithm implementation for rate limiting."""

import os
import threading
import time
import weakref


class _TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Thread-safe implementation that refills tokens at a specified rate and
    handles process forking correctly.
    """

    def __init__(self, capacity: float = 0, rate: float = 0):
        """
        Initialize the TokenBucket.

        Parameters:
        capacity (float): The maximum number of tokens the bucket can hold. Defaults to 0.
        rate (float): The rate at which tokens are added per second. Defaults to 0.
        """
        self._capacity = capacity
        self._rate = rate
        self._tokens = capacity
        self._last_used = time.time()
        self._lock = threading.Lock()
        self._pid = os.getpid()
        # Register fork handler to reinitialize lock in child processes.
        # Prevents deadlocks from inheriting locked state when parent forks
        # (e.g., gunicorn pre-fork workers).
        if hasattr(os, "register_at_fork"):
            weak_reinit = weakref.WeakMethod(self._at_fork_reinit)
            # pylint: disable=unnecessary-lambda
            os.register_at_fork(after_in_child=lambda: weak_reinit()())

    @property
    def capacity(self):
        with self._lock:
            return self._capacity

    @property
    def rate(self):
        with self._lock:
            return self._rate

    @property
    def tokens(self):
        with self._lock:
            self._calculate_tokens()
            return self._tokens

    def _calculate_tokens(self):
        """
        Calculate and update the current token count based on elapsed time.

        Updates tokens based on the rate and time elapsed since last use.
        """
        now = time.time()
        elapsed = now - self._last_used
        self._last_used = now
        self._tokens += elapsed * self._rate
        self._tokens = min(self._tokens, self._capacity)

    def _at_fork_reinit(self):
        """
        Reinitialize lock and state after fork to avoid deadlocks.

        When a process forks, locks must be recreated in the child process
        to avoid inheriting locked state from the parent. Token state is
        reset to ensure child processes start with a full bucket.
        """
        self._lock = threading.Lock()
        self._tokens = self._capacity
        self._last_used = time.time()
        self._pid = os.getpid()

    def update(self, new_capacity=None, new_rate=None):
        """
        Update the capacity and rate of the token bucket.

        Parameters:
        new_capacity (float | None): The new bucket capacity. Negative values reset to 0. Defaults to None.
        new_rate (float | None): The new token generation rate. Negative values reset to 0. Defaults to None.
        """
        with self._lock:
            self._calculate_tokens()
            if new_capacity is not None:
                # negative means reset to 0
                new_capacity = max(0, new_capacity)
                diff = new_capacity - self._capacity
                self._capacity = new_capacity
                self._tokens += diff
                self._tokens = max(float(0), self._tokens)
            if new_rate is not None:
                new_rate = max(0, new_rate)
                self._rate = new_rate

    def consume(self, tokens=1):
        """
        Consume the specified number of tokens from the bucket.

        Parameters:
        tokens (int): The number of tokens to consume. Defaults to 1.

        Returns:
        bool: True if tokens were successfully consumed, False if insufficient tokens available.
        """
        with self._lock:
            self._calculate_tokens()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def __str__(self):
        return f"_TokenBucket(capacity={self._capacity}, rate={self._rate})"

# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import threading
import time

from solarwinds_apm.oboe.token_bucket import _TokenBucket


def test_initialization():
    bucket = _TokenBucket(capacity=10, rate=1)
    assert bucket.capacity == 10
    assert bucket.rate == 1


def test_update():
    bucket = _TokenBucket(capacity=10, rate=1)
    bucket.update(new_capacity=20, new_rate=2)
    assert bucket.capacity == 20
    assert bucket.rate == 2


def test_consume():
    bucket = _TokenBucket(capacity=10)
    assert bucket.consume(5) is True
    assert bucket.tokens == 5
    assert bucket.consume(6) is False
    assert bucket.tokens == 5


def test_starts_full():
    bucket = _TokenBucket(capacity=2, rate=1)
    assert bucket.consume(2) is True


def test_can_not_consume_more_than_it_contains():
    bucket = _TokenBucket(capacity=1, rate=1)
    assert bucket.consume(2) is False
    assert bucket.consume() is True


def test_replenishes_over_time():
    bucket = _TokenBucket(capacity=2, rate=1)
    assert bucket.consume(2) is True
    time.sleep(2)
    assert bucket.consume(2) is True


def test_does_not_replenish_more_than_its_capacity():
    bucket = _TokenBucket(capacity=2, rate=1)
    assert bucket.consume(2) is True
    time.sleep(2)
    assert bucket.consume(4) is False


def test_can_be_updated():
    bucket = _TokenBucket(capacity=1, rate=1)
    assert bucket.consume(2) is False
    bucket.update(new_capacity=2)
    assert bucket.consume(2) is True


def test_decreases_tokens_to_capacity_when_updating_to_a_lower_one():
    bucket = _TokenBucket(capacity=2, rate=1)
    bucket.update(new_capacity=1)
    assert bucket.consume(2) is False


def test_can_be_updated_while_running():
    bucket = _TokenBucket(capacity=8, rate=0)
    assert bucket.consume(8) is True
    bucket.update(new_rate=2)
    time.sleep(4)
    assert bucket.consume(8) is True


def test_defaults_to_zero():
    bucket = _TokenBucket()
    time.sleep(1)
    assert bucket.consume() is False


def test_concurrent_consume_does_not_over_consume():
    bucket = _TokenBucket(capacity=100, rate=0)
    consumed_count = [0]
    lock = threading.Lock()

    def consume_tokens():
        if bucket.consume(1):
            with lock:
                consumed_count[0] += 1

    threads = []
    for _ in range(150):
        thread = threading.Thread(target=consume_tokens)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Exactly 100 tokens in bucket were consumed by 150 threads
    assert consumed_count[0] == 100


def test_concurrent_property_access():
    bucket = _TokenBucket(capacity=50, rate=5)
    results = {"capacity": [], "rate": [], "tokens": []}
    errors = []

    def read_properties():
        try:
            results["capacity"].append(bucket.capacity)
            results["rate"].append(bucket.rate)
            results["tokens"].append(bucket.tokens)
        except Exception as e:
            errors.append(e)

    threads = []
    for _ in range(50):
        thread = threading.Thread(target=read_properties)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Multiple threads safely and correctly read bucket values
    assert len(errors) == 0
    assert all(c == 50 for c in results["capacity"])
    assert all(r == 5 for r in results["rate"])
    assert all(isinstance(t, (int, float)) for t in results["tokens"])


def test_concurrent_update_and_consume():
    bucket = _TokenBucket(capacity=10, rate=1)
    errors = []

    def update_bucket():
        try:
            for _ in range(10):
                bucket.update(new_capacity=20, new_rate=2)
                time.sleep(0.01)
        except Exception as e:
            errors.append(e)

    def consume_from_bucket():
        try:
            for _ in range(10):
                bucket.consume(1)
                time.sleep(0.01)
        except Exception as e:
            errors.append(e)

    threads = []
    for _ in range(5):
        threads.append(threading.Thread(target=update_bucket))
        threads.append(threading.Thread(target=consume_from_bucket))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Concurrent updates and consumes don't cause race conditions
    assert len(errors) == 0
    assert bucket.capacity == 20
    assert bucket.rate == 2


def test_fork_reinitializes_lock():
    if not hasattr(os, "fork"):
        return

    bucket = _TokenBucket(capacity=10, rate=1)
    bucket.consume(5)
    parent_pid = os.getpid()
    # Create a pipe for child to communicate back
    read_fd, write_fd = os.pipe()

    # Create child process to verify fork handler reinitializes lock
    pid = os.fork()

    if pid == 0:
        # Child process
        os.close(read_fd)
        try:
            # Verify lock works in child
            result = bucket.consume(3)
            # Verify state was reset after fork
            tokens = bucket.tokens
            child_pid = os.getpid()

            # Send results back to parent
            message = f"{result},{tokens},{child_pid}\n".encode()
            os.write(write_fd, message)
            os.close(write_fd)
            os._exit(0)  # Use _exit to avoid cleanup issues
        except Exception as e:
            import traceback
            error_msg = f"ERROR:{e}:{traceback.format_exc()}\n".encode()
            os.write(write_fd, error_msg)
            os.close(write_fd)
            os._exit(1)  # Use _exit to avoid cleanup issues
    else:
        # Parent process
        os.close(write_fd)
        # Wait for child
        _, status = os.waitpid(pid, 0)

        # Read result from child
        result_bytes = os.read(read_fd, 1024)
        os.close(read_fd)
        result_str = result_bytes.decode().strip()

        # Check for errors first
        if result_str.startswith("ERROR"):
            raise AssertionError(f"Child encountered error: {result_str}")

        # Verify child exited successfully
        exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
        assert exit_code == 0, f"Child process failed with exit code {exit_code}, output: {result_str}"

        # Parse results
        parts = result_str.split(",")
        assert len(parts) == 3, f"Expected 3 parts but got {len(parts)}: {result_str}"
        result, tokens, child_pid = parts

        # Verify fork occurred
        assert int(child_pid) != parent_pid

        # Verify child could consume tokens (lock works)
        assert result == "True"

        # Verify child started with full bucket (state was reset)
        # Use approximate comparison due to tiny time elapsed between reset and token read
        assert abs(float(tokens) - 7.0) < 0.1  # 10 capacity - 3 consumed

        # Verify parent still has its state (tokens may have replenished slightly with rate=1)
        parent_tokens = bucket.tokens
        assert 5.0 <= parent_tokens <= 6.0  # Should be close to 5 but may have replenished


def test_multiple_threads_replenishing_and_consuming():
    bucket = _TokenBucket(capacity=50, rate=10)  # 10 tokens per second
    total_consumed = [0]
    lock = threading.Lock()
    errors = []

    def consumer():
        try:
            for _ in range(20):
                if bucket.consume(1):
                    with lock:
                        total_consumed[0] += 1
                time.sleep(0.05)
        except Exception as e:
            errors.append(e)

    threads = []
    for _ in range(5):
        thread = threading.Thread(target=consumer)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    assert len(errors) == 0
    # With 10 tokens/sec rate and ~1 second of sleep time,
    # we should consume initial capacity plus some replenished tokens
    assert total_consumed[0] >= 50  # At least initial capacity
    assert total_consumed[0] <= 100  # But not more than initial + 1 sec replenishment

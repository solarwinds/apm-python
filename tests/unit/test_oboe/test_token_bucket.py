# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

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

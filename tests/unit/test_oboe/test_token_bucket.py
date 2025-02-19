import time

from solarwinds_apm.oboe.token_bucket import _TokenBucket


def test_initialization():
    bucket = _TokenBucket(capacity=10, rate=1, interval=1)
    assert bucket.capacity == 10
    assert bucket.rate == 1
    assert bucket.interval == 1
    assert bucket.tokens == 10


def test_capacity_setter():
    bucket = _TokenBucket(capacity=10)
    bucket.capacity = 20
    assert bucket.capacity == 20


def test_rate_setter():
    bucket = _TokenBucket(rate=1)
    bucket.rate = 2
    assert bucket.rate == 2


def test_interval_setter():
    bucket = _TokenBucket(interval=1)
    bucket.interval = 2
    assert bucket.interval == 2


def test_tokens_setter():
    bucket = _TokenBucket(capacity=10)
    bucket.tokens = 5
    assert bucket.tokens == 5
    bucket.tokens = 15
    assert bucket.tokens == 10  # Should not exceed capacity


def test_update():
    bucket = _TokenBucket(capacity=10, rate=1, interval=1)
    bucket.update(capacity=20, rate=2, interval=2)
    assert bucket.capacity == 20
    assert bucket.rate == 2
    assert bucket.interval == 2
    assert bucket.tokens == 20


def test_consume():
    bucket = _TokenBucket(capacity=10)
    assert bucket.consume(5) is True
    assert bucket.tokens == 5
    assert bucket.consume(6) is False
    assert bucket.tokens == 5


def test_start_stop():
    bucket = _TokenBucket(capacity=10, rate=1, interval=0.1)
    assert bucket.consume(10) is True
    bucket.start()
    time.sleep(0.5)
    assert bucket.tokens > 0  # Tokens should have increased
    bucket.stop()
    tokens_after_stop = bucket.tokens
    time.sleep(0.5)
    assert bucket.tokens == tokens_after_stop  # Tokens should not increase after stop


def test_starts_full():
    bucket = _TokenBucket(capacity=2, rate=1, interval=1)
    assert bucket.consume(2) is True


def test_can_not_consume_more_than_it_contains():
    bucket = _TokenBucket(capacity=1, rate=1, interval=1)
    assert bucket.consume(2) is False
    assert bucket.consume() is True


def test_replenishes_over_time():
    bucket = _TokenBucket(capacity=2, rate=1, interval=0.1)
    assert bucket.consume(2) is True
    bucket.start()
    time.sleep(0.5)
    bucket.stop()
    assert bucket.consume(2) is True


def test_does_not_replenish_more_than_its_capacity():
    bucket = _TokenBucket(capacity=2, rate=1, interval=0.1)
    assert bucket.consume(2) is True
    bucket.start()
    time.sleep(1)
    bucket.stop()
    assert bucket.consume(4) is False


def test_can_be_updated():
    bucket = _TokenBucket(capacity=1, rate=1, interval=1)
    assert bucket.consume(2) is False
    bucket.update(capacity=2)
    assert bucket.consume(2) is True


def test_decreases_tokens_to_capacity_when_updating_to_a_lower_one():
    bucket = _TokenBucket(capacity=2, rate=1, interval=10)
    bucket.update(capacity=1)
    assert bucket.consume(2) is False


def test_can_be_updated_while_running():
    bucket = _TokenBucket(capacity=8, rate=0, interval=0.1)
    assert bucket.consume(8) is True
    bucket.start()
    bucket.update(rate=2, interval=0.05)
    time.sleep(1)
    bucket.stop()
    assert bucket.consume(8) is True


def test_defaults_to_zero():
    bucket = _TokenBucket()
    bucket.start()
    time.sleep(1)
    bucket.stop()
    assert bucket.consume() is False

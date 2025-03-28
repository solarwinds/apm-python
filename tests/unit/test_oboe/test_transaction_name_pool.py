import pytest
import time
from solarwinds_apm.oboe.transaction_name_pool import TransactionNamePool, NameItem

@pytest.fixture
def pool():
    return TransactionNamePool()

def test_register_name(pool):
    name = "test_name"
    registered_name = pool.registered(name)
    assert registered_name == name
    assert name in pool._pool
    assert len(pool._min_heap) == 1

def test_register_name_exceeds_max_length(pool):
    long_name = "a" * (pool._max_length + 10)
    registered_name = pool.registered(long_name)
    assert registered_name == long_name[:pool._max_length]
    assert registered_name in pool._pool

def test_register_name_exceeds_max_size(pool):
    for i in range(pool._max_size):
        pool.registered(f"name_{i}")
    assert len(pool._pool) == pool._max_size
    assert len(pool._min_heap) == pool._max_size
    default_name = pool.registered("new_name")
    assert default_name == pool._default

def test_housekeep(pool):
    name = "test_name"
    pool.registered(name)
    pool._pool[name].timestamp -= (pool._ttl + 1)
    pool._housekeep()
    assert name not in pool._pool
    assert len(pool._min_heap) == 0
    assert len(pool._pool) == 0

def test_update_timestamp(pool):
    name = "test_name"
    pool.registered(name)
    old_timestamp = pool._pool[name].timestamp
    time.sleep(1)
    pool.registered(name)
    new_timestamp = pool._pool[name].timestamp
    assert new_timestamp > old_timestamp

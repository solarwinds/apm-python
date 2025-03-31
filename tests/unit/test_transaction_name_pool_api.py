from solarwinds_apm.oboe import (
    get_transaction_name_pool,
    TransactionNamePool,
)

def test_get_transaction_name_pool():
    local_pool = TransactionNamePool()
    global_pool = get_transaction_name_pool()
    another_global_pool = get_transaction_name_pool()
    assert isinstance(local_pool, TransactionNamePool)
    assert isinstance(global_pool, TransactionNamePool)
    assert isinstance(another_global_pool, TransactionNamePool)
    assert local_pool != global_pool
    assert global_pool == another_global_pool

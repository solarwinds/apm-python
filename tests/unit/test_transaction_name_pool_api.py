# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

from solarwinds_apm.oboe import (
    TransactionNamePool,
    get_transaction_name_pool,
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

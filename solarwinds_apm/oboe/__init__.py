# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

"""Transaction name pool management for SolarWinds APM."""

from __future__ import annotations

import logging
from typing import cast

from opentelemetry.util._once import Once

from solarwinds_apm.oboe.transaction_name_pool import TransactionNamePool

logger = logging.getLogger(__name__)

_TRANSACTION_NAME_POOL_SET_ONCE = Once()
_transaction_name_pool: TransactionNamePool | None = None


def _set_transaction_name_pool(
    transaction_name_pool: TransactionNamePool,
) -> None:
    """
    Set the global transaction name pool instance.

    This function ensures the pool is set only once using the Once mechanism.

    Parameters:
    transaction_name_pool (TransactionNamePool): The transaction name pool instance to set globally.
    """

    def set_tp() -> None:
        global _transaction_name_pool  # pylint: disable=global-statement
        _transaction_name_pool = transaction_name_pool

    _TRANSACTION_NAME_POOL_SET_ONCE.do_once(set_tp)


def get_transaction_name_pool() -> TransactionNamePool:
    """
    Get the current global TransactionNamePool object.

    If no pool exists, creates and initializes a new one.

    Returns:
    TransactionNamePool: The global transaction name pool instance.
    """
    if _transaction_name_pool is None:
        transaction_name_pool = TransactionNamePool()
        _set_transaction_name_pool(transaction_name_pool)
    # _transaction_name_pool will have been set by one thread
    return cast("TransactionNamePool", _transaction_name_pool)

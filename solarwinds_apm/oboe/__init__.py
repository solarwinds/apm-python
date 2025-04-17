# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import Optional, cast

from opentelemetry.util._once import Once

from solarwinds_apm.oboe.transaction_name_pool import TransactionNamePool

logger = logging.getLogger(__name__)

_TRANSACTION_NAME_POOL_SET_ONCE = Once()
# pylint: disable=consider-alternative-union-syntax
_TRANSACTION_NAME_POOL: Optional[TransactionNamePool] = None


def _set_transaction_name_pool(
    transaction_name_pool: TransactionNamePool,
) -> None:
    def set_tp() -> None:
        global _TRANSACTION_NAME_POOL  # pylint: disable=global-statement
        _TRANSACTION_NAME_POOL = transaction_name_pool

    _TRANSACTION_NAME_POOL_SET_ONCE.do_once(set_tp)


def get_transaction_name_pool() -> TransactionNamePool:
    """Gets the current global :class:`~.TransactionNamePool` object."""
    if _TRANSACTION_NAME_POOL is None:
        transaction_name_pool = TransactionNamePool()
        _set_transaction_name_pool(transaction_name_pool)
    # _TRANSACTION_NAME_POOL will have been set by one thread
    return cast("TransactionNamePool", _TRANSACTION_NAME_POOL)

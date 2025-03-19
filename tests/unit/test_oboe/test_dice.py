# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from collections import Counter

import pytest

from solarwinds_apm.oboe.dice import _Dice


@pytest.fixture
def dice():
    return _Dice(scale=100, rate=50)


@pytest.fixture
def dice_full_rate():
    return _Dice(scale=100, rate=100)


@pytest.fixture
def dice_zero_rate():
    return _Dice(scale=100, rate=0)


def test_roll_within_range(dice):
    result = dice.roll()
    assert result in [True, False]


def test_roll_randomness(dice):
    results = [dice.roll() for _ in range(1000)]
    count = Counter(results)
    assert abs(count[True] - count[False]) < 100


def test_rate_setter_getter(dice):
    dice.rate = 5
    assert dice.rate == 5


def test_rate_setter_negative_value(dice):
    dice.rate = -1
    assert dice.rate == 0


def test_roll_zero_rate(dice_zero_rate):
    assert all(dice_zero_rate.roll() == False for _ in range(1000))


def test_roll_full_rate(dice_full_rate):
    assert all(dice_full_rate.roll() == True for _ in range(1000))

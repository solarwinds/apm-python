import pytest
from collections import Counter
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
    assert abs(count[True]-count[False]) < 100

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


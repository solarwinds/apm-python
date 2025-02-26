import pytest
from unittest.mock import patch
from solarwinds_apm.oboe.backoff import backoff

@patch('time.sleep', return_value=None)
def test_backoff_success(mock_sleep):
    @backoff(base=0.1, multiplier=2, cap=1, retries=3)
    def always_succeed():
        return "success"

    result = always_succeed()
    assert result == "success"
    mock_sleep.assert_not_called()

@patch('time.sleep', return_value=None)
def test_backoff_failure(mock_sleep):
    @backoff(base=0.1, multiplier=2, cap=1, retries=3)
    def always_fail():
        raise Exception("failure")

    with pytest.raises(Exception) as excinfo:
        always_fail()
    assert str(excinfo.value) == "failure"
    assert mock_sleep.call_count == 3

@patch('time.sleep', return_value=None)
def test_backoff_eventual_success(mock_sleep):
    attempts = 0

    @backoff(base=0.1, multiplier=2, cap=1, retries=3)
    def succeed_after_two_attempts():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception("failure")
        return "success"

    result = succeed_after_two_attempts()
    assert result == "success"
    assert mock_sleep.call_count == 2
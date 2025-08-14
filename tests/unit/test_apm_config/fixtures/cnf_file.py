import pytest


@pytest.fixture
def fixture_cnf_file(mocker):
    read_data = '{"foo": "bar"}'
    mocked_cnf_file_data = mocker.mock_open(read_data=read_data)
    builtin_open = "builtins.open"
    mocker.patch(builtin_open, mocked_cnf_file_data)


@pytest.fixture
def fixture_cnf_file_invalid_json(mocker):
    mocked_cnf_file_data = mocker.mock_open(read_data="invalid-foo")
    builtin_open = "builtins.open"
    mocker.patch(builtin_open, mocked_cnf_file_data)

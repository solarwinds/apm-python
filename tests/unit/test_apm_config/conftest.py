"""Pytest configuration and fixtures for test_apm_config tests."""

# Import all fixtures to make them available to tests
from .fixtures.cnf_dict import (
    fixture_cnf_dict,
    fixture_cnf_dict_enabled_false,
    fixture_cnf_dict_enabled_false_mixed_case,
)
from .fixtures.cnf_file import (
    fixture_cnf_file,
    fixture_cnf_file_invalid_json,
)
from .fixtures.env_vars import (
    fixture_mock_env_vars,
)

__all__ = [
    "fixture_cnf_dict",
    "fixture_cnf_dict_enabled_false",
    "fixture_cnf_dict_enabled_false_mixed_case",
    "fixture_cnf_file",
    "fixture_cnf_file_invalid_json",
    "fixture_mock_env_vars",
]

# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

import re

from solarwinds_apm import apm_config


class TestSolarWindsApmConfigTxnFilters:
    def test_update_transaction_filters_none(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters({})
        assert cfg.get("transaction_filters") == []

    def test_update_transaction_filters_not_list(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters({"transactionSettings": "foo"})
        assert cfg.get("transaction_filters") == []

    def test_update_transaction_filters_missing_tracing(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters(
            {"transactionSettings": [{"regex": "foo"}]}
        )
        assert cfg.get("transaction_filters") == []

    def test_update_transaction_filters_invalid_tracing(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters(
            {"transactionSettings": [{"regex": "foo", "tracing": "not-valid"}]}
        )
        assert cfg.get("transaction_filters") == []

    def test_update_transaction_filters_missing_regex(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters(
            {"transactionSettings": [{"tracing": "enabled"}]}
        )
        assert cfg.get("transaction_filters") == []

    def test_update_transaction_filters_invalid_type_regex(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters(
            {"transactionSettings": [{"regex": 123, "tracing": "enabled"}]}
        )
        assert cfg.get("transaction_filters") == []

    def test_update_transaction_filters_empty_regex(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters(
            {"transactionSettings": [{"regex": "", "tracing": "enabled"}]}
        )
        assert cfg.get("transaction_filters") == []

    def test_update_transaction_filters_invalid_compile_regex(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters(
            {"transactionSettings": [{"regex": "[", "tracing": "enabled"}]}
        )
        assert cfg.get("transaction_filters") == []

    def test_update_transaction_filters(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters(
            {
                "transactionSettings": [
                    {"regex": "foo", "tracing": "enabled"},
                    {"regex": "bar", "tracing": "disabled"},
                ]
            }
        )
        assert cfg.get("transaction_filters") == [
            {"regex": re.compile("foo"), "tracing_mode": 1},
            {"regex": re.compile("bar"), "tracing_mode": 0},
        ]

    def test_update_transaction_filters_multiple_regex_use_first(self):
        cfg = apm_config.SolarWindsApmConfig()
        cfg.update_transaction_filters(
            {
                "transactionSettings": [
                    {"regex": "foo", "tracing": "enabled"},
                    {"regex": "bar", "tracing": "disabled"},
                    {"regex": "foo", "tracing": "disabled"},
                    {"regex": "bar", "tracing": "enabled"},
                ]
            }
        )
        assert cfg.get("transaction_filters") == [
            {"regex": re.compile("foo"), "tracing_mode": 1},
            {"regex": re.compile("bar"), "tracing_mode": 0},
        ]

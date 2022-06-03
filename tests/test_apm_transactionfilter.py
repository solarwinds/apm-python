""" Test transaction filter module """
import re
import unittest

import solarwinds_apm
from solarwinds_apm.apm_transactionfilter import (
    ExtensionsRule, RegexRule, UrlFilter, UrlGetter, add_transaction_filter_rule)
from solarwinds_apm.apm_config import OboeTracingMode


class TestTransactionFilterBase(unittest.TestCase):
    # always check the solarwinds_apm base logger to catch all messages emitted by the package
    logger = solarwinds_apm.apm_logging.logger

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def assert_transaction_filter_rules(self, config, url_filter):
        """Verifies that custom transaction filter has implemented all rules provided by the config"""
        self.assertEqual(len(url_filter._filter_rules), len(config))
        for i in range(len(url_filter._filter_rules)):  # pylint: disable-msg=consider-using-enumerate
            found_rule = url_filter._filter_rules[i]
            if isinstance(found_rule, RegexRule):
                self.assertEqual(found_rule._regex, re.compile(config[i]['regexp']))
            elif isinstance(found_rule, ExtensionsRule):
                self.assertEqual(found_rule._extensions, tuple(config[i]['extensions'].strip().split(' ')))
            else:
                self.fail("Unexpected filter rule instance of '{}' detected.".format(found_rule))
            self.assertEqual(found_rule.tracing_mode, OboeTracingMode.get_oboe_trace_mode(config[i]['tracing']))


class TestUrlFilter(TestTransactionFilterBase):
    """Test the instantiation and configuration of UrlFilter class for custom transaction filtering."""
    def test_init_with_invalid_object(self):
        """Instantiate UrlFilter with an invalid object"""
        with self.assertLogs(self.logger.name) as cm:
            url_filter = UrlFilter("some random string")
        self.assertEqual(len(cm.records), 1, 'Unexpected log messages detected! Log: {}'.format(cm.output))
        self.assertEqual(url_filter._filter_rules, [])

    def test_init_with_valid_rule(self):
        """Instantiate UrlFilter with valid filter rule"""
        config = {
            'type': 'url',
            'regexp': '.*/abc/.*',
            'tracing': 'disabled',
        }
        with self.assertLogs(self.logger.name) as cm:
            url_filter = UrlFilter(config)
            solarwinds_apm.apm_transactionfilter.logger.info('Logging dummy message to prevent assertLogs from asserting.')
        self.assertEqual(len(cm.records[1:]), 0, 'Unexpected log messages detected! Log: {}'.format(cm.output[1:]))
        self.assert_transaction_filter_rules((config, ), url_filter)

    def test_init_with_invalid_rule(self):
        """Instantiate UrlFilter with invalid filter rule"""
        config = {
            'type': 'some invalid type',
            'regexp': '.*/abc/.*',
            'tracing': 'disabled',
        }
        with self.assertLogs(self.logger.name) as cm:
            url_filter = UrlFilter(config)
        self.assertEqual(len(cm.records), 1, 'Unexpected log messages detected! Log: {}'.format(cm.output))
        self.assertEqual(len(url_filter._filter_rules), 0)

    def test_init_with_valid_tuple(self):
        """Instantiate UrlFilter with valid tuple of configuration dictionaries"""
        config = (
            {
                'type': 'url',
                'regexp': '.*/abc/.*',
                'tracing': 'disabled',
            },
            {
                'type': 'url',
                'extensions': 'css html',
                'tracing': 'disabled',
            },
        )
        with self.assertLogs(self.logger.name) as cm:
            url_filter = UrlFilter(config)
            solarwinds_apm.apm_transactionfilter.logger.info('Logging dummy message to prevent assertLogs from asserting.')
        self.assertEqual(len(cm.records[1:]), 0, 'Unexpected log messages detected! Log: {}'.format(cm.output[1:]))
        self.assert_transaction_filter_rules(config, url_filter)

    def test_with_valid_and_invalid_rules(self):
        """Instantiate UrlFilter with tuple having valid and invalid filter rules"""
        config = (
            {
                'type': 'url',
                'regexp': '.*/abc/.*',
                'tracing': 'disabled',
            },
            ('invalid', 'type'),
            {
                'type': 'url',
                'extensions': 'css html',
                'tracing': 'disabled',
            },
            {
                'type': 'something_invalid',
                'extensions': 'css html',
                'tracing': 'disabled',
            },
        )
        with self.assertLogs(self.logger.name) as cm:
            url_filter = UrlFilter(config)
        self.assertEqual(len(cm.records), 4, 'Unexpected log messages detected! Log: {}'.format(cm.output))
        self.assertEqual(len(url_filter._filter_rules), 2, 'UrlFilter configured with unexpected filter rules')
        self.assert_transaction_filter_rules((config[0], config[2]), url_filter)

    def test_filter_url_and_get_tracing(self):
        """Instantiate UrlFilter and match test urls"""
        config = (
            {
                'type': 'url',
                'regexp': '.*/abc/.*',
                'tracing': 'disabled',
            },
            {
                'type': 'url',
                'extensions': 'css html',
                'tracing': 'enabled',
            },
        )
        # set up url_filter instance
        url_filter = UrlFilter(config)

        # test with URL which only matches regex rule
        tracing_mode = url_filter.filter_url_and_get_tracing(UrlGetter('www.test_url.com/abc/123'))
        self.assertEqual(tracing_mode, OboeTracingMode.get_oboe_trace_mode('disabled'))

        # test with URL which should only matches extensions rule
        tracing_mode = url_filter.filter_url_and_get_tracing(UrlGetter('www.test_url.com/abc.html'))
        self.assertEqual(tracing_mode, OboeTracingMode.get_oboe_trace_mode('enabled'))

        # test with URL which does not match any rule
        tracing_mode = url_filter.filter_url_and_get_tracing(UrlGetter('www.test_url.com/abc.jpg'))
        self.assertEqual(tracing_mode, OboeTracingMode.get_oboe_trace_mode('unset'))

        # test with URL which matches both, regex rule and extensions rule
        tracing_mode = url_filter.filter_url_and_get_tracing(UrlGetter('www.test_url.com/abc/123.html'))
        self.assertEqual(tracing_mode, OboeTracingMode.get_oboe_trace_mode('disabled'))


class TestTransactionFilterApi(TestTransactionFilterBase):
    """Test the instantiation and configuration of UrlFilter class for custom transaction filtering."""
    def setUp(self):
        """Clear custom transaction filter configuration before running each test case"""
        solarwinds_apm.apm_transactionfilter.url_filter = None

    def test_with_valid_configuration(self):
        """Instantiate UrlFilter with valid config file"""
        config = (
            {
                'type': 'url',
                'regexp': '.*/abc/.*',
                'tracing': 'disabled',
            },
            {
                'type': 'url',
                'extensions': 'css html',
                'tracing': 'disabled',
            },
        )
        with self.assertLogs(self.logger.name) as cm:
            for rule in config:
                add_transaction_filter_rule(rule)
            solarwinds_apm.apm_transactionfilter.logger.info('Logging dummy message to prevent assertLogs from asserting.')
        self.assertEqual(len(cm.records[1:]), 0, 'Unexpected log messages detected! Log: {}'.format(cm.output[1:]))
        url_filter = solarwinds_apm.apm_transactionfilter.url_filter
        self.assert_transaction_filter_rules(config, url_filter)

    def test_configured_invalid(self):
        """Instantiate UrlFilter with invalid config file"""
        config = (
            {
                'type': 'url',
                'regexp': '.*/some_invalid_regex(/.*',
                'tracing': 'disabled',
            },
            {
                'type': 'some_type',
                'extensions': 'css html',
                'tracing': 'disabled',
            },
            {
                'type': 'url',
                'extensions': 'css html',
                'tracing': 'sometimes',
            },
            {
                'type': 'url',
                'extensions': 'css html',
                'tracing': 'disabled',
            },
            {
                'type': 'url',
                'extensions': 'css html',
                'invalid_key': 123,
            },
        )
        with self.assertLogs(self.logger.name) as cm:
            for rule in config:
                add_transaction_filter_rule(rule)
        self.assertEqual(len(cm.records), 4, 'Unexpected log messages detected! Log: {}'.format(cm.output))
        # make sure that correct rules are showing up in transaction filter rules
        url_filter = solarwinds_apm.apm_transactionfilter.url_filter
        self.assert_transaction_filter_rules((config[3], ), url_filter)

    def test_no_empty_transaction_filter(self):
        """Verify that transaction filter without rules is not instantiated"""
        config = ({
            'type': 'invalid_type',
            'regexp': '.*/abc/.*',
            'tracing': 'disabled',
        }, 'something invalid')
        with self.assertLogs(self.logger.name) as cm:
            for rule in config:
                add_transaction_filter_rule(rule)
                self.assertEqual(
                    solarwinds_apm.apm_transactionfilter.url_filter,
                    None,
                    "UrlFilter instance has been created unexpectedly")
        self.assertEqual(len(cm.records), 2, 'Unexpected log messages detected! Log: {}'.format(cm.output))

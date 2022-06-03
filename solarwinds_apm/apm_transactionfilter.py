#    Copyright 2021 SolarWinds, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Transaction filter for custom URL filtering
"""
import logging
import re

from solarwinds_apm import apm_config

logger = logging.getLogger(__name__)


class UrlGetter:
    """Base class which provides a common interface to retrieve the request URL from an instrumented framework. In case
    of complex/ time-consuming URL retrieval mechanisms, a derived class should be created which overrides set_url."""
    def __init__(self, url=None):
        """url is a string representing the request URL."""
        self._url = url

    def set_url(self):
        """This function must be defined in the inherited class, as URL retrieval depends on the instrumented framework.
        This function should not be called directly, but only through get_url to defer the URL reconstruction to the
        point when it is actually needed."""
        logger.error(
            "UrlGetter.set_url: set_url function of UrlGetter base class called. Setting url to an empty string.")
        self._url = ''

    def get_url(self):
        """Returns string representation of URL. If url has not been set yet, set_url will be invoked first to
        reconstruct the request URL. This allows deferring the URL reconstruction until it the URL is really needed."""
        if self._url is None:
            # None indicates, that set_url has not been called yet, thus first retrieve and store the URL.
            self.set_url()
        return self._url


class Rule:
    """Abstract base class for all filter rules."""
    def __init__(self, tracing_mode):
        self.tracing_mode = tracing_mode

    def match(self, url):
        """Must be overridden in every derived class."""


class RegexRule(Rule):
    """Performs a regex match with the provided string input."""
    def __init__(self, tracing_mode, regex):
        Rule.__init__(self, tracing_mode)
        self._regex = regex

    def __str__(self):
        return "RegexRule(_regex={}, tracing={})".format(self._regex, self.tracing_mode)

    def match(self, url):
        return bool(self._regex.match(url))


class ExtensionsRule(Rule):
    """Checks if provided input string ends with the (extension) strings in the extensions list."""
    def __init__(self, tracing_mode, extensions):
        Rule.__init__(self, tracing_mode)
        self._extensions = extensions

    def __str__(self):
        return "ExtensionsRule(_extensions={}, tracing={})".format(self._extensions, self.tracing_mode)

    def match(self, url):
        return url.endswith(self._extensions)


class UrlFilter:
    """URL filter consisting of a list of filter rules for custom URL filtering.
    A valid filter rule must be provided in form of a dictionary having a structure as outlined below:
    [0]
        {
            'type':  'url',
            'regexp': '.*/abc/.*',
            'tracing':  'disabled'
        }
    [1]
        {
            'type':  'url',
            'extensions':  'css html',
            'tracing':  'disabled'
        }
    i.e., each dictionary must have the keys 'type', 'tracing' and either 'regexp' or 'extensions'.
    """
    # possible combinations of keys in a valid entry for a filter rule
    allowed_config_keys = (set(('type', 'tracing', 'regexp')), set(('type', 'tracing', 'extensions')))

    def __init__(self, config=None):
        """UrlFilter can be configured by either a single configuration dictionary representing one filter rule or
        a tuple of configuration dictionaries, with each dictionary corresponding to one filter rule.
        The configuration tuple is intended for testing purposes only."""
        # list of filter rules, the first rule applicable to the URL to be filtered will determine the behaviour
        # of the custom transaction filter
        self._filter_rules = []

        if isinstance(config, tuple):
            for filter_rule in config:
                if not self.add_filter_rule(filter_rule):
                    logger.warning(
                        "Ignoring custom transaction filter rule {} provided through config tuple.".format(filter_rule))
        else:
            self.add_filter_rule(config)

    def __str__(self):
        return "{}({})".format(self.__class__, '[' + ', '.join([str(i) for i in self._filter_rules]) + ']')

    def add_filter_rule(self, config):
        """Adds the provided config dictionary as a custom transaction filter rule. Returns True if the entry could be
        created properly, False otherwise."""
        try:
            # Check proper structure of provided configuration
            if set(config) not in self.allowed_config_keys:
                logger.warning("Invalid transaction filter rule {} provided".format(config))
                raise KeyError
            if config['type'] != 'url':
                logger.warning("Expected 'url' for 'type', got '{}' instead".format(config['type']))
                raise ValueError
            if config['tracing'] not in ('enabled', 'disabled'):
                logger.warning(
                    "Expected 'enabled' or 'disabled' for 'tracing', got '{}' instead".format(config['tracing']))
                raise ValueError
            tracing_mode = apm_config.OboeTracingMode.get_oboe_trace_mode(config['tracing'])
            if 'regexp' in config:
                try:
                    regex = re.compile(config['regexp'])
                    self._filter_rules.append(RegexRule(tracing_mode, regex))
                    logger.debug("_add_filter_rule: adding new regex filter rule with pattern {}".format(regex.pattern))
                except Exception:
                    logger.warning("Invalid regular expression provided")
                    raise
            else:
                extensions = tuple(config['extensions'].strip().split(' '))
                self._filter_rules.append(ExtensionsRule(tracing_mode, extensions))
                logger.debug("_add_filter_rule: adding new extension filter rule for extensions {}".format(extensions))
        except Exception:
            return False
        return True

    def filter_url_and_get_tracing(self, url_getter):
        """Checks if the provided request URL matches any of the regular expressions or URL extensions. If any of the
        defined filter rules is applicable, the custom tracing mode corresponding to the first applicable rule will be
        returned. If none of the filter rules is applicable, -1 is returned.
        The url_getter parameter should be an instance of the UrlGetter class, if an invalid value has been provided,
        -1 will be returned (i.e. URL will not be filtered)."""
        try:
            url = url_getter.get_url()
            for filter_rule in self._filter_rules:
                if filter_rule.match(url):
                    return filter_rule.tracing_mode
        except Exception as e:
            # we catch all exceptions here, since we might get a url_getter object whose get_url does not provide a
            # string, which can lead to a variety of Exceptions thrown from the machter.filter calls
            logger.debug("filter_url_and_get_tracing got invalid url_getter object: {}".format(e))
        return apm_config.OboeTracingMode.OBOE_SETTINGS_UNSET


url_filter = None


def add_transaction_filter_rule(config):
    """Add filter rule provided in config to existing custom transaction filter instance. If no custom transaction
    filter exists, the function creates a new one and adds the provided filter rule.
    Returns True if provided filter rule was added successfully, False if rule could not be added.
    None."""
    global url_filter
    if url_filter:
        return url_filter.add_filter_rule(config)
    new_filter = UrlFilter(config)
    if new_filter._filter_rules != []:
        url_filter = new_filter
    return bool(url_filter)

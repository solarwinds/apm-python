#    Copyright 2022 SolarWinds, LLC
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
""" SolarWinds instrumentation API for Python.

apm_noop defines no-op classes for platforms we don't support building the c extension on
"""
# No-op classes intentionally left undocumented
# "Missing docstring"
# pylint: disable-msg=C0103
import threading


class Metadata:
    def __init__(self, _=None):
        pass

    @staticmethod
    def fromString(_):
        return Metadata()

    def createEvent(self):
        return Event()

    @staticmethod
    def makeRandom(flag=True):
        return Metadata(True)

    def copy(self):
        return self

    def isValid(self):
        return False

    def isSampled(self):
        return False

    def toString(self):
        return ''


class Context:
    transaction_dict = threading.local()

    @staticmethod
    def setTracingMode(_):
        return False

    @staticmethod
    def setTriggerMode(_):
        return False

    @staticmethod
    def setDefaultSampleRate(_):
        return False

    @staticmethod
    def getDecisions(*args, **kwargs):
        """
        This is the stub method in no-op mode. The corresponding method in the
        `normal` mode (when the instrumentation is working) is actually a wrapper
        of the `getDecisions` method of the Context class in swig/oboe.hpp.

        There are multiple return values in this method, which are:
        do_metrics, do_sample, sample_rate, sample_source, bucket_rate, bucket_capacity, typ, auth, status_msg,
        auth_msg, status

        Go to oboe_api.h to see the descriptions of all the return values.
        """
        return 0, 0, 0, 6, 0, 0, 0, -1, "", "", 0

    @staticmethod
    def get():
        return Metadata()

    @staticmethod
    def set(_):
        pass

    @staticmethod
    def fromString(_):
        return Context()

    @staticmethod
    def copy():
        return Context()

    @staticmethod
    def clear():
        pass

    @staticmethod
    def isValid():
        return False

    @staticmethod
    def toString():
        return ''

    @staticmethod
    def createEvent():
        return Event()

    @staticmethod
    def startTrace(_=None):
        return Event()

    @staticmethod
    def isReady(_):
        # unknown error
        return 0


class Event:
    def __init__(self, _=None, __=None):
        pass

    def addInfo(self, _, __):
        pass

    def addEdge(self, _):
        pass

    def addEdgeStr(self, _):
        pass

    def getMetadata(self):
        return Metadata()

    def metadataString(self):
        return ''

    def is_valid(self):
        return False

    @staticmethod
    def startTrace(_=None):
        return Event()


class Reporter:
    def __init__(self, *args, **kwargs):
        self.init_status = 0

    def sendReport(self, _, __=None):
        pass

    def sendStatus(self, _, __=None):
        pass

    def flush(self):
        pass


class Span:
    @staticmethod
    def createHttpSpan(_, __, ___, ____, _____, ______, _______):
        pass

    @staticmethod
    def createSpan(_, __, ___, ____):
        pass


class MetricTags:
    def __init__(self, count):
        super(MetricTags, self).__init__()

    @staticmethod
    def add(*args, **kwargs):
        pass


class CustomMetrics:
    @staticmethod
    def summary(*args, **kwargs):
        pass

    @staticmethod
    def increment(*args, **kwargs):
        pass


class Config:
    @staticmethod
    def getVersionString():
        return "No extension loaded."

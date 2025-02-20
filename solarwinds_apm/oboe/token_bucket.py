import sys
import threading


class _TokenBucket(object):
    MAX_INTERVAL = sys.maxsize
    DEFAULT_INTERVAL = 1

    def __init__(self, capacity=0, rate=0, interval=DEFAULT_INTERVAL):
        self._capacity = float(capacity)
        self._rate = float(rate)
        self._interval = float(interval)
        self._tokens = float(capacity)
        self._stopping = False
        self._lock = threading.Lock()
        self._condition = threading.Condition()
        self._timer = None

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, new_capacity):
        self._capacity = max([0, new_capacity])

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, new_rate):
        self._rate = max([0, new_rate])

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, new_interval):
        self._interval = max([0, min([_TokenBucket.MAX_INTERVAL, new_interval])])

    @property
    def tokens(self):
        ans = 0
        self._lock.acquire()
        try:
            ans = self._tokens
        finally:
            self._lock.release()
            return ans

    @tokens.setter
    def tokens(self, new_tokens):
        self._lock.acquire()
        try:
            self._tokens = max([0, min([self.capacity, new_tokens])])
        finally:
            self._lock.release()

    def update(self, capacity=None, rate=None, interval=None):
        if capacity is not None:
            diff = capacity - self.capacity
            self.capacity = capacity
            self.tokens += diff
        if rate is not None:
            self.rate = rate
        if interval is not None:
            self.interval = interval

    def consume(self, tokens=1):
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def start(self):
        with (self._condition):
            self._stopping = False
            self._timer = threading.Timer(self.interval, self.task)
            self._timer.start()

    def stop(self):
        with self._condition:
            self._timer.cancel()
            self._stopping = True
            self._condition.notify_all()

    def task(self):
        self.tokens += self.rate
        with (self._condition):
            predicate = self._condition.wait_for(lambda: self._stopping, self.interval)
            if predicate is False:
                # either self._stopping is False and the interval has elapsed
                self._timer = threading.Timer(self.interval, self.task)
                self._timer.start()

import random

class _Dice:
    def __init__(self, scale, rate = 0):
        self._scale = scale
        self._rate = rate

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, new_rate):
        self._rate = max([0, min([self._scale, new_rate])])

    def update(self, new_scale, new_rate):
        self._scale = new_scale
        self.rate = new_rate

    def roll(self):
        return random.random() * self._scale < self.rate
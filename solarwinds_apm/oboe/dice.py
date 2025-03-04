from random import random
from typing import Optional


class _Dice:
    def __init__(self, scale : int, rate : int = 0):
        self._scale = scale
        self._rate = rate

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, new_rate : int):
        self._rate = max([0, min([self._scale, new_rate])])

    def update(self, new_scale : int, new_rate : Optional[int] = None):
        self._scale = new_scale
        if new_rate is not None:
            self.rate = new_rate

    def roll(self):
        return random() * self._scale < self.rate

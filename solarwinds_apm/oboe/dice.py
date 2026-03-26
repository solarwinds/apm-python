# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Dice class for probabilistic sampling decisions."""

from __future__ import annotations

from random import random


class _Dice:
    """
    Probabilistic sampling decision maker using a dice roll metaphor.

    Uses a scale and rate to determine sampling probability.
    """

    def __init__(self, scale: int, rate: int = 0):
        """
        Initialize the Dice.

        Parameters:
        scale (int): The maximum value for the dice scale.
        rate (int): The current sampling rate. Defaults to 0.
        """
        self._scale = scale
        self._rate = rate

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, new_rate: int):
        self._rate = max([0, min([self._scale, new_rate])])

    def update(self, new_scale: int, new_rate: int | None = None):
        """
        Update the dice scale and optionally the rate.

        Parameters:
        new_scale (int): The new scale value.
        new_rate (int | None): The new rate value. Defaults to None.
        """
        self._scale = new_scale
        if new_rate is not None:
            self.rate = new_rate

    def roll(self) -> bool:
        """
        Roll the dice and return True if the roll is successful.

        Performs a probabilistic check based on the current rate and scale.

        Returns:
        bool: True if the random roll is less than the current rate, False otherwise.
        """
        return random() * self._scale < self.rate

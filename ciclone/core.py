
from typing import (
    Any,
    Optional,
    TYPE_CHECKING
)

import simpy

from .typing import *

# if TYPE_CHECKING:
#     from .element import simTime

"""
que 집어넣기에서 simpy로 변경
"""


class Environment(simpy.Environment):
    def __init__(self):
        super().__init__()

    def timeout(self, delay: simTime = 0, value: Optional[Any] = None):
        if callable(delay):
            delay = delay()

        return super().timeout(delay, value)

    @property
    def test(self):
        return 'test'

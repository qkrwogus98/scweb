from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
    Callable,
    Sequence,
    TYPE_CHECKING
)

from .base import Element
from ..entities import Entity
from ..typing import *


class Func(Element):
    """Consolidate Function node"""

    def __init__(self, description, followers, con: int):
        super().__init__(description)
        self.con = con
        self._length = 0
        self.fol(followers)

    async def __call__(self, entity: Optional[Entity] = None) -> GenReturn:
        start = self._call()

        self._length += 1
        self._env.trace(self, start, entity)  # self._length)

        if self._length < self.con:
            return -1
        else:
            self._env.trace(self, start, entity)
            self._length = 0

    def clear(self):
        super().clear()
        self._length = 0

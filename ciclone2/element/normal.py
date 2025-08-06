from collections import deque
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


class Normal(Element):
    """NORMAL element:

    An unconstrained work task. Entities are delayed for a specified amount of time."""

    def __init__(self, description, followers, duration: simTime):
        super().__init__(description)
        self.fol(followers)
        self.duration = duration

    async def call(self, entity: Optional[Entity] = None):
        self._env.trace(self, self._start, entity, arrival=True)
        await self._env.timeout(self.duration)

    def __repr__(self):
        res = super().__repr__()
        dur = f'{self.duration}' if callable(self.duration) else f'{self.duration:.3f}'
        return (
            f'<{res[1:-1]} duration={dur}>'
        )

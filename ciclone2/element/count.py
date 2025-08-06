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


class Count(Element):
    """COUNT node:

    Counts passing entities. Primarily used to track production in a system."""

    def __init__(self, description, followers, quantity: int = 1):
        """
        asdasdasd

        :param description:
        :param followers:
        :param quantity:
        """
        super().__init__(description)
        self.quantity = quantity
        self.fol(followers)

        self.count = 0

    async def call(self, entity: Optional[Entity] = None):
        # start = super()._call(self.quantity)
        # yield self._env.timeout()
        await self._env.timeout()

        self.count += self.quantity

        # self._env.trace(self, start, entity)

    def clear(self):
        super().clear()
        self.count = 0

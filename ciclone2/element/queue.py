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


def _unimplemented(self, *_: Any):
    raise NotImplementedError


class _Deque(deque):
    def __init__(self, queue: 'Queue' = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._que = queue

    def _change(self):
        if self._que is not None:
            # noinspection PyProtectedMember
            self._que._env.queue_change(self._que.id, len(self._que))

    def append(self, *args, **kwargs):
        super().append(*args, **kwargs)
        self._change()

    def popleft(self, *args, **kwargs):
        get = super().popleft()
        self._change()
        return get


# TODO: threading lock 등..
class Queue(Element):
    """QUEUE node:

    The idle state of an entity. Represents a queue in which entities are waiting for use."""

    def __init__(self, description: str, length: int = 0, start: Optional[bool] = False):
        super().__init__(description)
        self._length = length
        self._start = start
        self.start = length if start else 0
        self.length = 0 if start else length
        # deque: pop O(1) random access O(N)
        self.deque = _Deque(self)

        self._trapped_num = 1

    @property
    def len(self):
        return len(self.deque)

    def __len__(self):
        return len(self.deque)

    def reset(self):
        self.length = 0 if self._start else self._length

    def to_start(self, env):
        self.start = self.length
        self.length = 0
        self.deque.clear()

        self._trapped_num = 1

    async def call(self, entity: Optional[Entity] = None):
        # start = self._call()
        self.length += 1
        # self._env.queue_change(self.id, self.length)

        if self._env.debug:  # and entity:
            self.deque.append(entity)

            # TODO
            if entity.first:
                entity.i = self._trapped_num
                entity.first = False
                self._trapped_num += 1

            entity.added = self._env.now
        else:
            self.deque.append(0)
            # self.deque.append([self._env.now])
        # await self._env.timeout()

        # print('at:', model.env.now, [model.command[x].length for x in model.command if isinstance(model.command[x], Queue)])
        # self._env.trace(self, start, entity)

    def clear(self):
        super().clear()
        self.start = self._length if self._start else 0
        self.length = 0 if self._start else self._length
        self.deque = _Deque(self)
        self._trapped_num = 1

    def __repr__(self):
        res = super().__repr__()
        return (
            f'<{res[1:-1]} start={self._start} set_length={self._length} '
            f'now_length={self.length} deq_length={len(self)}>'
        )

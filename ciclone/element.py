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

from .network import Network
from .entities import Entity

if TYPE_CHECKING:
    from .model import Model

"""
초기 references

https://engineering.purdue.edu/CEM/people/Personal/Halpin/Sim/index_html
"""

from .typing import *

# elemID = Union[int, str]
# simTime = Union[float, int, 'Generator']


def _unimplemented(self, *_: Any):
    raise NotImplementedError


class Deque(deque):
    def __init__(self, queue: 'Queue' = None, iterable=(), maxlen=None):
        super().__init__(iterable, maxlen)
        self._que = queue

    def _change(self):
        if self._que is not None:
            self._que\
                .model.queue_change(self._que.id, len(self._que))

    def append(self, *args, **kwargs):
        super().append(*args, **kwargs)
        self._change()

    def popleft(self, *args, **kwargs):
        get = super().popleft()
        self._change()
        return get


# TODO: element 추가
# TODO: 시간에 scalar or array_like 도 받아서 따로 결과 내줄 수 있게..?

class Element:
    _model: 'Model'
    id: elemID

    preceded: Network
    following: Network

    def __init__(self, description: str):
        # self._model: 'Model' = None
        # self.id: elemID = None
        self.desc: str = description
        self._access: int = 0

        self.preceded = Network(Element)
        self.following = Network(Element)

        self._first: simTime = -1
        self._last: simTime = -1

    @property
    def type(self):
        return self.__class__.__name__.lower()

    @property
    def model(self):
        return self._model

    def set(self, model):
        self._model = model

    def pre(self, els):
        self.preceded.add(els)

    def fol(self, els):
        self.following.add(els)

    def _call(self, num: int = 1):
        start = self._model.now
        self._access += num

        if self._access == 1:
            self._first = start
        else:
            self._last = start

        return start

    __call__: Callable[..., Any] = _unimplemented  # @abstractmethod

    @property
    def access(self) -> int:
        """A number of times an element was accessed"""
        return self._access

    def __del__(self):
        # TODO: elem 삭제되는 상황
        pass


# TODO: threading lock 등..
class Queue(Element):
    """QUEUE node:

    The idle state of an entity. Represents a queue in which entities are waiting for use."""

    def __init__(self, description: str, length: int = 0, start: Optional[bool] = False):
        super().__init__(description)
        self._test = length
        self.starting = start
        self.start = length if start else 0
        self.length = 0 if start else length
        # deque: pop O(1) random access O(N)
        self.deque = Deque(self)

        self._trapped_num = 1

    @property
    def len(self):
        return len(self.deque)

    def __len__(self):
        return len(self.deque)

    def reset(self):
        self.length = 0 if self.starting else self._test

    def to_start(self, env):
        self.start = self.length
        self.length = 0
        self.deque.clear()

        self._trapped_num = 1

    def connect(self, env):
        pass
        # self.env = env
        # if self.length > 0:
        # self.queue = simpy.Resource(env, self.length if self.length > 0 else 1)
        # self.sleep = env.event()

    def __call__(self, entity: Optional[Entity] = None):
        # https://simpy.readthedocs.io/en/4.0.1/topical_guides/process_interaction.html#sleep-until-woken-up
        start = super()._call()
        self.length += 1
        # self._model.queue_change(self.id, self.length)

        if self._model.debug and entity:
            self.deque.append(entity)

            """
            큰 문제를 불러일으킬 수 있음,,,,,?
            진짜 que인듯 하게 만들어주지만
            후반에 또 duration에 따라 달라짐
            
            생각해보니 맞는 것 같기도 하고..
            """
            if entity.first:
                entity.i = self._trapped_num
                entity.first = False
                self._trapped_num += 1

            entity.added = self._model.now
        else:
            self.deque.append([self._model.now])

        # yield self.sleep  # passivate

        # print('at:', model.env.now, [model.command[x].length for x in model.command if isinstance(model.command[x], Queue)])
        self._model.trace(self, start, entity)

        yield self._model.timeout()


class Combi(Element):
    """COMBI element:

    A constrained (in terms of its starting logic) work task; otherwise identical to a NORMAL."""

    def __init__(
        self,
        description: str,
        preceders,
        followers,
        duration: simTime
    ):
        super().__init__(description)
        self.pre(preceders)
        self.fol(followers)
        self.duration = duration
        self.path: Dict[elemID, Union[elemID, List[elemID]]] = dict()

    def __call__(self, entity: Optional[Entity] = None) -> GenReturn:
        start = super()._call()

        # entity.start = False

        if not all(v.len for v in self.preceded[Queue].values()):
            if self._model.debug:
                for k, v in self.preceded[Queue].items():
                    self._model.wait_change(k, entity, True)
                # self._model.wait_change(entity, True)
                self._model.trace(self, -1, entity)
            return -1

        result = []
        entities = {}
        real_prev = self.id

        for k in self.path.keys():
            # TODO: exception for IndexError
            entities[k] = self._model[k].deque.popleft()

        for k, v in self.preceded[Queue].items():
            v.length -= 1
            self._model.waiting_change(k, self._model.now)
            self._model.wait_change(k, entity)

        # if self._model.debug:
        #     for k, v in ppp.items():
        #         try:
        #             self._model[k].deque.remove(v[0])
        #         except ValueError:
        #             pass

        # TODO: 지금으로면 진짜 que가 아니라 먼저 점유..??? 맞는 말인 것 같기도 하구
        yield self._model.timeout(self.duration)

        if self._model.debug and entity:
            # TODO: 아주 안 좋은 임시방편...?! (for que 시작 ENtity)
            if self.path[entity.prev] == entity.prev:
                que = [x for x in self.path.keys() if x != entity.prev]
                if len(que):
                    entity = entities[que[0]]

            for k, v in self.path.items():
                one = entities[k]
                one.prev = real_prev

                if isinstance(v, list):
                    for pp in v:
                        self._model._last[one.parent][one.cnt] += 1
                        new = Entity.new_from(one)
                        new.i = self._model._last[one.parent][one.cnt]
                        new.now = pp
                        result.append(new)
                else:
                    one.now = v
                    result.append(one)

        self._model.trace(self, start, entity)

        return result


class Normal(Element):
    """NORMAL element:

    An unconstrained work task. Entities are delayed for a specified amount of time."""

    def __init__(self, description, followers, duration: simTime):
        super().__init__(description)
        self.fol(followers)
        self.duration = duration

    def __call__(self, entity: Optional[Entity] = None):
        start = super()._call()

        yield self._model.timeout(self.duration)

        self._model.trace(self, start, entity)


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

    def __call__(self, entity: Optional[Entity] = None):
        start = super()._call(self.quantity)
        yield self._model.timeout()

        self.count += self.quantity

        self._model.trace(self, start, entity)


class Func(Element):
    """Consolidate Function node"""

    def __init__(self, description, followers, con: int):
        super().__init__(description)
        self.con = con
        self._length = 0
        self.fol(followers)

    def __call__(self, entity: Optional[Entity] = None) -> GenReturn:
        start = super()._call()
        yield self._model.timeout()

        self._length += 1
        self._model.trace(self, start, self._length)

        if self._length < self.con:
            return -1
        else:
            self._model.trace(self, start, entity)
            self._length = 0

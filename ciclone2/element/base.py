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

from ..network import Network
from ..entities import Entity
# from ..core import Environment

if TYPE_CHECKING:
    from ..model import Model
    from ..core import Environment

"""
초기 references

https://engineering.purdue.edu/CEM/people/Personal/Halpin/Sim/index_html
"""

from ..typing import *


def _unimplemented(self, *_: Any):
    raise NotImplementedError


# TODO: element 추가
# TODO: 시간에 scalar or array_like 도 받아서 따로 결과 내줄 수 있게..?
class Element:
    _model: 'Model'
    _env: 'Environment'
    id: elemID

    preceded: Network
    following: Network

    def __init__(self, description: str):
        # self._model: 'Model' = None
        self.id: elemID = None  # TODO: elem id init 어떻게 할지
        self.desc: str = description
        self._access: int = 0

        self.preceded = Network(Element)
        self.following = Network(Element)

        self._first: simTime = -1
        self._last: simTime = -1

        self._start = None

    @property
    def type(self):
        return self.__class__.__name__.lower()

    @property
    def model(self):
        return self._env

    def set(self, env):
        self._env = env

    def pre(self, els):
        self.preceded.add(els)

    def fol(self, els):
        self.following.add(els)

    def _call(self, num: int = 1):
        # if self._env._end:
        #     return

        start = self._env.now
        # self._access += num

        if self._access == 0:
            self._first = start
        else:
            self._last = start

        return start

    call: FuncType = _unimplemented  # @abstractmethod

    # clear: Callable[..., Any] = _unimplemented  # @abstractmethod

    async def __call__(self, entity: Optional[Entity] = None, *args, **kwargs):
        start = self._start = self._call()
        res = await self.call(entity, *args, **kwargs)
        self._env.trace(self, start, entity)
        self._access += 1
        return res

    def __repr__(self):
        if self.id is None:
            raise RuntimeError(
                'An element is not yet attached to the environment')
        return (
            f'<{type(self).__qualname__} '
            f'"{self.id}" element on {self._env.id} environment>'
        )

    @property
    def access(self) -> int:
        """A number of times an element was accessed"""
        return self._access

    def clear(self):
        self._access = 0
        self._first = -1
        self._last = -1

    def __del__(self):
        # TODO: elem 삭제되는 상황
        #  pre, fol 연결 끊기
        pass

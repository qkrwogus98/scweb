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
from .queue import Queue
from ..entities import Entity
from ..typing import *


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

    # TODO: call로 변환
    async def __call__(self, entity: Optional[Entity] = None) -> GenReturn:
        start = self._call()

        # entity.start = False

        if not all(v.len for v in self.preceded[Queue].values()):
            if self._env.debug:
                for k, v in self.preceded[Queue].items():
                    self._env.wait_change(k, entity, True)
                # self._env.wait_change(entity, True)
                self._env.trace(self, start, entity, closed=True)
            return -1

        result = []
        entities = {}
        real_prev = self.id

        for k in self.path.keys():
            # TODO: exception for IndexError
            entities[k] = self._env.command[k].deque.popleft()

        for k, v in self.preceded[Queue].items():
            v.length -= 1
            self._env.waiting_change(k, self._env.now)
            self._env.wait_change(k, entity)

        # if self._env.debug:
        #     for k, v in ppp.items():
        #         try:
        #             self._env[k].deque.remove(v[0])
        #         except ValueError:
        #             pass

        if self._env.debug and entity:
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
                        self._env._last[one.parent][one.cnt] += 1
                        new = Entity.new_from(one)
                        new.i = self._env._last[one.parent][one.cnt]
                        new.now = pp
                        result.append(new)
                else:
                    one.now = v
                    result.append(one)

        self._env.trace(self, start, entity, arrival=True)

        # TODO: 지금으로면 진짜 que가 아니라 먼저 점유..??? 맞는 말인 것 같기도 하구
        # TODO: 지금 위 if문 뒤로 옮겼음. 나중에 다시 한번 확인!!
        await self._env.timeout(self.duration)

        self._access += 1
        self._env.trace(self, start, entity)

        return result

    def __repr__(self):
        res = super().__repr__()
        dur = f'{self.duration}' if callable(self.duration) else f'{self.duration:.3f}'
        return (
            f'<{res[1:-1]} duration={dur}>'
        )

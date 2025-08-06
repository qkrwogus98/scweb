from typing import (
    Any,
    Dict,
    Optional,
    Union,
    TYPE_CHECKING
)
if TYPE_CHECKING:
    from .model import Model
    from .core import Environment
import asyncio
from .typing import *

__all__ = ['entity', 'Entity']


async def entity(
        env: 'Environment',
        eid: elemID,
        cnt,
        i: int = 1,
        prev: elemID = None,
        start: bool = False,
        loop: asyncio.AbstractEventLoop = None
):
    """An entity function for non-debug.

    debug 모드에서는 Entity class로 반환한다.

    :param env: 환경 Environment
    :param eid: 시작 element id
    :param cnt:
    :param i:
    :param prev:
    :param start:
    :param loop:
    :return:
    """
    if env.debug:
        new = Entity(env, eid, cnt, i, prev, start)
        env.create_task(new.run())
        # r = await new.run()
        return new

    if loop is None:
        loop = env

    # print(f'{eid}에서 {cnt}가 작동')
    ret = await env.command[eid]()
    # print(ret)

    for k, v in env._stop.items():
        if env.command[k].count >= v:
            env.queue_change()

            env._end = True  # TODO: integrate env's _end and _running
            env.stop()
            return 0

    # entity 여기서 죽다..
    if ret == -1:
        return -1

    # new_process = []
    # Run next elements
    for i in env.command[eid].following:
        # print(f'{eid}->{i}')
        h = loop.create_task(
            entity(env, i, cnt)
        )
        # print(h)
        # new_process.append(h)
    # await asyncio.gather(*new_process)


class Entity:
    # _from: elemID
    # id = 1
    # i = 1
    #
    # now: elemID
    # prev: elemID = None

    """
    https://github.com/LeunPark/ciclone/tree/361bfa86db2961dff10e25a83418be2b2086a17d
    """

    def __init__(
        self,
        env: 'Environment',  # = None,
        eid: elemID,  # = None,
        cnt: int,  # = None,
        i: int = 1,
        prev: elemID = None,
        start: bool = False,
        first: bool = False,
    ):
        self._env = env
        # 현재 위치!
        self._now = self._from = eid
        self.cnt = cnt
        self.i = i
        self.prev = prev
        self.start = start

        self.first = first

        if env.verbose:
            print(f"entity 생성됨 now {self.now} cnt {self.cnt} i {self.i}")

    @property
    def now(self):
        return self._now

    @now.setter
    def now(self, p):
        if self._env.verbose:
            print(f"[{self._env.now}] Entity #{self.cnt * 1000 + self.i}의 now가 {self.now}에서 {p}로 바뀜;")
        self._now = p

    @property
    def parent(self):
        return self._from

    async def run(self, eid=None):
        if eid is None:
            eid = self.now

        if self._env.verbose:
            print(f"[{self._env.now}] Entity #{self.cnt * 1000 + self.i} (from {self.prev}) to {eid}")

        # element 실행
        ret = await self._env.command[eid](self)
        # self.start = False
        # print(f"{str}, {'will die' if ret == -1 else ''}")

        # if self._model[eid].type == 'queue':
        #     if self._model[eid].len != self._model[eid].length:
        #         print("!!!!!달라!!!!!")

        # 종료 조건인지 확인
        for k, v in self._env._stop.items():
            if self._env.command[k].count >= v:
                # print([self.command[x].length for x in self.command if isinstance(self.command[x], Queue)])
                self._env.queue_change()

                # 시뮬레이터 종료
                self._env._end = True
                self._env.stop()
                return 0

        # entity 여기서 죽다..
        if ret is not None and ret == -1:
            if self._env.verbose:
                print('Entity #%d died at %d at %f' % (self.cnt * 1000 + self.i, eid, self._env.now))
            return -1

        # 다음 element 실행
        following = self._env.command[eid].following
        if len(following) == 1:
            # following = following.one
            following = following.one[0]
            self.prev = self.now
            # self.now = following.id
            self.now = following
            if self._env.verbose:
                print(f"#{self.cnt * 1000 + self.i} {self.prev} -> {self.now}")
            self._env.create_task(
                self.run(self.now)
            )
            # self._model.env.process(self.run(self.now))
        # else:
        #     for f in following:
        #         new = Entity.new_from(self)
        #         new.prev = self.now
        #         new.now = f
        #         self._env.create_task(
        #             new.run(f)
        #         )

        elif self._env.command[eid].type == 'combi':
            # self._model.env.process(self.run())
            # print("@@@@", [(x.now, x.cnt, x.i) for x in ret])
            for x in ret:
                if self._env.verbose:
                    print(f'{eid} -> {x.now}')
                self._env.create_task(x.run())

        else:
            for i in following:
                ### Branching to new entites
                # if ent == -1:
                #     if isinstance(self.command[i], Queue):
                #         self.env.process(self.entity(i))
                # else:
                try:
                    self._env._last[self._from][self.cnt] += 1
                except:
                    print(f'_from: {self._from} / cnt: {self.cnt}')
                new = Entity(
                    self._env,
                    i,
                    self.cnt,
                    self._env._last[self._from][self.cnt],
                    self.now
                )
                self._env.trace(None, -200, (
                    self._env,
                    i,
                    self.cnt,
                    self._env._last[self._from][self.cnt],
                    self.now
                ))
                if self._env.command[i].type != 'queue':
                    self._env._processnum += 1
                # TODO: ?????? cnt,,
                new._from = self._from
                self._env._process.append(new)
                # self._env.env.process(new.run(i))
                self._env.create_task(
                    new.run(i)
                )
                # self._model._last += 1
                # break
                # yield self.env.process(self.command[i-1](self.env))

    def __repr__(self):
        return f'<{type(self).__qualname__} {self.cnt}-{self.i} at={self._now} environment={self._env.id}>'

    @classmethod
    def new_from(cls, entity) -> 'Entity':
        return cls(
            entity._env,
            entity.now,
            entity.cnt,
            entity.i,
            entity.prev,
            entity.start
        )

    def test(self):
        assert self._env, "없어욤"
        print(self._env.data[-1][1])

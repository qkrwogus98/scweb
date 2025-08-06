from typing import (
    Any,
    Dict,
    Optional,
    Union,
    TYPE_CHECKING
)
if TYPE_CHECKING:
    from .model import Model
# from .element import elemID

from .typing import *


class E:
    cnt = 0
    i = 0
    added = None


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
        model: 'Model',  # = None,
        eid: elemID,  # = None,
        cnt: int,  # = None,
        i: int = 1,
        prev: elemID = None,
        start: bool = False,
        first: bool = False
    ) -> object:
        self._model = model
        self._now = self._from = eid
        self.cnt = cnt
        self.i = i
        self.prev = prev
        self.start = start

        self.first = first

        # print(f"entity 생성됨 now {self.now} cnt {self.cnt} i {self.i}")

    @property
    def now(self):
        return self._now

    @now.setter
    def now(self, p):
        # print(f"[{self._model.now}] Entity #{self.cnt * 1000 + self.i}의 now가 {self.now}에서 {p}로 바뀜;")
        self._now = p

    @property
    def parent(self):
        return self._from

    def run(self, eid=None) -> GenReturn:
        # for x in self._model._kill:
        #     for y in range(len(self._model._process)):
        #         if x == id(self._model._process[y]):
        #             # print(len(self._model._process))
        #             # print("gotcha!!!!~~~~")
        #             del self._model._process[y]
        #             # print(len(self._model._process))
        #             self._model._kill.remove(x)
        #             break

        if eid is None:
            eid = self.now

        # str = f"[{self._model.now}] Entity #{self.cnt * 1000 + self.i} (from {self.prev}) to {eid}"

        # element 실행
        ret = yield self._model.env.process(self._model[eid](self))
        # self.start = False
        # print(f"{str}, {'will die' if ret == -1 else ''}")

        # if self._model[eid].type == 'queue':
        #     if self._model[eid].len != self._model[eid].length:
        #         print("!!!!!달라!!!!!")

        # 종료 조건인지 확인
        for k, v in self._model._stop.items():
            if self._model[k].count >= v:
                # print([self.command[x].length for x in self.command if isinstance(self.command[x], Queue)])
                self._model.queue_change()

                # 시뮬레이터 종료
                self._model._end = True
                # 나중에~ run 할 때 event들 붙여주기..
                self._model.env.event().succeed()
                return 0

        if ret is not None:
            # entity 여기서 죽다..
            if ret == -1:
                # self._model._kill.append(id(self))
                self._model._processnum -= 1
                # print('Entity #%d died at %d at %f' % (yy, eid, self.env.now))
                # self._model._last -= 1
                return -1

        # 다음 element 실행
        following = self._model[eid].following
        if len(following) == 1:
            following = following.one
            self.prev = self.now
            self.now = following[0]
            # print(f'{eid}->{self.now}')
            # print(f"#{self.cnt * 1000 + self.i} {self.prev} -> {self.now}")
            self._model.env.process(self.run(self.now))

        elif self._model[eid].type == 'combi':
            # self._model.env.process(self.run())
            # print("@@@@", [(x.now, x.cnt, x.i) for x in ret])
            for x in ret:
                # print(f'{eid}->{x.now}')
                self._model.env.process(x.run())

        else:
            for i in following:
                """
                Branching to new entites
                """
                # if ent == -1:
                #     if isinstance(self.command[i], Queue):
                #         self.env.process(self.entity(i))
                # else:
                self._model._last[self._from][self.cnt] += 1
                new = Entity(
                    self._model,
                    i,
                    self.cnt,
                    self._model._last[self._from][self.cnt],
                    self.now
                )
                self._model.trace(None, -200, (
                    self._model,
                    i,
                    self.cnt,
                    self._model._last[self._from][self.cnt],
                    self.now
                ))
                if self._model[i].type != 'queue':
                    self._model._processnum += 1
                # TODO: ?????? cnt,,
                new._from = self._from
                self._model._process.append(new)
                self._model.env.process(new.run(i))
                # self._model._last += 1
                # break
                # yield self.env.process(self.command[i-1](self.env))

    @classmethod
    def new_from(cls, entity) -> 'Entity':
        return cls(
            entity._model,
            entity.now,
            entity.cnt,
            entity.i,
            entity.prev,
            entity.start
        )

    def test(self):
        assert self._model, "없어욤"
        print(self._model.data[-1][1])

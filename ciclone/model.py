import time as tm
import warnings
from typing import (
    overload,
    Tuple,
    List,
    Type,
    Dict,
    Optional,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    pass
from .core import Environment
from .element import *
# from .element import Element, Queue, Combi, Count, Network, Func
from .stats import Statistics
from .entities import Entity

from .typing import *
# Infinity = float('inf')

"""
    비동기로 바꾸기..?!!!!!
    귀찮,, 어렵,, 귀찮,,
"""


class Model:
    """Execution model for a CICLONE model simulation.
    The passing of time is simulated by stepping from element to element."""

    command: Network

    def __init__(self, socket: Optional[F] = None):
        self.debug = True
        self._socket = socket

        # self.command: Dict[elemID, Element] = {}
        self.command = Network(Element)
        self._copy = {}

        self.stats = Statistics(self)
        self.env = Environment()
        self._time: float = -1.

        self._until: simTime = 0
        self._stop: Dict[elemID, int] = dict()
        self._end: bool = False

        self._run: int = 0

        self.data = []
        self.passive = {}
        self.waiting = {}
        self._wait = {}

        self._process = []
        self._last = {}
        self._processnum = 0

        self._last_queue = 0

        self._trace = []

    def add(self, command: Dict[elemID, Element], internal=False):
        """Link elements to a model and check the integrity"""
        # TODO: check the integrity (at run part?)

        if not internal:
            self._copy = command

        # self.command = command
        self.command.all = command

        self._last_queue = 0
        for k, v in command.items():
            v.id = k
            v.set(self)

            # Combi
            if isinstance(v, Combi):
                for f in v.following:
                    command[f].pre(k)
                for p in v.preceded:
                    command[p].fol(k)
            # Queue
            elif isinstance(v, Queue):
                v.connect(self.env)
                if not v.start and v.length == 0:
                    self.queue_change(v.id, 0)
                self._last[k] = {}
                for j in range(v.length):
                    new = Entity(self, k, self._last_queue + 1, j + 1, start=True, first=True)
                    # print(k, self._last_queue + 1, j + 1)
                    new.added = Infinity
                    v.deque.append(new)
                if v.length:
                    self._last_queue += 1
                self._last[k][1] = len(v.deque)
                # print("!!!!!!", k, len(v.deque), self._last)

            # Normal, Counter, Function, etc.
            else:
                for f in v.following:
                    command[f].pre(k)

        for k, v in command.items():
            for f in v.following:
                command[f].preceded.add(k, command[k])
            for p in v.preceded:
                command[p].following.add(k, command[k])

        for com in self[Combi].values():
            pre = com.preceded.all
            fol = com.following.all

            for k, v in fol.items():
                if k in pre:
                    # 앞 :(->) 뒤
                    com.path[k] = k
                else:
                    search = self.search(k, pre.keys())
                    if len(search):
                        # TODO: find 2개가 될 수도 있는지 확인해야 함
                        com.path[search[0][1]] = k
                    # else:
                    #     com.path[k] = None

            not_in = [x for x in fol.keys() if x not in com.path.values()]
            # TODO: 지금은 combi 앞에 que만 올 수 있다지만 확장시키면 어떻게 될 지 모름,,
            for k, v in pre.items():
                if k not in com.path:
                    if len(not_in) == 1:
                        not_in = not_in[0]
                    com.path[k] = not_in
            # print(com.path)

    def entity(
        self,
        eid: elemID,
        cnt,
        i: int = 1,
        prev: elemID = None,
        start: bool = False
    ) -> GenReturn:
        """An entity function for non-debug.

        debug 모드에서는 Entity class로 반환한다."""

        if self.debug:
            new = Entity(self, eid, cnt, i, prev, start)
            self._process.append(new)
            return self.env.process(new.run())

        """ Like DFS """

        # element 실행
        ret = yield self.env.process(self[eid]())
        # Element __call__ = Generator

        # 종료 조건인지 확인 For Count elements
        for k, v in self._stop.items():
            if self[k].count >= v:
                self.queue_change()

                # 시뮬레이션 종료
                self._end = True
                # 나중에~ run 할 때 event들 붙여주기..
                self.env.event().succeed()
                return 0

        # entity 여기서 죽다..
        if ret == -1:
            return -1

        # 다음 element 실행
        for i in self[eid].following:
            self.env.process(self.entity(i, cnt))

    def watcher(self):
        while True:
            print('at:', self.env.now,
                  [self[x].length for x in self.command if isinstance(self[x], Queue)])
            yield self.env.timeout(1)
            if self._end:
                return

    @property
    def now(self) -> simTime:
        """The current simulation time"""
        return self.env.now

    def timeout(self, delay: simTime = 0):
        if callable(delay):
            delay = delay()
        return self.env.timeout(delay)

    @property
    def time(self) -> float:
        """The execution time in millisecond"""
        assert self._time != -1., "task has not yet run"
        return self._time

    def clear(self):
        # TODO: clear 수정

        self._end = False
        self._processnum = 0
        self._process.clear()
        self._last.clear()

        self.data.clear()
        self.passive.clear()
        self.waiting.clear()

        del self.env
        self.env = Environment()

        for k, v in self.command.items():
            if isinstance(v, Count):
                v.count = 0
            # elif isinstance(v, Combi):
            #     v._queue = deque()
            #     v._waiting.clear()
            elif isinstance(v, Queue):
                v.deque.clear()
                v.reset()
            elif isinstance(v, Func):
                v._length = 0

            v._access = 0

        # TODO: 바꿔;
        self.add(self._copy, True)

    def run(
        self,
        num: int = 1
    ) -> bool:
        if num > 1:
            self.run(num - 1)

        # 초기화
        # if self._time != -1.:
        if self._run > 0:
            # print("첫 번째가 아님")
            self.clear()

        i = max(self._last_queue + 10, 20)

        # starting QUE에 있는 entity들 process 시작
        for k, v in self[Queue].items():
            if k not in self._last:
                self._last[k] = {}

            # if v.start:
            for _ in range(v.start):
                self._last[k][i] = 1
                self._processnum += 1
                self.env.process(self.entity(k, i, start=True))
                # self._process.append(self.env.process(self.entity(k, i, -1, True)))
                i += 1

        # FUNC 뒤에 있는 entity들 process 시작
        for x in self[Func].values():
            """
            FORMAL: Any unit from any FUNC preceding activates the function
            which automatically activates all elements following it.
    
            그래서 일단 fol이 QUE면 length 있는 건 starting point로 바꾸고
            length 0이면 놔둠. 나머진 그냥 등록.
            """
            if len(x.preceded):
                for k, v in x.following.all.items():
                    self._last[k] = {}

                    if isinstance(v, Queue):
                        if v.start or v.length == 0:
                            continue
                        else:
                            v.to_start(self.env)
                            # deque 만들

                            for _ in range(v.start):
                                self._last[k][i] = 1
                                self._processnum += 1
                                self.env.process(self.entity(k, i, start=True))

                                # self._process.append(self.env.process(self.entity(k, i, -1, True)))
                                i += 1
                            # [self.env.process(self.entity(self.command[z].id)) for _ in range(self.command[z].start)]
                    else:
                        self._last[k] = {i: 1}
                        self._processnum += 1
                        self.env.process(self.entity(k, i, start=True))
                        # self._process.append(self.env.process(self.entity(k, i, -1, True)))
                        i += 1
        # self.env.process(self.watcher())

        # TODO: 멀티 프로세서 구현
        self._run += 1

        self.queue_change()
        if self._socket is not None:
            self._socket({
                'type': 'system',
                'status': 'start',
                'count': list(self._stop.values())[0]
            })
        self._trace.append({
            'type': 'system',
            'status': 'start',
            'count': list(self._stop.values())[0]
        })
        start = tm.time()
        # try except
        if self._until:
            self.env.run(until=self._until)
            self._end = True
        else:
            self.env.run()
        self._time = (tm.time() - start) / 2
        if self._socket is not None:
            self._socket({
                'type': 'system',
                'status': 'close',
                'time': self._time
            })
        self._trace.append({
            'type': 'system',
            'status': 'close',
            'time': self._time
        })


        # TODO: 할 때마다 stats 계산..? (임시방편)
        self.stats.test[self._run] = {
            'prod': self.stats.prod(),
            'active': self.stats.active(),
            'passive': self.stats.passive(),
            'counter': self.stats.counter()
        }
        # self.stats.data[self._run] = {
        #     'data': self.data,
        #     'passive': self.passive,
        #     'waiting': self.waiting
        # }

        # print('Elapsed time:', self._time)
        return True

    def until(self, **kwargs) -> None:
        """Set a condition of termination. 파라미터 다음같다.

        Parameters
        ----------
        :key time: 정해진 시간abc만큼
        :key Count[id]: id의 카운트값이 지정된 값까지

        Raise a :exc:`TypeError` if """
        for k, v in kwargs.items():
            key = k.lower()

            if key == 'time':
                self._until = v
            elif key.startswith('count'):
                name = k[5:]

                if int(name) in self.command:
                    name = int(name)
                elif name not in self.command:
                    warnings.warn(f"The element {name} is undefined", Warning)

                if name in self.command and self[name].type != 'count':
                    raise TypeError(
                        f"The element {name} is not a count, "
                        f"{self[name].type} given"
                    )

                self._stop[name] = v
            else:
                raise TypeError(f"{k}: not supported argument")

    # @functools.lru_cache(maxsize=128)
    def _search(self, start, find, n=1, cache={}):
        # TODO: bfs로 바꾸고 최대 깊이 제한하려고 했으나 구성 달라져 상관없을듯
        # TODO: 어쩄든 나중에 최적화하기
        for k in self.command[start].following:
            if start not in cache:
                cache[start] = {}

            if k in find:
                cache[start][k] = n
                continue

            if k in cache[start] and not cache[start][k]:
                continue

            cache[start][k] = False

            self._search(k, find, n + 1, cache)

        return cache

    def search(
        self,
        start: elemID,
        find: Optional[List[elemID]] = None
    ):
        if find is None:
            find = self[start].preceded.all.keys()

        search = self._search(start, find, cache={})

        result = []
        for v in search.values():
            for k2, v2 in v.items():
                if v2:
                    result.append((v2, k2))

        result.sort(key=lambda s: s[0])
        return result

    def trace(self, element: Element, start, i=-1):
        if self._end:
            return

        if element is None:
            self.data.append([start, self.env.now, '', '', '', str(i)])
        else:
            if isinstance(i, Entity):
                i = i.cnt * 1000 + i.i

            self.data.append([start, self.env.now, element.id, element.type, element.desc, i])

        self._trace.append({
            'type': 'trace',
            'start': start,
            'end': self.env.now,
            'current': element.id,
            'current_type': element.type,
            'current_desc': element.desc,
            'entity': i,
        })

        if self._socket is not None:
            # self._socket(self.data[-1])
            self._socket({
                'type': 'trace',
                'start': start,
                'end': self.env.now,
                'current': element.id,
                'current_type': element.type,
                'current_desc': element.desc,
                'entity': i,
            })

    def queue_change(
        self,
        eid: elemID = None,
        val: int = None
    ):
        if self._end:
            return

        if (eid and val) is not None:
            if eid not in self.passive:
                self.passive[eid] = []
            self.passive[eid].append([self.env.now, val])
            if self._socket is not None:
                self._socket({
                    'type': 'queue',
                    'id': eid,
                    'desc': self[eid].desc,
                    'now': self.env.now,
                    'val': val
                })
            self._trace.append({
                'type': 'queue',
                'id': eid,
                'desc': self[eid].desc,
                'now': self.env.now,
                'val': val
            })
        # self.passive[self.env.now] = [self.command[x].length for x in self.command if
        #                               isinstance(self.command[x], Queue)]
        # TODO: ??? 왜 이렇게 했지... ??
        else:
            for k, v in self[Queue].items():
                if k not in self.passive: self.passive[k] = []
                self.passive[k].append([self.env.now, v.length])
                if self._socket is not None:
                    self._socket({
                        'type': 'queue',
                        'id': k,
                        'desc': v.desc,
                        'now': self.env.now,
                        'val': v.length
                    })
                self._trace.append({
                    'type': 'queue',
                    'id': k,
                    'desc': v.desc,
                    'now': self.env.now,
                    'val': v.length
                })

    def waiting_change(self, eid=None, val=None):
        if self._end:
            return

        if (eid and val) is not None:
            if eid not in self.waiting: self.waiting[eid] = []
            self.waiting[eid].append(val)

    def wait_change(self, que, entity, start=False):
        if self._end or entity is None:
            return

        i = entity.cnt * 1000 + entity.i


        if que not in self._wait:
            self._wait[que] = []

        if start:
            self._wait[que].append([i, self.now, None])
        else:
            let = False
            # let = [x for x in self._wait[eid][::-1] if x[0] == i]
            for x in self._wait[que][::-1]:
                if x[0] == i:
                    x[2] = self.now
                    let = True
                    break

            # if not let:

            # self._wait[eid]

    # TODO: Network로 통합하기

    @overload  # TODO: 여기도 typing?
    def __getitem__(self, key: Union[Tuple, List]) -> Dict[elemID, elemCls]: ...
    @overload
    def __getitem__(self, key: Type[elemOf]) -> Dict[elemID, elemOf]: ...
    @overload
    def __getitem__(self, key: elemID) -> elemCls: ...

    def __getitem__(self, key):
        return self.command.get(key)

    def __len__(self) -> int:
        return len(self.command)

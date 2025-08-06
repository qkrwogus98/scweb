import concurrent.futures
import copy
import time as tm
import warnings
from functools import partial
from pprint import pprint
from typing import (
    overload,
    Tuple,
    List,
    Type,
    Dict,
    Union,
    Optional,
    TYPE_CHECKING
)
import asyncio
import janus
import warnings

if TYPE_CHECKING:
    pass
# from ._core import Environment
from .core import Environment
from .element import *
# from .element import Element, Queue, Combi, Count, Network, Func
from .stats import Statistics
from .entities import Entity, entity
from .network import Network

from .typing import *


class Model:
    """Execution model for a CICLONE model simulation.
    The passing of time is simulated by stepping from element to element."""

    command: Network

    def __init__(self, *, max_envs: int = 5):
        self._debug = True

        # self.command: Dict[elemID, Element] = {}
        self.command = Network(Element)
        self._copy = {}

        # self.stats = Statistics(self)
        self.stats = list()
        self.max_envs = max_envs
        self.envs = [Environment(self, self.debug) for _ in range(self.max_envs)]
        self._time: float = -1.

        self._until: Optional[simTime] = None
        self._stop: Dict[elemID, int] = dict()
        self._end: bool = False

        self._run: int = 0
        self._with_yield = False

        self.data = []
        self.passive = {}
        self.waiting = {}
        self._wait = {}

        self._process = []
        self._last = {}
        self._processnum = 0

        self._process_num = 0

        self._last_queue = 0
        # self._kill = []

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        self._debug = value
        for env in self.envs:
            env.debug = value

    def _add(self, dst, src, env):
        dst.all = copy.deepcopy(src)

        env._last_queue = 0
        for k, v in dst.items():
            v.id = k
            v.set(env)

            # Combi
            if isinstance(v, Combi):
                for f in v.following:
                    dst[f].pre(k)
                for p in v.preceded:
                    dst[p].fol(k)
            # Queue
            elif isinstance(v, Queue):
                # v.connect(env)
                if not v._start and v.length == 0:
                    env.queue_change(v.id, 0)
                env._last[k] = {}
                for j in range(v.length):
                    new = Entity(env, k, env._last_queue + 1, j + 1, start=True, first=True)
                    # print(k, self._last_queue + 1, j + 1)
                    new.added = Infinity
                    v.deque.append(new)
                    env._last[k][j+1] = 1
                if v.length:
                    env._last_queue += 1
                # env._last[k][1] = len(v.deque)
                # print("!!!!!!", k, len(v.deque), self._last)

            # Normal, Counter, Function, etc.
            else:
                for f in v.following:
                    dst[f].pre(k)

        for k, v in dst.items():
            for f in v.following:
                dst[f].preceded.add(k, dst[k])
            for p in v.preceded:
                dst[p].following.add(k, dst[k])

        for com in dst[Combi].values():
            pre = com.preceded.all
            fol = com.following.all

            for k, v in fol.items():
                if k in pre:
                    # 앞 :(->) 뒤
                    com.path[k] = k
                else:
                    search = dst.search(k, pre.keys())
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
                        com.path[k] = not_in[0]
                    else:
                        com.path[k] = not_in
                    # if len(not_in) == 1:
                    #     not_in = not_in[0]
                    # com.path[k] = not_in
            # print(com.path)

    def add(self, command: Dict[elemID, Element], internal=False):
        """Link elements to a model and check the integrity"""
        # TODO: check the integrity (at run part?)

        if not internal:
            self._copy = command

        for e in self.envs:
            self._add(e.command, command, e)

        self.command = self.envs[0].command
        # self.env2.command.all = copy.deepcopy(command)

    def watcher(self):
        while True:
            print('at:', self.envs[0].now,
                  [self[x].length for x in self.command if isinstance(self[x], Queue)])
            yield self.envs[0].timeout(1)
            if self._end:
                return

    @property
    def time(self) -> float:
        """The execution time in millisecond"""
        assert self._time != -1., "task has not yet run"
        return self._time

    @property
    def elapsed_time(self) -> float:
        """The execution time in millisecond"""
        assert self._time != -1., "task has not yet run"
        return self._time

    def run(
        self,
        num: int = 1,
        verbose=False
    ) -> None:
        # loop = self.env
        # asyncio.set_event_loop(loop)

        for i, env in enumerate(self.envs):
            # create entities only in 'num' environments
            if i + 1 > num:
                break

            env.verbose = verbose
            env.init()

        def _on_env_done(env: Environment, reset=False, fut=None):
            stat = Statistics(env)
            self.stats.append(stat.summary())
            if reset:
                env.reset()

        self._run += 1

        if num == 1:
            start = tm.time()
            self.envs[0].run_forever(until=self._until)
            self._time = tm.time() - start
            _on_env_done(self.envs[0])
            return

        # TODO: ``asyncio.Event``

        with concurrent.futures.ThreadPoolExecutor() as executor:  # max_workers=4
            start = tm.time()
            if num <= len(self.envs):
                for i in range(num):
                    # await loop.run_in_executor(exector,
                    fut = executor.submit(self.envs[i].run_forever, until=self._until)
                    fut.add_done_callback(partial(_on_env_done, self.envs[i], False))
            else:
                while num > 0:
                    for env in self.envs:
                        num -= 1
                        a = num <= 0  # Terminate cond.
                        b = num < self.max_envs  # Continue cond.

                        fut = executor.submit(env.run_forever, until=self._until)
                        fut.add_done_callback(partial(_on_env_done, env, not (a or b)))
                        if a: break
                        if b: continue

        self._time = tm.time() - start

    def simulate2(
            self,
            num=1,
            fn: F = None,
            verbose=False
    ) -> None:
        if num != 1:
            raise RuntimeError('simulate2 now only supports num=1')

        for i, env in enumerate(self.envs):
            # create entities only in 'num' environments
            if i + 1 > num:
                break

            env.verbose = verbose
            env.init()

        self._run += 1

        _env = self.envs[0]

        start = tm.time()
        _env.run_forever(until=self._until, fn=fn)
        self._time = tm.time() - start

        stat = Statistics(_env)
        # self.stats.append(stat.summary())

    def change_duration(self, elem_id: elemID, duration: simTime):
        self.command[elem_id].duration = duration
        for env in self.envs:
            env.command[elem_id].duration = duration

    def simulate(
            self,
            num: int = 1,
            fn: F = None,
            with_yield=False,
            verbose=False
    ) -> None:
        _changed = False
        # assert num <= len(self.envs), 'In simulate, num must be less than the number of environments'
        # assert callable(fn), 'A callable function fn must be given'
        if num > len(self.envs):
            raise ValueError(f"In simulate, 'num' must be less than {len(self.envs)}, the number of environments")
        if not callable(fn):
            raise TypeError("A callable function 'fn' must be given")
        if not self.debug:
            raise RuntimeError('simulate only works in debug mode')
            # warnings.warn('simulate only works in debug mode', Warning)
            # self.debug = _changed = True

        for i, env in enumerate(self.envs):
            # create entities only in 'num' environments
            if i + 1 > num:
                break

            env.verbose = verbose
            env.init()

        self._run += 1

        class _Simulate:
            def __init__(self, async_q, futs, model):
                self._async_q = async_q
                self._futs = futs
                self._model = model

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self._model.numnum > 0:
                    val = await self._async_q.get()
                    if type(val) is dict and val['_id'] == 'all' and val['closed']:
                        raise StopAsyncIteration
                    self._async_q.task_done()
                    return val

        def logger_f(val, futs):
            print(sum(fut.running() for fut in futs), futs)
            print(val, not all(fut.done() for fut in futs))

        async def logger(async_q, futs):
            while self._process_num > 0:
                val = await async_q.get()
                close = False
                if type(val) is dict and val['_type'] == 'system' and val['closed']:
                    close = True
                # logger_f(val, futs)
                if asyncio.iscoroutinefunction(fn):
                    await fn(val)
                else:
                    fn(val)
                if close:
                    break
                async_q.task_done()

        self._process_num = num

        async def run_with_queue(num=num):
            queue = janus.Queue()
            executor = concurrent.futures.ThreadPoolExecutor()
            futs = set()

            def _on_env_done(env: Environment, fut):
                self._process_num -= 1
                stat = Statistics(env)
                self.stats.append(stat.summary())
                # All work done
                if all(fut.done() for fut in futs):
                    queue.sync_q.put({
                        '_type': 'system',
                        'closed': True,
                        'time': tm.time() - start
                    })

            for i in range(num):
                f = executor.submit(self.envs[i].run_forever, sync_q=queue.sync_q)
                f.add_done_callback(partial(_on_env_done, self.envs[i]))
                futs.add(f)

            await logger(queue.async_q, futs)

            queue.close()
            await queue.wait_closed()
            executor.shutdown()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        start = tm.time()

        if loop and loop.is_running():
            loop.create_task(run_with_queue())
        else:
            asyncio.run(run_with_queue())

        self._time = tm.time() - start

        if _changed:
            self.debug = False

    def until(self, **kwargs) -> None:
        """Set a condition of termination. 파라미터 다음같다.

        Parameters
        ----------
        :key time: 정해진 시간만큼
        :key Count[id]: id의 카운트값이 지정된 값까지

        Raise a :exc:`TypeError` if given element is not a count"""
        for k, v in kwargs.items():
            key = k.lower()

            if key == 'time':
                assert isinstance(v, simTime)
                self._until = v
                for e in self.envs:
                    e._until = v
            elif key.startswith('count'):
                name = k[5:]

                if int(name) in self.command:
                    name = int(name)
                elif name not in self.command:
                    warnings.warn(f"The element {name} is undefined", Warning)

                if name in self.command and self.command[name].type != 'count':
                    raise TypeError(
                        f"The element {name} is not a count, "
                        f"{self.command[name].type} given"
                    )

                self._stop[name] = v
                for e in self.envs:
                    e._stop[name] = v
            else:
                raise TypeError(f"{k}: not supported argument")

    # TODO: Network로 통합하기

    @overload
    def __getitem__(self, key: Union[Tuple, List]) -> Dict[elemID, elemCls]: ...
    @overload
    def __getitem__(self, key: Type[elemOf]) -> Dict[elemID, elemOf]: ...
    @overload
    def __getitem__(self, key: elemID) -> elemCls: ...

    def __getitem__(self, key):
        return self.command.get(key)

    def __len__(self) -> int:
        return len(self.command)

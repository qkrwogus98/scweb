import threading
import types
from abc import ABC
from typing import (
    Any,
    Optional,
    Coroutine,
    TYPE_CHECKING,
    List
)

from .element import Element, Queue, Func
from .entities import Entity, entity
from .network import Network
from .typing import *

import heapq

import asyncio
from asyncio import events, futures

from functools import wraps
from itertools import count
from collections import deque


class Environment(asyncio.AbstractEventLoop, ABC):
    """
    The simulator environment of async loop of the CICLONE models
    for the event-driven async/await coroutines
    """
    _ids = count(1)

    def __init__(self, model, debug):
        # self.name = name
        self.id = next(self._ids)
        self.name = self.id
        self._model = model
        self.debug = debug
        self.verbose = False

        self._time = 0
        self._thread_id = None
        self._loop_debug = False
        self._running = False
        self._immediate = deque()
        self._scheduled: List[asyncio.TimerHandle] = []
        self._exc = None
        self._temp = []

        self.command = Network(Element)

        self._until: simTime = 0
        self._stop = dict()
        self._end: bool = False

        self._run: int = 0

        self.data = []
        self._test = []
        self.passive = {}
        self.queues = []
        self.waiting = {}
        self._wait = {}

        # TODO: handle these
        self._process = []
        self._last = {}
        '''
        {Queue: {entities...: 1}}
        '''
        self._processnum = 0
        self._process_num = 0
        self._last_queue = 0

        self.fn = None

        self.sync_q = None

    def __repr__(self):
        return (
            f'<{self.__class__.__name__} {self.id} running={self.is_running()}>'
        )

    def create_future(self):
        return asyncio.Future(loop=self)

    def create_task(self, coro, *, name=None):
        # noinspection PyTypeChecker
        @wraps(coro)
        async def wrapper():
            try:
                res = await coro
                self._temp.append(res)
            except Exception as e:
                print("Wrapped exception:", e)
                self._exc = e

        return asyncio.Task(wrapper(), loop=self)

    # TODO: need to handle close
    # noinspection PyProtectedMember
    def run_forever(self, *, sync_q=None, verbose: bool = None, until: simTime = None, fn=None):
        self.sync_q = sync_q
        self.fn = fn
        if verbose is not None:
            self.verbose = verbose
        if until is not None:
            # Event 향상
            def end_event():
                self._end = True
                self.stop()
            self.call_at(until, end_event)
        self._running = True
        try:
            events._set_running_loop(self)
            self._thread_id = threading.get_ident()
            if self.verbose:
                print(f'#{self.name} THREADING IDENTIFICATION {self._thread_id}')
            while self._running and (self._immediate or self._scheduled):
                if self._immediate:
                    h = self._immediate.popleft()
                else:
                    h = heapq.heappop(self._scheduled)
                    self._time = h.when()
                    h._scheduled = False
                if not h.cancelled():
                    h._run()
                if self._exc is not None:
                    raise self._exc
        finally:
            self._running = False
            events._set_running_loop(None)

    def run_until_complete(self, future):
        raise NotImplementedError

    def stop(self):
        self._running = False

    def close(self):
        if self.is_running():
            raise RuntimeError('Cannot close a running event loop')

    def is_running(self):
        return self._running

    def is_closed(self):
        return not self._running

    def _timer_handle_cancelled(self, handle):
        # TODO
        pass

    async def shutdown_asyncgens(self):
        pass

    def call_exception_handler(self, context):
        self._exc = context.get('exception', None)

    # TODO:
    def schedule(
            self,
            callback: Coroutine,
            delay: simTime = None,
            at: simTime = None,
    ):
        if delay and delay < 0:
            raise Exception

    def call_soon(self, callback, *args, **kwargs):
        h = asyncio.Handle(callback, args, self)
        self._immediate.append(h)
        return h

    def call_later(self, delay, callback, *args):
        if delay < 0:
            raise ValueError("Cannot schedule in the past")
        return self.call_at(self.time() + delay, callback, *args)

    def call_at(self, when, callback, *args):
        if when < self.time():
            raise ValueError("Cannot schedule in the past")
        h = asyncio.TimerHandle(when, callback, args, self)
        heapq.heappush(self._scheduled, h)
        h._scheduled = True
        return h

    def time(self):
        return self._time

    @property
    def now(self):
        return self._time

    async def timeout(
            self,
            delay: simTime = 0,
            result=None
    ):
        """Coroutine that completes after a given time.

        from asyncio.sleep"""

        if callable(delay):
            delay = delay()

        return await asyncio.sleep(delay, result)

        if delay <= 0:
            await _sleep0()
            return result

        future = self.create_future()
        h = self.call_later(delay,
                            futures._set_result_unless_cancelled,
                            future, result)
        try:
            return await future
        finally:
            h.cancel()

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
            self.passive[eid].append([self.now, val])

            if self.fn is not None:
                self.fn({'_type': 'queue', 'id': eid, 'now': self.now, 'val': val, 'env': self.id})
            if self.sync_q is not None:
                self.sync_q.put({'_type': 'queue', 'id': eid, 'now': self.now, 'val': val, 'env': self.id})

            self.queues.append({'id': eid, 'now': self.now, 'val': val, 'env': self.id})

        # self.passive[self.now] = [self.command[x].length for x in self.command if
        #                               isinstance(self.command[x], Queue)]
        # TODO: ??? 왜 이렇게 했지... ??
        else:
            for k, v in self.command[Queue].items():
                if k not in self.passive: self.passive[k] = []
                self.passive[k].append([self.now, v.length])
                if self.fn is not None:
                    self.fn({'_type': 'queue', 'id': k, 'now': self.now, 'val': v.length, 'env': self.id})
                if self.sync_q is not None:
                    self.sync_q.put({'_type': 'queue', 'id': k, 'now': self.now, 'val': v.length, 'env': self.id})

                # self.queues.append({'id': k, 'now': self.now, 'val': v.length, 'env': self.id})

        if self.sync_q is not None:
            self.sync_q.join()

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

    def trace(self, element: Element, start, entity: Entity = None, closed=False, arrival=False):
        if self._end:
            return

        if element is None:
            self._test.append([start, self.now, '', '', '', str(entity)])
            return

        d = {
            'start': start,
            'end': None if arrival else self.now,
            'current': element.id,
            'current_type': element.type,
            'current_desc': element.desc,
            'cnt': entity.cnt,
            'i': entity.i,
            'closed': closed,
            'arrival': arrival
        }

        if isinstance(entity, Entity):
            i = entity.cnt * 1000 + entity.i
        self._test.append([start, self.now, element.id, element.type, element.desc, i])

        if self.fn is not None:
            self.fn({'_type': 'trace', **d, 'env': self.id})
        if self.sync_q is not None:
            self.sync_q.put({'_type': 'trace', **d, 'env': self.id})
            self.sync_q.join()

        self.data.append(d)
        # print(self.data[-1])

    def init(self):
        # Insert starting entities into starting Queue
        i = max(self._last_queue + 10, 20)
        for k, v in self.command[Queue].items():
            for _ in range(v.start):
                self._last[k][i] = 1
                self.create_task(entity(self, k, i, start=True))
                i += 1

        # Insert starting entities into Queue after Func
        # TODO: 다시 한번 확인!!!
        for x in self.command[Func].values():
            """
            FORMAL: Any unit from any FUNC preceding activates the function
            which automatically activates all elements following it.

            그래서 일단 fol이 QUE면 length 있는 건 starting point로 바꾸고
            length 0이면 놔둠. 나머진 그냥 등록.
            """
            if len(x.preceded):
                for k, v in x.following.items():
                    self._last[k] = {}

                    if isinstance(v, Queue):
                        if v.start or v.length == 0:
                            continue
                        else:
                            v.to_start(self)
                            # deque 만들

                            for _ in range(v.start):
                                self._last[k][i] = 1
                                # env._processnum += 1
                                self.create_task(entity(self, k, i, start=True))
                                i += 1
                    else:
                        self._last[k] = {i: 1}
                        # env._processnum += 1
                        self.create_task(entity(self, k, i, start=True))
                        i += 1

        self._last_queue = i

    def reset(self):
        for elem in self.command.values():
            elem.clear()

        self._time = 0
        self._thread_id = None
        self._running = False
        self._immediate.clear()
        self._scheduled.clear()
        self._exc = None
        self._temp.clear()

        self._end: bool = False

        self._run: int = 0

        self.data.clear()
        self.passive.clear()
        self.waiting.clear()
        self._wait.clear()

        self._last_queue = 0
        for k, v in self.command[Queue].items():
            if not v._start and v.length == 0:
                self.queue_change(v.id, 0)
            # self._last[k] = {}
            for j in range(v.length):
                new = Entity(self, k, self._last_queue + 1, j + 1, start=True, first=True)
                new.added = Infinity
                v.deque.append(new)
            if v.length:
                self._last_queue += 1
            self._last[k][1] = len(v.deque)

        self.init()


    # Debug flag management of EventLoop

    def get_debug(self) -> bool:
        return self._loop_debug

    def set_debug(self, enabled: bool = True):
        self._loop_debug = enabled


import numpy as np
from typing import (
    List,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from .core import Environment
    from .model import Model

from .element import Queue, Combi, Normal, Count

# TODO: 쓰레기 덩어리..

class Statistics:
    def __init__(self, env):
        self._env: Environment = env

        self.data = {}
        self.test = {}

        self._prod = []
        self._active = []
        self._passive = []
        self._counter = []

    def prod(self, data=None, save=True):
        """
        productivity information

        :param data:
        :param save:
        :return:
        """
        if data is None:
            data = self._env.data # simulation data load

        prod = [] # productivity data save
        # Departure time, Arrival time
        p, q = [], [] # loading(starting) time and arrival time list

        starting: Queue

        # Finding start point (Queue)
        for k, v in self._env.command[Queue].items():
            if v._start:
                starting = v
                break

        for x in data:
            if not x['closed'] and x['current'] == starting.id:
                p.append(x['start']) # dump 출발 시간 저장
            elif x['current_type'] == 'count':
                q.append(x['start']) # dump 도착 시간 저장

        for i in range(min(len(p), len(q))):
            prod.append({
                'no': i+1,
                'departure_time': p[i],
                'arrival_time': q[i],
                'productivity': 1 / (q[i] - p[i]) # 생산성 계산 단위
            })

        if save:
            self._prod = prod

        return prod

    def active(self, data=None, save=True):
        """
        active element 정보

        :param data:
        :param save:
        :return:
        """
        if data is None:
            data = self._env.data

        active = []
        # active.append([0, 'SCENE', 'Scenario', 1, 0, 0, data[-1][1], 0, 0, 0])

        for k, v in self._env.command[Combi, Normal].items():
            times = [(x['end'] - x['start']) for x in data if x['current'] == k and not x['closed'] and not x['arrival']]
            active.append({
                'id': v.id,
                'type': v.type,
                'desc': v.desc,
                'access': v.access,
                'first': v._first,
                'last': v._last,
                'avg': np.average(times),
                'std': np.std(times),
                'min': np.min(times) if v.access else 0,
                'max': np.max(times) if v.access else 0
            })

        if save:
            self._active = active

        return active

    def passive(self, data=None, save=True):
        """
        passive element 정보

        :param data:
        :param save:
        :return:
        """
        if data is None:
            data = self._env.data

        passive = []
        ### ????? 까먹음;
        for k, v in self._env.command[Queue].items():
            tn1 = 0
            tn11 = 0
            tn2 = 0
            tn3 = 0
            # TODO: avg. wait time 계산 이상함!!!! ~ model.*_change와 같이 수정!
            for p, q in self._env.passive[k]:
                if q == 0:
                    tn1 += p - tn2
                    tn11 += tn3 * (p - tn2)
                else:
                    tn2 = p
                    tn3 = q

            busy_time = 0
            prev_t = 0
            prev_v = -1
            for now_t, now_v in self._env.passive[k]:
                if prev_v > 0:
                    busy_time += now_t - prev_t
                prev_v = now_v
                prev_t = now_t

            total_time = self._env.data[-1]['end']
            idle_time = total_time - busy_time

            # wait_time = sum(self._env.waiting[k])
            wait_time = 0
            cnt = v.access
            passive.append({
                'id': v.id,
                'type': v.type,
                'desc': v.desc,
                'avg_idle': tn11 / total_time,
                'max': max(o[1] for o in self._env.passive[k]),
                'at_end': self._env.passive[k][-1][1],
                'time_ne': busy_time,  # self._model.data[-1][1] if tn1 > self._model.data[-1][1] else tn1,
                'access': cnt,
                'avg_wait': -1 if cnt == 0 else wait_time / cnt,
            })

        if save:
            self._passive = passive

        return passive

    def counter(self, save=True):
        counter = []

        data = self._env.data

        for k, v in self._env.command[Count].items():
            times = [x['start'] for x in data if x['current'] == k]
            sub = times[-1] - times[0]

            avg_interarrival = sub if v.count == 1 else sub / (v.count - 1)
            counter.append({
                'id': v.id,
                'desc': v.desc,
                'count': v.count,
                'avg_interarrival': avg_interarrival,
                'first': v._first,
                'last': v._last,
                'prod_rate': 0 if v.count == 1 else 1 / avg_interarrival
            })

        if save:
            self._counter = counter

        return counter

    def summary(self):
        if len(self._env.data) == 0:
            return {'executed': False}
        return {
            'executed': True,
            # 'prod': self.prod(),
            # 'active': self.active(),
            # 'passive': self.passive(),
            'counter': self.counter()
        }

    def summing(self):
        p = [x['counter'][0] for x in self.test.values()]
        prod_rate = np.average([x[3] for x in p])
        avg_inter = np.average([x[4] for x in p])
        first_arrival = np.average([x[5] for x in p])
        last_arrival = np.average([x[6] for x in p])

        # print(p)
        return [prod_rate, avg_inter, first_arrival, last_arrival]

    @classmethod
    def t2(cls):
        pass

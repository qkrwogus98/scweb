
import numpy as np
from typing import (
    List,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from .model import Model

from .element import Queue, Combi, Normal, Count

# TODO: 쓰레기 덩어리..

class Statistics:
    def __init__(self, model: 'Model'):
        self._model = model

        self.data = {}
        self.test = {}

        self._prod = []
        self._active = []
        self._passive = []
        self._counter = []

    def _test(self):
        assert self._model, "없어욤"
        print(self._model.data[-1][1])

    # 여려개로 나눠야함
    def prod(self, data=None, save=True):
        """
        productivity information

        :param data:
        :param save:
        :return:
        """
        if data is None:
            data = self._model.data

        prod = []
        p, q, s = [], [], []

        starting: Queue

        for k, v in self._model[Queue].items():
            if v.starting:
                starting = v
                break

        for x in data:
            if x[2] == starting.id and x[0] >= 0:
                p.append(x[0])
            elif x[3] == 'count':
                q.append(x[0])

        for i in range(len(q)):
            s.append(1 / (q[i] - p[i]))
            prod.append([
                i + 1,
                p[i],
                q[i],
                1 / (q[i] - p[i])
            ])

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
            data = self._model.data

        active = []
        ### TODO: 평균 내야함
        active.append([0, 'SCENE', 'Scenario', 1, 0, 0, data[-1][1], 0, 0, 0])

        for k, v in self._model[Combi, Normal].items():
            p = [(g[1] - g[0]) for g in data if g[2] == k and g[0] >= 0]
            active.append([
                v.id,
                v.type,
                v.desc,
                len(p),
                v._first,
                v._last,
                np.average(p),
                np.std(p),
                np.min(p) if len(p) else 0,
                np.max(p) if len(p) else 0
            ])

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
            data = self._model.data

        passive = []
        ### ????? 까먹음;
        for k, v in self._model[Queue].items():
            tn1 = 0
            tn11 = 0
            tn2 = 0
            tn3 = 0
            # TODO: avg. wait time 계산 이상함!!!! ~ model.*_change와 같이 수정!
            for p, q in self._model.passive[k]:
                if q == 0:
                    tn1 += p - tn2
                    tn11 += tn3 * (p - tn2)
                else:
                    tn2 = p
                    tn3 = q

            time = 0
            prev_t = 0
            prev_v = -1
            for now_t, now_v in self._model.passive[k]:
                if prev_v > 0:
                    time += now_t - prev_t
                prev_v = now_v
                prev_t = now_t
            wait_time = sum(self._model.waiting[k])
            cnt = v.access
            passive.append([
                v.id,
                v.type,
                v.desc,
                tn11 / self._model.data[-1][1],
                max(o[1] for o in self._model.passive[k]),
                self._model.passive[k][-1][1],
                time,  # self._model.data[-1][1] if tn1 > self._model.data[-1][1] else tn1,
                cnt,
                wait_time / cnt,
            ])

        if save:
            self._passive = passive

        return passive

    def counter(self, save=True):
        counter = []

        for k, v in self._model[Count].items():
            a = [p[0] for p in self._model.data if p[2] == k]

            if v.count == 1:
                v.count += 1

            counter.append([
                v.id,
                v.desc,
                v.count,
                -1,
                (a[-1] - a[0]) / (v.count - 1),
                v._first,
                v._last
            ])
            counter[-1][3] = 1 / counter[-1][4]

        if save:
            self._counter = counter

        return counter

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

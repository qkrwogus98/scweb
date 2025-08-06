
try:
    from typing import get_args  # >= (3, 8)
except ImportError:
    from .typing import _get_args as get_args

from .typing import *


class Network:
    def __init__(self, element):
        self._cls = element
        self._node = dict()

    @property
    def all(self):
        return self._node

    @all.setter
    def all(self, value):
        self._node = value

    @property
    def one(self):
        it = iter(self._node.items())
        return next(it)

    # @add.setter
    # def add(self, val):
    #     self._node.update(val)

    def add(self, key, value=None):
        if isinstance(key, ListLike):
            for x in key:
                self.add(x, value)
        else:
            self._node[key] = value

    def items(self):
        for k, v in self._node.items():
            yield k, v

    def get(self, key):
        if isinstance(key, type) and issubclass(key, self._cls):
        # if isinstance(key, type) and issubclass(key, elemCls):
            """
            TypeError: Subscripted generics cannot be used with class and instance checks
            """
            return {k: v for k, v in self._node.items() if isinstance(v, key)}
        # is_list_like
        # 그냥 isinstance 해도 되지만 그러면 subclass 확인이..
        elif isinstance(key, ListLike):
            # TODO: O(N*K).. 일단 귀찮
            temp = {}
            for x in key:
                temp.update(self[x])
                # temp.update(self.get(x))
            return temp
        elif isinstance(key, get_args(elemID)):
            # noinspection PyTypeChecker
            return self._node[key]

        return self._node

    __getitem__ = get

    def __iter__(self):
        return iter(self._node)

    def __contains__(self, item):
        try:
            return item in self._node
        except TypeError:
            return False

    def __len__(self):
        return len(self._node)

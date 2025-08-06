try:
    from typing import get_args  # >= (3, 8)
except ImportError:
    from .typing import _get_args as get_args

from .typing import *  # ListLike


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

    def add(self, key, value=None):
        if isinstance(key, ListLike):
            for x in key:
                self.add(x, value)
        else:
            self._node[key] = value

    def add_from(self, dicts):
        for x in dicts:
            self.add()

    def items(self):
        for k, v in self._node.items():
            yield k, v

    def values(self):
        for v in self._node.values():
            yield v

    # @functools.lru_cache(maxsize=128)
    def _search(self, start, find, n=1, cache={}):
        # TODO: bfs로 바꾸고 최대 깊이 제한하려고 했으나 구성 달라져 상관없을듯
        # TODO: 어쩄든 나중에 최적화하기
        for k in self[start].following:
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
            find=None
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

    def get(self, key):
        if isinstance(key, type) and issubclass(key, self._cls):  # elemCls
            # is class and subclass of Element
            """
            TypeError: Subscripted generics cannot be used with class and instance checks
            """
            return {k: v for k, v in self._node.items() if isinstance(v, key)}
        # is_list_like
        # 그냥 isinstance 해도 되지만 그러면 subclass 확인이..
        elif isinstance(key, ListLike):
            # TODO: key check 먼저
            return {k: v for k, v in self._node.items() if isinstance(v, key)}
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

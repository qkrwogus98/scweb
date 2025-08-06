from functools import wraps

from numpy import random  # for docstring test
from numpy.random import default_rng
# from typing import Sequence
from random import choice

from .typing import *

__all__ = ['random_generator', 'triangular', 'integers', 'normal', 'binomial', 'uniform', 'beta']


def docstring(docs: str):
    def wrapper(func: F):
        func.__doc__ = docs
        return func

    return wrapper


def random_generator(func: F):
    """
    Generator container for the random distribution

    class 형태로 상주, call 마다 "새로운" value 넘겨줌
    """

    # @wraps(func, updated=())
    class wrapper:
        def __init__(self, *args, **kwargs):
            self._func = func
            self._args = args
            self._kwargs = kwargs

        def __call__(self):
            return self._func(*self._args, **self._kwargs)

        def __repr__(self):
            return (
                f'{self._func.__name__}({", ".join(map(str, self._args))})'
            )
            # return f'<{self.__module__}.{func.__name__} function wrapped with random_generator at {id(self):#x}>'

    return wrapper


rng = default_rng()

# TODO: random __all__ foreach 돌려서


@docstring(random.triangular.__doc__)
# @random_generator2(random.triangular.__doc__)
def doc_test(left: float, mode: float, right: float):
    print(doc_test.__doc__)
    return rng.triangular(left, mode, right)


@random_generator
@docstring(random.triangular.__doc__)
def triangular(left, mode, right):
    return rng.triangular(left, mode, right)


@random_generator
def integers(low, high=None):
    return rng.integers(low, high)


@random_generator
def normal(loc: int, scale: float):
    return rng.normal(loc, scale)


@random_generator
def binomial(n: int, p: float):
    return rng.binomial(n, p)


@random_generator
def uniform(low: float = 0.0, high: float = 1.0):
    return rng.uniform(low, high)


@random_generator
def beta(a: float, b: float):
    return rng.beta(a, b)


@random_generator
def on_list(seq: ListLike):
    return choice(seq)

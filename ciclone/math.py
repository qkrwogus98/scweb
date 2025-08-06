from numpy import random  # for docstring test
from numpy.random import default_rng
# from typing import Sequence

from .typing import *


def docstring(docs: str):
    def wrapper(func: F):
        func.__doc__ = docs
        return func

    return wrapper


rng = default_rng()


class Generator:
    """
    Container for the distributions

    class 형태로 상주, call 마다 "새로운" value 넘겨줌
    """

    def __init__(self, func: F):
        self._func = func

    # __float__
    def __call__(self, *args, **kwargs) -> F:
        return self._func(*args, **kwargs)


# test
@Generator
def tri2(left, mode, right):
    return rng.triangular(left, mode, right)


@docstring(random.triangular.__doc__)
def triangular(left: float, mode: float, right: float) -> Generator:
    return Generator(
        lambda: rng.triangular(left, mode, right)
    )


def normal(loc: int, scale: float):
    return Generator(
        lambda: rng.normal(loc, scale)
    )


def binomial(n: int, p: float):
    return Generator(
        lambda: rng.binomial(n, p)
    )


def uniform(low: float = 0.0, high: float = 1.0):
    return Generator(
        lambda: rng.uniform(low, high)
    )


def beta(a: float, b: float):
    return Generator(
        lambda: rng.beta(a, b)
    )

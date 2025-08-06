import typing as t
import collections.abc

if t.TYPE_CHECKING:
    from .element import Element
    # from .entities import Entity
    # from .math import Generator

elemID = t.Union[int, str]
elemCls = t.Type['Element']
elemOf = t.TypeVar('elemOf', bound='Element')

simTime = t.Union[float, int, t.Callable]
Infinity = float('inf')

GenNone = t.Generator[t.Any, t.Any, None]
GenReturn = t.Generator[t.Any, t.Any, t.Optional[t.Union[int, t.Sequence['Entity']]]]

FuncType = t.Callable[..., t.Any]
F = t.TypeVar("F", bound=FuncType)

ListLike = collections.abc.Sequence  # (tuple, list)


def _get_args(tp):
    res = tp.__args__
    if res[0] is not Ellipsis:
        return list(res[:-1]), res[-1]
    return ()

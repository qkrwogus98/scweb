from typing import (
    Any,
    Dict,
    Tuple,
    List,
    Optional,
    Union,
    Type,
    overload,
    final,
    Sequence,
    Iterator,
    Iterable,
    TYPE_CHECKING
)

from .typing import *

if TYPE_CHECKING:
    from .element import Element

_NodeType = Dict[elemID, 'Element']

@final
class Network:

    _cls: elemCls
    _node: _NodeType

    def __init__(self, element: elemCls): ...

    @property
    def all(self) -> _NodeType: ...
    @all.setter
    def all(self, value: _NodeType) -> None: ...

    @property
    def one(self) -> Tuple: ...

    @overload
    def add(self, key: elemID, value: elemOf) -> None: ...
    @overload
    def add(self, key: Sequence[elemID], value = None) -> None: ...

    def items(self) -> Iterable[Tuple[elemID, elemCls]]: ...

    def values(self) -> Iterable[elemCls]: ...

    @overload
    def get(self, key: Union[Tuple, List]) -> Dict[elemID, elemCls]: ...
    @overload
    def get(self, key: Type[elemOf]) -> Dict[elemID, elemOf]: ...
    @overload
    def get(self, key: elemID) -> elemCls: ...

    @overload
    def __getitem__(self, key: Union[Tuple, List]) -> Dict[elemID, elemCls]: ...
    @overload
    def __getitem__(self, key: Type[elemOf]) -> Dict[elemID, elemOf]: ...
    @overload
    def __getitem__(self, key: elemID) -> elemCls: ...

    def __iter__(self) -> Iterator: ...

    def __contains__(self, item) -> bool: ...

    def __len__(self) -> int: ...

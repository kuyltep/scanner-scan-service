import copy
from typing import Iterator
from smalivm.smali.registers import RegisterValue
from smalivm.smali.registers_values.unknown import UnknownValue


class Array:
    """
    Initialize array indexes only on access it for saving memory
    """
    __items: dict[int, RegisterValue]
    _size: int
    _type: str

    def __init__(self, size: int, type: str) -> None:
        self.__items = {}
        self._size = size
        self._type = type

    def __getitem__(self, index: int) -> "RegisterValue":
        if index < 0 or index >= self._size:
            raise IndexError("Index out of bounds")
        if index not in self.__items:
            self.__items[index] = RegisterValue(UnknownValue(), "<unknown>")
        return self.__items[index]

    def __setitem__(self, index: int, value: "RegisterValue") -> None:
        if index < 0 or index >= self._size:
            raise IndexError("Index out of bounds")
        self.__items[index] = value

    def get_type(self) -> str:
        return self._type

    def __repr__(self) -> str:
        return "Array({})".format(self.__items)

    def __str__(self) -> str:
        return "Array({})".format(self.__items)

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[RegisterValue]:
        return iter(self.__items.values())

    def __copy__(self) -> "Array":
        arr = Array(self._size, self._type)
        for index, item in self.__items.items():
            arr.__items[index] = copy.copy(item)
        return arr

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Array):
            return False
        return self.__items == value.__items

    def __hash__(self) -> int:
        return hash(tuple(self.__items))

import locale
from typing import Any, Generator, Self, overload, TYPE_CHECKING

from smalivm.framework.base_framework_class import BaseFrameworkClass

if TYPE_CHECKING:
    from smalivm.framework.java.lang import StringBuilder

from smalivm.smali.registers import RegisterValue
from smalivm.smali.registers_values.unknown import UnknownValue


class FrameworkClass(BaseFrameworkClass):
    data: str

    def __init__(self) -> None:
        super().__init__()
        self._source = "String.java"

        self.flags = ["public", "final"]

    @property
    def initialized(self) -> bool:
        return hasattr(self, "data")

    # @property
    # def data(self) -> str:
    #     return self.data

    @overload
    def _init_(self) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: str) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: RegisterValue) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: bytes) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: bytes, d: int) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: bytes, d: int, d2: int) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: bytes, d: int, d2: int, d3: int) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: bytes, d: int, d2: int, d3: str) -> Self | UnknownValue: ...

    @overload
    def _init_(
        self, data: bytes, d: int, d2: int, d3: RegisterValue
    ) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: bytes, d: str) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: bytes, d: RegisterValue) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: list[str]) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: list[str], d: int, d2: int) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: list[int], d: int, d2: int) -> Self | UnknownValue: ...

    @overload
    def _init_(self, data: "StringBuilder.FrameworkClass") -> Self | UnknownValue: ...

    def _init_(self, data=None, d=None, d2=None, d3=None) -> Self | UnknownValue:
        if data is None:
            return UnknownValue()
        elif isinstance(data, RegisterValue):
            if not data.is_string():
                return UnknownValue()
            self.data = data.get_string()
        else:
            self.data = data

        return self

    def getBytes(
        self, charset: str | RegisterValue | None = None
    ) -> bytes | UnknownValue:
        if isinstance(charset, RegisterValue) or not hasattr(self, "data"):
            return UnknownValue()
        if charset is None:
            charset = locale.getpreferredencoding()

        charset = charset.upper()

        if charset == "UTF-8":
            return self.data.encode("utf-8")
        elif charset == "ISO-8859-1":
            return self.data.encode("latin-1")
        elif charset == "US-ASCII":
            return self.data.encode("ascii")
        elif charset == "UTF-16BE":
            return self.data.encode("utf-16-be")

        return self.data.encode(charset)

    # def toString(self) -> str:
    #     return self.__data

    @staticmethod
    def format(
        format: RegisterValue, *args: RegisterValue
    ) -> "FrameworkClass | UnknownValue":
        if format.is_unknown() or format.is_null():
            return UnknownValue()
        format_string = format.get_string()

        def get_value(val: RegisterValue) -> UnknownValue | str | list[str]:
            if val.is_unknown():
                return UnknownValue()
            elif val.is_array():
                values: list[str] = []
                for value in val.get_array():
                    value = get_value(value)
                    if isinstance(value, UnknownValue):
                        return value
                    elif isinstance(value, list):
                        for v in get_list_values(value):
                            values.append(str(v))
                    else:
                        values.append(str(value))
                return values
            elif val.is_class():
                cls = val.get_class()
                if isinstance(cls, FrameworkClass):
                    return cls.data
                else:
                    raise ValueError("Invalid value type")
            else:
                return str(val.get())

        def get_list_values(val: list[Any]) -> Generator[Any, None, None]:
            for v in val:
                if isinstance(v, RegisterValue):
                    yield get_value(v)
                elif isinstance(v, list):
                    yield from get_list_values(v)
                else:
                    yield v

        values = []
        for arg in args:
            value = get_value(arg)
            if isinstance(value, UnknownValue):
                return value
            elif isinstance(value, list):
                values.extend(value)
            else:
                values.append(value)
        return FrameworkClass()._init_(format_string % tuple(values))

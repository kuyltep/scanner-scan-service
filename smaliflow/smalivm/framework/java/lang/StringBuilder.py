from typing import Self
from smalivm.framework.base_framework_class import BaseFrameworkClass
from smalivm.framework.java.lang import String
from smalivm.smali.registers import RegisterValue
from smalivm.smali.registers_values.unknown import UnknownValue


class FrameworkClass(BaseFrameworkClass):
    __data: str

    def __init__(self) -> None:
        super().__init__()
        self._source = "StringBuilder.java"

        self.flags = ["public", "final"]

    def _init_(self, data: RegisterValue | None = None) -> None:
        if data is not None and data.is_string():
            self.__data = data.get_string()
        else:
            self.__data = ""

    def append(self, *data: RegisterValue) -> Self | UnknownValue:
        if len(data) == 0:
            raise ValueError("No data provided to append")
        value = data[0]
        if value.is_unknown():
            return UnknownValue()

        value_data = value.get()
        if isinstance(value_data, (str, float, int)):
            self.__data += str(value_data)
        elif isinstance(value_data, String.FrameworkClass) and value_data.initialized:
            self.__data += value_data.data
        else:
            return UnknownValue()
        return self

    def toString(self) -> String.FrameworkClass | UnknownValue:
        return String.FrameworkClass()._init_(self.__data)

import copy
import re
import struct
from typing import Iterable, Union, overload

from smalivm.exceptions import (
    InvalidRegisterTypeError,
    RegisterInvalidValue,
    RegisterNotFound,
    RegisterNotInitialized,
)
from smalivm.smali.members import Class
from smalivm.smali.registers_values.no_value import NoValue
from smalivm.smali.registers_values.unknown import UnknownValue
from dataclasses import dataclass


RegisterValueType = Union[str, "Array", UnknownValue]
FLOAT_MAX_VALUE = float.fromhex("0x1.fffffeP+127")
DOUBLE_MAX_VALUE = float.fromhex("0x1.fffffffffffffP+1023")
INT_MAX_VALUE = 0x7FFFFFFF


REGISTER_NAME_PATTERN = re.compile(r"^[vp]\d+$")


@dataclass(slots=True, init=False)
class RegisterValue:
    __value: "RegisterValueType | AmbiguousValue | NoValue | Class"
    __value_type: str

    @overload
    def __init__(
        self,
        value: "RegisterValueType | AmbiguousValue | NoValue | Class",
        value_type: str,
    ) -> None: ...
    @overload
    def __init__(
        self,
        value: "RegisterValueType | AmbiguousValue | NoValue | Class",
    ) -> None: ...

    def __init__(
        self,
        value,
        value_type=None,
    ) -> None:
        self.__value = value
        if value_type is None:
            value_type = "<unknown>"
        self.__value_type = value_type

    def get(
        self,
    ) -> "RegisterValueType | AmbiguousValue | NoValue | Class":
        return self.__value

    def get_string(self) -> str:
        from smalivm.framework.java.lang.String import FrameworkClass as FrameworkString

        value = self.get()
        if isinstance(value, FrameworkString) and value.initialized:
            return value.data
        raise RegisterInvalidValue("string")

    def get_int(self) -> int:
        value = self.get()
        if not isinstance(value, str):
            raise RegisterInvalidValue("int")
        if value.endswith("L") or value.endswith("t"):
            value = value[:-1]
        return int(value, 16)

    def get_double(self) -> float:
        value = self.get()
        if not isinstance(value, str):
            raise RegisterInvalidValue("double")
        if value == "nan":
            return float("nan")
        if value.endswith("L"):
            value = value[:-1]
        if self._is_hex_float(value):
            return float.fromhex(value)
        else:
            int_value = int(value, 16) & 0xFFFFFFFFFFFFFFFF
            return struct.unpack("d", struct.pack("Q", int_value))[0]

    def get_float(self) -> float:
        value = self.get()
        if not isinstance(value, str):
            raise RegisterInvalidValue("float")
        if value == "nan":
            return float("nan")
        if value.endswith("L"):
            value = value[:-1]
        if self._is_hex_float(value):
            return float.fromhex(value)
        else:
            float_value = int(value, 16)
            if 0 <= float_value <= 4294967295:
                float_value = struct.unpack("f", struct.pack("I", float_value))[0]
            return float.fromhex(value)

    def get_long(self) -> int:
        LONG_MAX = (1 << 63) - 1
        LONG_MIN = -(1 << 63)
        value = self.get_int()
        # if not (LONG_MIN <= value <= LONG_MAX):
        #     raise RegisterInvalidValue("Value is out of long range")
        return value

    def get_array(self) -> "Array":
        value = self.get()
        if not isinstance(value, Array):
            raise RegisterInvalidValue("array")
        return value

    def get_ambiguous(self) -> "AmbiguousValue":
        value = self.get()
        if not isinstance(value, AmbiguousValue):
            raise RegisterInvalidValue("ambiguous")
        return value

    def get_boolean(self) -> bool:
        value = self.get_int()
        if value == 1:
            return True
        elif value == 0:
            return False
        raise RegisterInvalidValue("boolean")

    def get_class(self) -> "Class":
        value = self.get()
        if not isinstance(value, Class):
            raise RegisterInvalidValue("class")
        return value

    # def get_smali_class(self) -> "SmaliClass":
    #     value = self.get()
    #     if not isinstance(value, SmaliClass):
    #         raise RegisterInvalidValue("smali class")
    #     return value

    def set_value(
        self, value: "RegisterValueType | AmbiguousValue | NoValue | Class"
    ) -> None:
        self.__value = value

    # def is_null(self) -> bool:
    #     return isinstance(self.get(), NULL)

    def is_unknown(self) -> bool:
        return isinstance(self.get(), UnknownValue)

    def is_array(self) -> bool:
        return isinstance(self.get(), Array)

    def is_int(self) -> bool:
        try:
            self.get_int()
            return True
        except RegisterInvalidValue:
            return False

    def is_class(self) -> bool:
        return isinstance(self.get(), Class)

    def is_string(self) -> bool:
        try:
            self.get_string()
            return True
        except RegisterInvalidValue:
            return False

    def is_null(self) -> bool:
        return self.get() == "0x0"

    def _is_hex_float(self, value: str):
        return bool(re.match(r"^[+-]?0x[0-9a-fA-F]+\.[0-9a-fA-F]*p[+-]?\d+$", value))

    def __copy__(self) -> "RegisterValue":
        return RegisterValue(copy.copy(self.__value), self.__value_type)

    def __repr__(self) -> str:
        return "RegisterValue({})".format(self.__value)

    def __hash__(self) -> int:
        return hash(self.__value)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, RegisterValue):
            return False
        return self.__value == value.__value

    @property
    def value_type(self) -> str:
        return self.__value_type

@dataclass(slots=True, init=False)
class Register:
    __name: str
    __value: RegisterValue | None
    pair: "Register | None"
    # __initialized: bool = False

    @property
    def name(self) -> str:
        return self.__name

    @property
    def value(self) -> RegisterValue:
        if self.__value is None:
            raise RegisterNotInitialized(self.name)
        return self.__value

    @value.setter
    def value(self, value: RegisterValue) -> None:
        self.__value = value
        # self.initialized = True

    @property
    def initialized(self) -> bool:
        return self.__value is not None

    # @initialized.setter
    # def initialized(self, value: bool) -> None:
    #     self.__initialized = value
    #     if not value:
    #         del self.__value

    def __init__(self, name: str) -> None:
        self.__name = name
        self.pair = None
        self.__value = None

    def __repr__(self) -> str:
        result = f"{self.name}"
        if self.pair:
            result = f"({result} + {self.pair.name})"
        if self.__value is not None:
            result += f" = {self.value.get()}"
        return result

    def has_value(self) -> bool:
        return (
            self.initialized
            and not isinstance(self.value.get(), UnknownValue)
            and not isinstance(self.value.get(), AmbiguousValue)
            and not isinstance(self.value.get(), NoValue)
        )

    def __copy__(self) -> "Register":
        register = Register(self.name)
        pair: Register | None = None
        if self.pair:
            pair = self.pair
            pair.pair = None
            register.pair = copy.copy(pair)
            pair.pair = register
        register.__value = copy.copy(self.__value)
        # register.__initialized = self.__initialized
        return register

    def reset(self) -> None:
        # self.__initialized = False
        # if hasattr(self, "_value"):
        #     del self.__value
        self.__value = None
        self.pair = None


class RegistersContext:
    __registers: tuple[Register, ...]
    # _max_count: int
    _count: int
    # _breakpoints_by_register_value: dict[
    #     str, dict[RegisterValue, set[Callable[["Register"], None]]]
    # ]
    # breakpoints: RegistersContextBreakpoints

    def __init__(self, registers: Iterable[Register]) -> None:
        self.__registers = tuple(registers)
        # self.breakpoints = RegistersContextBreakpoints()
        # self._count = 0
        # self._breakpoints_by_register_value = {}

        # self._max_count = max_count

    # def set_max_registers_count(self, count: int) -> None:
    #     self._max_count = count

    # def add_register(self, register: Register) -> None:
    #     if self._count >= self._max_count:
    #         raise MaxRegistersExceededError(
    #             register.name,
    #             self._max_count,
    #             list(map(lambda x: x.name, self._registers)),
    #         )
    #     self._registers.append(register)
    #     self._count += 1

    @overload
    def set_register(
        self,
        name: str,
        value: RegisterValueType,
        value_type: str | None,
        wide: bool,
    ) -> Register: ...

    @overload
    def set_register(
        self,
        name: str,
        value: RegisterValue,
        value_type: str | None,
        wide: bool,
    ) -> Register: ...

    @overload
    def set_register(
        self,
        name: str,
        value: "AmbiguousValue",
        value_type: str | None,
        wide: bool,
    ) -> Register: ...

    def set_register(
        self,
        name,
        value,
        value_type,
        wide=False,
    ) -> Register:
        if not REGISTER_NAME_PATTERN.match(name):
            raise ValueError(f"Invalid register name: {name}")

        register: Register | None = None
        try:
            register = self.get_register(name)
        except RegisterNotFound:
            # If the register is exists as a pair, we should use the pair register, break the pair and uninitialized the first register in the pair
            for reg in self.__registers:
                if reg.pair is not None and reg.pair.name == name:
                    register = reg.pair
                    # reg.pair = None
                    reg.reset()
                    # reg.initialized = False
                    break

            if register is None:
                raise RegisterNotFound(name)
                # register = Register(name)
                # self.add_register(register)
            if wide:
                pair_name = self._increment_register(name)
                # if self.has_register(pair_name):
                register.pair = self.get_register(pair_name)
                # else:
                #     register_pair = Register(pair_name)
                #     self._count += 1
                #     register.pair = register_pair
        register_value: RegisterValue
        if isinstance(value, RegisterValue):
            register_value = value
        else:
            register_value = RegisterValue(value, value_type)
        register.value = register_value
        # self.breakpoints.trigger(self, register, register_value.get())
        # self._trigger_breakpoints(register)
        if register.pair:
            if wide:
                register.pair.value = register_value
                # self._trigger_breakpoints(register.pair)
            else:
                # pair = register.pair
                register.pair = None
                # if not self.has_register(pair.name):
                #     self.__registers.add(pair)

        return register

    # def _trigger_breakpoints(self, register: Register):
    #     if register.name not in self._breakpoints_by_register_value:
    #         return
    #     for value, callbacks in self._breakpoints_by_register_value[
    #         register.name
    #     ].items():
    #         if register.value == value:
    #             for callback in callbacks:
    #                 callback(register)

    def get_register(self, name: str) -> Register:
        for reg in self.__registers:
            if reg.name == name:
                return reg
        raise RegisterNotFound(name)

    # def has_register(self, name: str) -> bool:
    #     for reg in self.__registers:
    #         if reg.name == name or (reg.pair and reg.pair.name == name):
    #             return True
    #     return False

    def get_registers(self) -> tuple[Register, ...]:
        return self.__registers

    def _increment_register(self, register: str):
        register_type = register[0]
        if register_type not in ["v", "p"]:
            raise InvalidRegisterTypeError(register_type)
        register_number = int(register[1:])
        register_number += 1
        return f"{register_type}{register_number}"

    # def get_max_registers_count(self) -> int:
    #     return self._max_count

    # def get_registers_count(self) -> int:
    #     return self._count

    def reset(self) -> None:
        for reg in self.__registers:
            reg.reset()

    # def add_breakpoint_by_register_value(
    #     self,
    #     register: str,
    #     value: RegisterValue,
    #     callback: Callable[["Register"], None],
    # ):
    #     if register not in self._breakpoints_by_register_value:
    #         self._breakpoints_by_register_value[register] = {}
    #     if value not in self._breakpoints_by_register_value[register]:
    #         self._breakpoints_by_register_value[register][value] = set()
    #     self._breakpoints_by_register_value[register][value].add(callback)

    # def remove_breakpoint_by_register_value(
    #     self,
    #     register: str,
    #     value: RegisterValue,
    #     callback: Callable[["Register"], None],
    # ):
    #     if (
    #         register in self._breakpoints_by_register_value
    #         and value in self._breakpoints_by_register_value[register]
    #     ):
    #         self._breakpoints_by_register_value[register][value].remove(callback)

    # def take_snapshot(self) -> Self:
    #     return copy.copy(self)

    # def restore_snapshot(self, snapshot: "RegistersContext") -> None:
    #     self.reset()
    #     self.__registers = copy.copy(snapshot.__registers)
    #     self._count = snapshot._count
    #     self._max_count = snapshot._max_count
    #     self._breakpoints_by_register_value = copy.copy(snapshot._breakpoints_by_register_value)

    def __repr__(self) -> str:
        return f"{self.__registers}"

    def __copy__(self) -> "RegistersContext":
        registers: list[Register] = []
        for reg in self.__registers:
            registers.append(copy.copy(reg))
        context = RegistersContext(registers)
        # context.breakpoints = self.breakpoints
        # context._max_count = self._max_count
        # context._count = self._count
        # for reg in self.__registers:
        #     context.__registers.add(copy.copy(reg))
        return context


# class NULL:
#     def __hash__(self) -> int:
#         return id(self)


from smalivm.smali.registers_values.ambiguous import AmbiguousValue
from smalivm.smali.registers_values.array import Array

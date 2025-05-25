# import copy
# import inspect
# import re
# import struct
# from typing import (
#     Callable,
#     Iterable,
#     Iterator,
#     Literal,
#     Union,
#     overload,
#     TYPE_CHECKING
# )

# from smalivm.exceptions import (
#     InvalidRegisterTypeError,
#     RegisterInvalidValue,
#     RegisterNotFound,
#     RegisterNotInitialized,
# )
# from smalivm.iterator import InstructionsIterator
# from smalivm.smali import labels
# from smalivm.smali import directives
# from smalivm.smali.directives import Directive
# from smalivm.smali.instructions import (
#     ConstString,
#     ConstStringJumbo,
#     Instruction,
#     InvokeType,
#     MoveResultObject,
# )
# from smalivm.smali.labels import Label
# from smalivm.smali.parsers import LineParser
# from smalivm.smali.reader import Reader
# from smalivm.smali.utils import parse_method_parameters




# class RegistersContextBreakpoints:
#     __by_value_type: dict[
#         Literal["string"],
#         set[
#             Callable[
#                 [
#                     "RegistersContext",
#                     Register,
#                 ],
#                 bool | None,
#             ]
#         ],
#     ]

#     def __init__(self) -> None:
#         self.__by_value_type = {}

#     # @overload
#     # def add(
#     #     self,
#     #     condition: Type[RegisterValueType],
#     # callback: Callable[
#     #     [
#     #         "RegistersContext",
#     #         Register,
#     #         RegisterValueType,
#     #     ],
#     #     bool | None,
#     # ],
#     # ) -> None: ...

#     def add_by_value_type(
#         self,
#         value_type: Literal["string"],
#         callback: Callable[
#             [
#                 "RegistersContext",
#                 Register,
#             ],
#             bool | None,
#         ],
#     ) -> None:
#         if value_type not in self.__by_value_type:
#             self.__by_value_type[value_type] = set()
#         self.__by_value_type[value_type].add(callback)

#     # def add(
#     #     self,
#     #     condition: "Type[RegisterValueType | AmbiguousValue | NoValue | Class]",
#     #     callback: Callable[
#     #         [
#     #             "RegistersContext",
#     #             Register,
#     #             "RegisterValueType | AmbiguousValue | NoValue | Class",
#     #         ],
#     #         bool | None,
#     #     ],
#     # ) -> None:
#     #     if issubclass(condition, (RegisterValueType, AmbiguousValue, NoValue, Class)):
#     #         if condition.__class__ not in self.__by_value_type:
#     #             self.__by_value_type[condition] = set()
#     #         self.__by_value_type[condition].add(callback)
#     #     else:
#     #         raise ValueError(f"Invalid condition type: {type(condition)}")

#     def trigger(
#         self,
#         context: "RegistersContext",
#         register: Register,
#         value: "RegisterValueType | AmbiguousValue | NoValue | Class",
#     ) -> None:
#         for value_type, callbacks in self.__by_value_type.items():
#             if isinstance(value, value_type):
#                 for callback in callbacks:
#                     callback(context, register, value)


# class MethodBreakpoints:
    # __by_instructions: dict[
    #     Instruction | Label | Directive,
    #     set[Callable[[RegistersContext, Instruction | Label | Directive], bool | None]],
    # ]
    # __by_conditions: set[
    #     tuple[
    #         Callable[[RegistersContext, Instruction | Label | Directive], bool],
    #         Callable[[RegistersContext, Instruction | Label | Directive], bool | None],
    #     ]
    # ]

    # def __init__(self) -> None:
    #     self.__by_instructions = {}
    #     self.__by_conditions = set()

    # @overload
    # def add(
    #     self,
    #     condition: Instruction | Label | Directive,
    #     callback: Callable[
    #         [RegistersContext, Instruction | Label | Directive], bool | None
    #     ],
    # ) -> None: ...

    # @overload
    # def add(
    #     self,
    #     condition: Callable[[RegistersContext, Instruction | Label | Directive], bool],
    #     callback: Callable[
    #         [RegistersContext, Instruction | Label | Directive], bool | None
    #     ],
    # ) -> None: ...

    # def add(self, condition, callback) -> None:
    #     if inspect.isfunction(condition) or inspect.ismethod(condition):
    #         self.__by_conditions.add((condition, callback))
    #     elif isinstance(condition, Instruction | Label | Directive):
    #         if condition not in self.__by_instructions:
    #             self.__by_instructions[condition] = set()
    #         self.__by_instructions[condition].add(callback)
    #     else:
    #         raise ValueError(f"Invalid condition type: {type(condition)}")

    # @overload
    # def remove(
    #     self,
    #     condition: Instruction | Label | Directive,
    #     callback: Callable[
    #         [RegistersContext, Instruction | Label | Directive], bool | None
    #     ],
    # ) -> None: ...

    # @overload
    # def remove(
    #     self,
    #     condition: Callable[[RegistersContext, Instruction | Label | Directive], bool],
    #     callback: Callable[
    #         [RegistersContext, Instruction | Label | Directive], bool | None
    #     ],
    # ) -> None: ...

    # def remove(
    #     self,
    #     condition: (
    #         Instruction
    #         | Label
    #         | Directive
    #         | Callable[[RegistersContext, Instruction], bool]
    #     ),
    #     callback: Callable[
    #         [RegistersContext, Instruction | Label | Directive], bool | None
    #     ],
    # ) -> None:
    #     if inspect.isfunction(condition) or inspect.ismethod(condition):
    #         self.__by_conditions.remove((condition, callback))
    #     elif isinstance(condition, Instruction | Label | Directive):
    #         if condition in self.__by_instructions:
    #             self.__by_instructions[condition].remove(callback)
    #         if len(self.__by_instructions[condition]) == 0:
    #             del self.__by_instructions[condition]
    #     else:
    #         raise ValueError(f"Invalid condition type: {type(condition)}")

    # # @overload
    # # def trigger(
    # #     self, context: RegistersContext, ins: Instruction | Label | Directive
    # # ) -> bool | None: ...

    # # @overload
    # # def trigger(
    # #     self,
    # #     context: RegistersContext,
    # #     ins: Instruction | Label | Directive,
    # #     reg: Register,
    # # ) -> bool | None: ...

    # def trigger(
    #     self,
    #     context: RegistersContext,
    #     ins: Instruction | Label | Directive,
    #     # reg: Register | None = None,
    # ) -> bool | None:
    #     # if reg is not None:
    #     #     if (
    #     #         reg.initialized
    #     #         and reg.has_value()
    #     #         and reg.value.get() in self.__by_value_type
    #     #     ):
    #     #         for callback in self.__by_value_type[reg.value.get()]:
    #     #             if callback(context, ins) == False:
    #     #                 return False
    #     # else:
    #     if ins in self.__by_instructions:
    #         for callback in self.__by_instructions[ins]:
    #             if callback(context, ins) == False:
    #                 return False
    #     for condition, callback in self.__by_conditions:
    #         if condition(context, ins) and callback(context, ins) == False:
    #             return False
from typing import Callable, Literal
from smalivm.iterator import InstructionsIterator
from smalivm.smali.helper import INSTRUCTION_TYPE_INVOKE
from smalivm.smali.instructions import (
    ConstString,
    ConstStringJumbo,
    FilledNewArray,
    FilledNewArrayRange,
    Instruction,
    MoveResultObject,
)
from smalivm.smali.registers import Register, RegistersContext

class Breakpoints:
    # __methods_breakpoints: dict[Method, MethodBreakpoints]
    __by_instructions: dict[
        Instruction,
        set[Callable[[RegistersContext, Instruction], bool | None]],
    ]
    __by_custom_condition: dict[
        Callable[[RegistersContext, Instruction], bool],
        set[Callable[[RegistersContext, Instruction], bool | None]],
    ]
    __by_value_type: dict[
        Literal["string"],
        set[
            Callable[
                [RegistersContext, Instruction, Register, str],
                bool | None,
            ]
        ],
    ]

    def __copy__(self) -> "Breakpoints":
        new_instance = Breakpoints()
        new_instance.__by_instructions = self.__by_instructions.copy()
        new_instance.__by_custom_condition = self.__by_custom_condition.copy()
        new_instance.__by_value_type = self.__by_value_type.copy()
        return new_instance

    def __init__(self) -> None:
        # self.__methods_breakpoints = {}
        self.__by_instructions = {}
        self.__by_custom_condition = {}
        self.__by_value_type = {}

    # def by_value_type(self, value_type: RegisterValueType | AmbiguousValue | NoValue | Class, callback: Callable[[], None]) -> None:
    #     pass

    def add_by_instruction(
        self,
        ins: Instruction,
        callback: Callable[[RegistersContext, Instruction], bool | None],
    ) -> None:
        if ins not in self.__by_instructions:
            self.__by_instructions[ins] = set()
        self.__by_instructions[ins].add(callback)

    def add_by_custom_condition(
        self,
        condition: Callable[[RegistersContext, Instruction], bool],
        callback: Callable[[RegistersContext, Instruction], bool | None],
    ) -> None:
        if condition not in self.__by_custom_condition:
            self.__by_custom_condition[condition] = set()
        self.__by_custom_condition[condition].add(callback)

    def add_by_value_type(
        self,
        value_type: Literal["string"],
        callback: Callable[
            [RegistersContext, Instruction, Register, str],
            bool | None,
        ],
    ) -> None:
        if value_type not in self.__by_value_type:
            self.__by_value_type[value_type] = set()
        self.__by_value_type[value_type].add(callback)

    # def by_value_type(
    #     self,
    #     value_type: Type[RegisterValueType | AmbiguousValue | NoValue | Class],
    #     callback: Callable[
    #         [
    #             RegistersContext,
    #             Instruction | Label | Directive,
    #             Register,
    #             RegisterValueType | AmbiguousValue | NoValue | Class,
    #         ],
    #         bool | None,
    #     ],
    # ) -> None:
    #     if value_type not in self.__by_value_type:
    #         self.__by_value_type[value_type] = set()
    #     self.__by_value_type[value_type].add(callback)

    def remove_by_instruction(
        self,
        ins: Instruction,
        callback: Callable[[RegistersContext, Instruction], bool | None],
    ) -> None:
        if ins in self.__by_instructions:
            self.__by_instructions[ins].remove(callback)
            if len(self.__by_instructions[ins]) == 0:
                del self.__by_instructions[ins]

    def remove_by_custom_condition(
        self,
        condition: Callable[[RegistersContext, Instruction], bool],
        callback: Callable[[RegistersContext, Instruction], bool | None],
    ):
        if condition in self.__by_custom_condition:
            self.__by_custom_condition[condition].remove(callback)
            if len(self.__by_custom_condition[condition]) == 0:
                del self.__by_custom_condition[condition]

    def remove_by_value_type(
        self,
        value_type: Literal["string"],
        callback: Callable[
            [RegistersContext, Instruction, Register, str],
            bool | None,
        ],
    ) -> None:
        if value_type in self.__by_value_type:
            self.__by_value_type[value_type].remove(callback)
            if len(self.__by_value_type[value_type]) == 0:
                del self.__by_value_type[value_type]

    # def remove_breakpoints(self, breakpoints_ins, breakpoint):
    #     to_remove = []
    #     for ins in breakpoints_ins:
    #         to_remove.append(ins)
    #     for ins in to_remove:
    #         self.__breakpoints.remove_by_instruction(
    #             ins, breakpoint  # pyright: ignore[reportArgumentType]
    #         )

    # def remove(self, callback: Callable) -> None:
    #     for_delete = []
    #     for ins in self.__by_instructions:
    #         if callback in self.__by_instructions[ins]:
    #             self.__by_instructions[ins].remove(callback)
    #             if len(self.__by_instructions[ins]) == 0:
    #                 for_delete.append(ins)
    #     for ins in for_delete:
    #         del self.__by_instructions[ins]
    #     for_delete.clear()
    #     for condition in self.__by_custom_condition:
    #         if callback in self.__by_custom_condition[condition]:
    #             self.__by_custom_condition[condition].remove(callback)
    #             if len(self.__by_custom_condition[condition]) == 0:
    #                 for_delete.append(condition)
    #     for condition in for_delete:
    #         del self.__by_custom_condition[condition]
    #     for_delete.clear()

    def trigger_before(self, ins: Instruction, context: RegistersContext) -> bool:
        ret = True
        if ins in self.__by_instructions:
            for callback in self.__by_instructions[ins]:
                if callback(context, ins) == False:
                    ret = False
        for condition in self.__by_custom_condition:
            if condition(context, ins):
                for callback in self.__by_custom_condition[condition]:
                    if callback(context, ins) == False:
                        ret = False

        return ret

    def trigger_after(
        self,
        ins: Instruction,
        context: RegistersContext,
        iterator: InstructionsIterator,
    ) -> bool:
        ret = True

        for value_type, callbacks in self.__by_value_type.items():
            if value_type == "string":
                if isinstance(ins, (ConstString, ConstStringJumbo)):
                    reg = context.get_register(ins.reg1)
                    if not reg.has_value():
                        continue
                    if reg.value.is_null():
                        continue
                    value = reg.value.get_string()
                    for callback in callbacks:
                        if callback(context, ins, reg, value) == False:
                            ret = False
                elif isinstance(ins, MoveResultObject):
                    back_count = 0
                    prev_ins = None
                    while not isinstance(prev_ins, Instruction):
                        back_count += 1
                        prev_ins = iterator.back()
                    for _ in range(back_count):
                        next(iterator)
                    strings: list[tuple[Register, str]] = []
                    if isinstance(prev_ins, INSTRUCTION_TYPE_INVOKE):
                        return_type = prev_ins.method_signature.split(")")[-1]
                        if return_type != "Ljava/lang/String;":
                            continue
                        reg = context.get_register(ins.reg1)
                        if not reg.has_value():
                            continue
                        if reg.value.is_null():
                            continue
                        value = reg.value.get_string()
                        strings.append((reg, value))
                    elif isinstance(prev_ins, (FilledNewArray, FilledNewArrayRange)):
                        return_type = prev_ins.data[prev_ins.data.rindex("[") + 1 :]
                        if return_type != "Ljava/lang/String;":
                            continue
                        reg = context.get_register(ins.reg1)
                        if not reg.has_value():
                            continue
                        if not reg.value.is_array():
                            continue
                        for value in reg.value.get_array():
                            if value.is_string():
                                strings.append((reg, value.get_string()))
                        # for reg in prev_ins.registers:
                        #     reg = context.get_register(reg)
                        #     if not reg.has_value():
                        #         continue
                        #     if reg.value.is_null():
                        #         continue
                        #     value = reg.value.get_string()
                        #     strings.append((reg, value))
                    else:
                        raise ValueError(f"Invalid previous instruction: {prev_ins}")
                    for reg, value in strings:
                        for callback in callbacks:
                            if callback(context, ins, reg, value) == False:
                                ret = False

        return ret

    # @overload
    # def add(
    #     self,
    #     method: "Method",
    #     condition: Instruction | Label | Directive,
    # callback: Callable[
    #     [RegistersContext, Instruction | Label | Directive], bool | None
    # ],
    # ) -> None: ...
    # @overload
    # def add(
    #     self,
    #     method: "Method",
    #     condition: Callable[[RegistersContext, Instruction | Label | Directive], bool],
    #     callback: Callable[
    #         [RegistersContext, Instruction | Label | Directive], bool | None
    #     ],
    # ) -> None: ...

    # def add(
    #     self,
    #     method: "Method",
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
    #     if method not in self.__methods_breakpoints:
    #         self.__methods_breakpoints[method] = MethodBreakpoints()
    #     self.__methods_breakpoints[method].add(condition, callback)  # type: ignore

    # @overload
    # def remove(
    #     self,
    #     method: "Method",
    #     condition: Instruction | Label | Directive,
    #     callback: Callable[
    #         [RegistersContext, Instruction | Label | Directive], bool | None
    #     ],
    # ) -> None: ...
    # @overload
    # def remove(
    #     self,
    #     method: "Method",
    #     condition: Callable[[RegistersContext, Instruction | Label | Directive], bool],
    #     callback: Callable[
    #         [RegistersContext, Instruction | Label | Directive], bool | None
    #     ],
    # ) -> None: ...

    # def remove(
    #     self,
    #     method: "Method",
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
    #     if method in self.__methods_breakpoints:
    #         self.__methods_breakpoints[method].remove(condition, callback)  # type: ignore

    # def trigger(
    #     self,
    #     method: "Method",
    #     context: RegistersContext,
    #     ins: Instruction | Label | Directive,
    # ) -> bool | None:
    #     if method in self.__methods_breakpoints:
    #         return self.__methods_breakpoints[method].trigger(context, ins)

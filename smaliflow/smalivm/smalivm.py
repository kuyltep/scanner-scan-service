import copy
import gc
import logging
import math
import os
import sys
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from importlib import util as importutil
from typing import Any, Callable, Iterator, Literal, Type, cast, overload

from smalivm.breakpoints import Breakpoints
from smalivm.exceptions import (
    AbstractMethodError,
    ClassNotFoundError,
    MethodNotFoundError,
    SmaliFlowError,
    UnsupportedInstructionError,
)
from smalivm.framework.base_framework_class import BaseFrameworkClass
from smalivm.framework.java.lang import String
from smalivm.iterator import InstructionsIterator
from smalivm.smali import (
    AddDouble,
    AddDouble2Addr,
    AddFloat,
    AddFloat2Addr,
    AddInt,
    AddInt2Addr,
    AddIntLit8,
    AddIntLit16,
    AddLong,
    AddLong2Addr,
    Aget,
    AgetBoolean,
    AgetByte,
    AgetChar,
    AgetObject,
    AgetShort,
    AgetWide,
    AndInt,
    AndInt2Addr,
    AndIntLit8,
    AndIntLit16,
    AndLong,
    AndLong2Addr,
    Aput,
    AputBoolean,
    AputByte,
    AputChar,
    AputObject,
    AputShort,
    AputWide,
    ArrayLength,
    CheckCast,
    CmpgDouble,
    CmpgFloat,
    CmplDouble,
    CmplFloat,
    CmpLong,
    Const,
    Const4,
    Const16,
    ConstClass,
    ConstHigh16,
    ConstMethodHandle,
    ConstMethodType,
    ConstString,
    ConstStringJumbo,
    ConstWide,
    ConstWide16,
    ConstWide32,
    ConstWideHigh16,
    DivDouble,
    DivDouble2Addr,
    DivFloat,
    DivFloat2Addr,
    DivInt,
    DivInt2Addr,
    DivIntLit8,
    DivIntLit16,
    DivLong,
    DivLong2Addr,
    DoubleToFloat,
    DoubleToInt,
    DoubleToLong,
    FillArrayData,
    FilledNewArray,
    FilledNewArrayRange,
    FloatToDouble,
    FloatToInt,
    FloatToLong,
    Goto,
    Goto16,
    Goto32,
    IfEq,
    IfEqz,
    IfGe,
    IfGez,
    IfGt,
    IfGtz,
    IfLe,
    IfLez,
    IfLt,
    IfLtz,
    IfNe,
    IfNez,
    Iget,
    IgetBoolean,
    IgetByte,
    IgetChar,
    IgetObject,
    IgetShort,
    IgetWide,
    InstanceOf,
    Instruction,
    Instruction21t,
    Instruction22t,
    IntToByte,
    IntToChar,
    IntToDouble,
    IntToFloat,
    IntToLong,
    IntToShort,
    InvokeCustom,
    InvokeCustomRange,
    InvokeDirect,
    InvokeDirectRange,
    InvokeInterface,
    InvokeInterfaceRange,
    InvokePolymorphic,
    InvokePolymorphicRange,
    InvokeStatic,
    InvokeStaticRange,
    InvokeSuper,
    InvokeSuperRange,
    InvokeVirtual,
    InvokeVirtualRange,
    Iput,
    IputBoolean,
    IputByte,
    IputChar,
    IputObject,
    IputShort,
    IputWide,
    Label,
    LongToDouble,
    LongToFloat,
    LongToInt,
    MonitorEnter,
    MonitorExit,
    Move,
    Move16,
    MoveException,
    MoveFrom16,
    MoveObject,
    MoveObject16,
    MoveObjectFrom16,
    MoveResult,
    MoveResultObject,
    MoveResultWide,
    MoveWide,
    MoveWide16,
    MoveWideFrom16,
    MulDouble,
    MulDouble2Addr,
    MulFloat,
    MulFloat2Addr,
    MulInt,
    MulInt2Addr,
    MulIntLit8,
    MulIntLit16,
    MulLong,
    MulLong2Addr,
    NegDouble,
    NegFloat,
    NegInt,
    NegLong,
    NewArray,
    NewInstance,
    Nop,
    NotInt,
    NotLong,
    OrInt,
    OrInt2Addr,
    OrIntLit8,
    OrIntLit16,
    OrLong,
    OrLong2Addr,
    PackedSwitch,
    RemDouble,
    RemDouble2Addr,
    RemFloat,
    RemFloat2Addr,
    RemInt,
    RemInt2Addr,
    RemIntLit8,
    RemIntLit16,
    RemLong,
    RemLong2Addr,
    Return,
    ReturnObject,
    ReturnVoid,
    ReturnWide,
    RsubInt,
    RsubIntLit8,
    Sget,
    SgetBoolean,
    SgetByte,
    SgetChar,
    SgetObject,
    SgetShort,
    SgetWide,
    ShlInt,
    ShlInt2Addr,
    ShlIntLit8,
    ShlLong,
    ShlLong2Addr,
    ShrInt,
    ShrInt2Addr,
    ShrIntLit8,
    ShrLong,
    ShrLong2Addr,
    SparseSwitch,
    Sput,
    SputBoolean,
    SputByte,
    SputChar,
    SputObject,
    SputShort,
    SputWide,
    SubDouble,
    SubDouble2Addr,
    SubFloat,
    SubFloat2Addr,
    SubInt,
    SubInt2Addr,
    SubLong,
    SubLong2Addr,
    Throw,
    UshrInt,
    UshrInt2Addr,
    UshrIntLit8,
    UshrLong,
    UshrLong2Addr,
    XorInt,
    XorInt2Addr,
    XorIntLit8,
    XorIntLit16,
    XorLong,
    XorLong2Addr,
    directives,
    instructions,
)
from smalivm.smali.directives import Catch, CatchAll, Directive
from smalivm.smali.instructions import Instruction
from smalivm.smali.labels import Label
from smalivm.smali.members import Class, Method
from smalivm.smali.parsers import ClassParser
from smalivm.smali.registers import (  # NULL,
    Register,
    RegistersContext,
    RegisterValue,
    RegisterValueType,
)
from smalivm.smali.registers_values.ambiguous import AmbiguousValue
from smalivm.smali.registers_values.array import Array
from smalivm.smali.registers_values.no_value import NoValue
from smalivm.smali.registers_values.unknown import UnknownValue

logger = logging.getLogger("smalivm")
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


class InstructionsRunner:
    __context: RegistersContext
    __iterator: InstructionsIterator
    # __stack: list[Instruction | Label | Directive]
    __last_instruction_result: (
        RegisterValueType | AmbiguousValue | NoValue | Class | None
    ) = None
    __blocks: dict[str, list[Instruction | Label | Directive]]
    __returned_value: RegisterValue | None = None
    __vm: "Vm"
    __method: Method
    __breakpoints: Breakpoints
    __service_breakpoints: Breakpoints
    __into_try_catch_block: bool = False

    _invokes_stack: list[str]

    def __init__(
        self,
        instructions: list[Instruction | Label | Directive],
        context: RegistersContext,
        vm: "Vm",
        method: Method,
        breakpoints: Breakpoints,
        invokes_stack: list[str],
    ) -> None:
        self.__iterator = InstructionsIterator(instructions)
        self.__context = context
        # self.__stack = []
        self.__blocks = {}
        self.__vm = vm
        self.__method = method
        self.__breakpoints = breakpoints
        # self.__ambiguous_stack = set()
        self.__service_breakpoints = Breakpoints()
        self.depth = 0
        self._invokes_stack = invokes_stack

        self.__init_blocks(instructions)

    def set_register(
        self,
        name: str,
        value: Any,
        wide: bool = False,
        value_type: str | None = None,
    ) -> Register:
        return self.__context.set_register(name, value, value_type, wide)

    def seek(self, pos: int) -> None:
        self.__iterator.seek(pos)

    def get_iterator(self) -> InstructionsIterator:
        return self.__iterator

    def __init_blocks(self, instructions):
        self.__blocks.clear()
        block: list[Instruction | Label | Directive] = []
        self.__blocks["main"] = block
        for ins in instructions:
            block.append(ins)

            if isinstance(ins, Label):
                block = []
                if ins.name in self.__blocks:
                    block = self.__blocks[ins.name]
                else:
                    self.__blocks[ins.name] = block

    def run(self) -> RegisterValue | None:
        # if self.__method.get_full_signature() == "Lkotlin/jvm/internal/Intrinsics;->B(Ljava/lang/Throwable;Ljava/lang/String;)Ljava/lang/Throwable;":
        #     return
        # with open("/home/kiber/smaliflow/log.txt", "a") as f:
        #     # print(f"InstructionsRunner: {self.__method.get_full_signature()}")
        #     f.write(f"InstructionsRunner: {self.__method.get_full_signature()}\n")
        # if self.__method.get_full_signature() == "LDelayRepayUKAddBankDetailsMainBodyContentKt$DelayRepayAddBankDetailsMainBodyContent$2;->a(Landroidx/compose/runtime/Composer;I)V":
        #     pass
        # if self.__method.get_full_signature() == "Landroid/support/v4/media/MediaDescriptionCompat;->fromMediaDescription(Ljava/lang/Object;)Landroid/support/v4/media/MediaDescriptionCompat;":
        #     pass
        for ins in self.__iterator:
            # if self.__method.get_full_signature() == "LDelayRepayUKAddBankDetailsMainBodyContentKt$DelayRepayAddBankDetailsMainBodyContent$2;->a(Landroidx/compose/runtime/Composer;I)V":
            #     print(ins)
            # if str(ins) == "invoke-static {p2, v0, p1, v1}, LDelayRepayUKAddBankDetailsMainBodyContentKt;->a(Lcom/thetrainline/delay_repay_uk/claim/presentation/ui/data/DelayRepayUKPaymentMethodFormDetails$BankFormDetails;Lkotlin/jvm/functions/Function1;Landroidx/compose/runtime/Composer;I)V":
            #     pass
            # self.__stack.append(ins)
            previous_instruction_result = self.__last_instruction_result
            # self._write_branch()
            if isinstance(ins, Instruction):
                if self.__breakpoints.trigger_before(ins, self.__context) == False:
                    self.__iterator.stop()
                    break
                if (
                    self.__service_breakpoints.trigger_before(ins, self.__context)
                    == False
                ):
                    self.__iterator.stop()
                    break

            try:
                if isinstance(
                    ins,
                    (
                        Label,
                        Directive,
                        MonitorEnter,
                        MonitorExit,
                        CheckCast,
                        Nop,
                    ),
                ):
                    if isinstance(ins, Label):
                        if not self.__into_try_catch_block and ins.name.startswith(
                            "try_start_"
                        ):
                            self.__into_try_catch_block = True
                        elif self.__into_try_catch_block and ins.name.startswith(
                            "try_end_"
                        ):
                            self.__into_try_catch_block = False
                elif isinstance(ins, (ReturnVoid, Return, ReturnObject, ReturnWide)):
                    self.__iterator.stop()
                    if isinstance(ins, (Return, ReturnObject, ReturnWide)):
                        reg = self.__context.get_register(ins.reg1)
                        if reg.initialized:
                            if isinstance(reg.value.get(), BaseFrameworkClass):
                                value = cast(BaseFrameworkClass, reg.value.get())
                                if value.initialized:
                                    self.__returned_value = reg.value
                            else:
                                self.__returned_value = reg.value
                elif isinstance(ins, Throw):
                    self.__thrown = True
                    self.__iterator.stop()
                elif isinstance(
                    ins,
                    (
                        Const,
                        Const4,
                        Const16,
                        ConstHigh16,
                        ConstWide,
                        ConstWide16,
                        ConstWide32,
                        ConstWideHigh16,
                    ),
                ):
                    self._const(ins)
                elif isinstance(ins, InstanceOf):
                    self._instance_of(ins)
                elif isinstance(ins, (ConstString, ConstStringJumbo)):
                    self._const_string(ins)
                elif isinstance(ins, ConstClass):
                    self._const_class(ins)
                elif isinstance(
                    ins,
                    (
                        Move,
                        MoveFrom16,
                        Move16,
                        MoveObject,
                        MoveObjectFrom16,
                        MoveObject16,
                        MoveWide,
                        MoveWide16,
                        MoveWideFrom16,
                    ),
                ):
                    self._move(ins)
                elif isinstance(ins, Instruction22t):
                    self._if(ins)
                elif isinstance(ins, Instruction21t):
                    self._ifz(ins)
                elif isinstance(ins, (Goto, Goto16, Goto32)):
                    self._goto(ins)
                elif isinstance(ins, AddInt):
                    self._math_int(ins, lambda x, y: x + y)
                elif isinstance(ins, SubInt):
                    self._math_int(ins, lambda x, y: x - y)
                elif isinstance(ins, MulInt):
                    self._math_int(ins, lambda x, y: x * y)
                elif isinstance(ins, DivInt):
                    self._math_int(ins, lambda x, y: x // y)
                elif isinstance(ins, RemInt):
                    self._math_int(ins, lambda x, y: x % y)
                elif isinstance(ins, AddDouble):
                    self._math_double(ins, lambda x, y: x + y)
                elif isinstance(ins, SubDouble):
                    self._math_double(ins, lambda x, y: x - y)
                elif isinstance(ins, MulDouble):
                    self._math_double(ins, lambda x, y: x * y)
                elif isinstance(ins, DivDouble):
                    self._math_double(ins, lambda x, y: x / y)
                elif isinstance(ins, RemDouble):
                    self._math_double(ins, lambda x, y: x % y)
                elif isinstance(ins, NewArray):
                    self._new_array(ins)
                elif isinstance(
                    ins,
                    (
                        Aput,
                        AputWide,
                        AputObject,
                        AputBoolean,
                        AputByte,
                        AputChar,
                        AputShort,
                    ),
                ):
                    self._aput(ins)
                elif isinstance(
                    ins,
                    (
                        InvokeVirtual,
                        InvokeStatic,
                        InvokeSuper,
                        InvokeDirect,
                        InvokeInterface,
                        InvokePolymorphic,
                        InvokeCustom,
                        InvokeVirtualRange,
                        InvokeStaticRange,
                        InvokeSuperRange,
                        InvokeDirectRange,
                        InvokeInterfaceRange,
                        InvokePolymorphicRange,
                        InvokeCustomRange,
                    ),
                ):
                    self._invoke(ins)
                elif isinstance(
                    ins, (MoveResult, MoveResultObject, MoveResultWide, MoveException)
                ):
                    self._move_result(ins)
                elif isinstance(ins, ArrayLength):
                    self._array_length(ins)
                elif isinstance(ins, NewInstance):
                    self._new_instance(ins)
                elif isinstance(ins, (FilledNewArray, FilledNewArrayRange)):
                    self._filled_new_array(ins)
                elif isinstance(ins, FillArrayData):
                    self._fill_array_data(ins)
                elif isinstance(ins, instructions.PackedSwitch):
                    self._packed_switch(ins)
                elif isinstance(ins, instructions.SparseSwitch):
                    self._sparse_switch(ins)
                elif isinstance(ins, (CmplFloat, CmpgFloat)):
                    self._cmplg_float(ins)
                elif isinstance(ins, (CmplDouble, CmpgDouble)):
                    self._cmplg_double(ins)
                elif isinstance(ins, CmpLong):
                    self._cmp_long(ins)
                elif isinstance(
                    ins,
                    (
                        Aget,
                        AgetWide,
                        AgetObject,
                        AgetBoolean,
                        AgetByte,
                        AgetChar,
                        AgetShort,
                    ),
                ):
                    self._aget(ins)
                elif isinstance(
                    ins,
                    (
                        Iget,
                        IgetWide,
                        IgetObject,
                        IgetBoolean,
                        IgetByte,
                        IgetChar,
                        IgetShort,
                    ),
                ):
                    self._iget(ins)
                elif isinstance(
                    ins,
                    (
                        Iput,
                        IputWide,
                        IputObject,
                        IputBoolean,
                        IputByte,
                        IputChar,
                        IputShort,
                    ),
                ):
                    self._iput(ins)
                elif isinstance(
                    ins,
                    (
                        Sget,
                        SgetWide,
                        SgetObject,
                        SgetBoolean,
                        SgetByte,
                        SgetChar,
                        SgetShort,
                    ),
                ):
                    self._sget(ins)
                elif isinstance(
                    ins,
                    (
                        Sput,
                        SputWide,
                        SputObject,
                        SputBoolean,
                        SputByte,
                        SputChar,
                        SputShort,
                    ),
                ):
                    self._sput(ins)
                elif isinstance(ins, NegInt):
                    self._math_int2(ins, lambda x: -x)
                elif isinstance(ins, NotInt):
                    self._math_int2(ins, lambda x: ~x)
                elif isinstance(ins, NegLong):
                    self._math_long2(ins, lambda x: -x)
                elif isinstance(ins, NotLong):
                    self._math_long2(ins, lambda x: ~x)
                elif isinstance(ins, NegFloat):
                    self._math_float2(ins, lambda x: -x)
                elif isinstance(ins, NegDouble):
                    self._math_double2(ins, lambda x: -x)
                elif isinstance(ins, IntToLong):
                    self._int_to_long(ins)
                elif isinstance(ins, IntToFloat):
                    self._int_to_float(ins)
                elif isinstance(ins, IntToDouble):
                    self._int_to_double(ins)
                elif isinstance(ins, LongToInt):
                    self._long_to_int(ins)
                elif isinstance(ins, LongToFloat):
                    self._long_to_float(ins)
                elif isinstance(ins, LongToDouble):
                    self._long_to_double(ins)
                elif isinstance(ins, FloatToInt):
                    self._float_to_int(ins)
                elif isinstance(ins, FloatToLong):
                    self._float_to_long(ins)
                elif isinstance(ins, FloatToDouble):
                    self._float_to_double(ins)
                elif isinstance(ins, DoubleToInt):
                    self._double_to_int(ins)
                elif isinstance(ins, DoubleToLong):
                    self._double_to_long(ins)
                elif isinstance(ins, DoubleToFloat):
                    self._double_to_float(ins)
                elif isinstance(ins, IntToByte):
                    self._int_to_byte(ins)
                elif isinstance(ins, IntToChar):
                    self._int_to_char(ins)
                elif isinstance(ins, IntToShort):
                    self._int_to_short(ins)
                elif isinstance(ins, AndInt):
                    self._math_int(ins, lambda x, y: x & y)
                elif isinstance(ins, OrInt):
                    self._math_int(ins, lambda x, y: x | y)
                elif isinstance(ins, XorInt):
                    self._math_int(ins, lambda x, y: x ^ y)
                elif isinstance(ins, ShlInt):
                    self._math_int(ins, lambda x, y: x << y if y > 0 else x >> -y)
                elif isinstance(ins, ShrInt):
                    self._math_int(ins, lambda x, y: x >> y if y > 0 else x << -y)
                elif isinstance(ins, UshrInt):
                    self._math_int(
                        ins,
                        lambda x, y: (
                            (x % 0x100000000) >> y if y > 0 else (x % 0x100000000) << -y
                        ),
                    )
                elif isinstance(ins, AddLong):
                    self._math_long(ins, lambda x, y: x + y)
                elif isinstance(ins, SubLong):
                    self._math_long(ins, lambda x, y: x - y)
                elif isinstance(ins, MulLong):
                    self._math_long(ins, lambda x, y: x * y)
                elif isinstance(ins, DivLong):
                    self._math_long(ins, lambda x, y: x // y)
                elif isinstance(ins, RemLong):
                    self._math_long(ins, lambda x, y: x % y)
                elif isinstance(ins, AndLong):
                    self._math_long(ins, lambda x, y: x & y)
                elif isinstance(ins, OrLong):
                    self._math_long(ins, lambda x, y: x | y)
                elif isinstance(ins, XorLong):
                    self._math_long(ins, lambda x, y: x ^ y)
                elif isinstance(ins, ShlLong):
                    self._math_long(ins, lambda x, y: x << y)
                elif isinstance(ins, ShrLong):
                    self._math_long(ins, lambda x, y: x >> y if y > 0 else x << -y)
                elif isinstance(ins, UshrLong):
                    self._math_long(
                        ins,
                        lambda x, y: (
                            (x % 0x10000000000000000) >> y
                            if y > 0
                            else (x % 0x10000000000000000) << -y
                        ),
                    )
                elif isinstance(ins, AddFloat):
                    self._math_float(ins, lambda x, y: x + y)
                elif isinstance(ins, SubFloat):
                    self._math_float(ins, lambda x, y: x - y)
                elif isinstance(ins, MulFloat):
                    self._math_float(ins, lambda x, y: x * y)
                elif isinstance(ins, DivFloat):
                    self._math_float(ins, lambda x, y: x / y)
                elif isinstance(ins, RemFloat):
                    self._math_float(ins, lambda x, y: x % y)
                elif isinstance(ins, AddInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x + y)
                elif isinstance(ins, SubInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x - y)
                elif isinstance(ins, MulInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x * y)
                elif isinstance(ins, DivInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x // y)
                elif isinstance(ins, RemInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x % y)
                elif isinstance(ins, AndInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x & y)
                elif isinstance(ins, OrInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x | y)
                elif isinstance(ins, XorInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x ^ y)
                elif isinstance(ins, ShlInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x << y)
                elif isinstance(ins, ShrInt2Addr):
                    self._math_int_2addr(ins, lambda x, y: x >> y if y > 0 else x << -y)
                elif isinstance(ins, UshrInt2Addr):
                    self._math_int_2addr(
                        ins,
                        lambda x, y: (
                            (x % 0x100000000) >> y
                            if y >= 0
                            else (x % 0x100000000) << -y
                        ),
                    )
                elif isinstance(ins, AddLong2Addr):
                    self._math_long_2addr(ins, lambda x, y: x + y)
                elif isinstance(ins, SubLong2Addr):
                    self._math_long_2addr(ins, lambda x, y: x - y)
                elif isinstance(ins, MulLong2Addr):
                    self._math_long_2addr(ins, lambda x, y: x * y)
                elif isinstance(ins, DivLong2Addr):
                    self._math_long_2addr(ins, lambda x, y: x // y)
                elif isinstance(ins, RemLong2Addr):
                    self._math_long_2addr(ins, lambda x, y: x % y)
                elif isinstance(ins, AndLong2Addr):
                    self._math_long_2addr(ins, lambda x, y: x & y)
                elif isinstance(ins, OrLong2Addr):
                    self._math_long_2addr(ins, lambda x, y: x | y)
                elif isinstance(ins, XorLong2Addr):
                    self._math_long_2addr(ins, lambda x, y: x ^ y)
                elif isinstance(ins, ShlLong2Addr):
                    self._math_long_2addr(ins, lambda x, y: x << y)
                elif isinstance(ins, ShrLong2Addr):
                    self._math_long_2addr(
                        ins, lambda x, y: x >> y if y > 0 else x << -y
                    )
                elif isinstance(ins, UshrLong2Addr):
                    self._math_long_2addr(
                        ins,
                        lambda x, y: (
                            (x % 0x10000000000000000) >> y
                            if y > 0
                            else (x % 0x10000000000000000) << -y
                        ),
                    )
                elif isinstance(ins, AddFloat2Addr):
                    self._math_float_2addr(ins, lambda x, y: x + y)
                elif isinstance(ins, SubFloat2Addr):
                    self._math_float_2addr(ins, lambda x, y: x - y)
                elif isinstance(ins, MulFloat2Addr):
                    self._math_float_2addr(ins, lambda x, y: x * y)
                elif isinstance(ins, DivFloat2Addr):
                    self._math_float_2addr(ins, lambda x, y: x / y)
                elif isinstance(ins, RemFloat2Addr):
                    self._math_float_2addr(ins, lambda x, y: x % y)
                elif isinstance(ins, AddDouble2Addr):
                    self._math_double_2addr(ins, lambda x, y: x + y)
                elif isinstance(ins, SubDouble2Addr):
                    self._math_double_2addr(ins, lambda x, y: x - y)
                elif isinstance(ins, MulDouble2Addr):
                    self._math_double_2addr(ins, lambda x, y: x * y)
                elif isinstance(ins, DivDouble2Addr):
                    self._math_double_2addr(ins, lambda x, y: x / y)
                elif isinstance(ins, RemDouble2Addr):
                    self._math_double_2addr(ins, lambda x, y: x % y)
                elif isinstance(ins, AddIntLit16):
                    self._math_int_lit16(ins, lambda x, y: x + y)
                elif isinstance(ins, RsubInt):
                    self._math_int_lit16(ins, lambda x, y: y - x)
                elif isinstance(ins, MulIntLit16):
                    self._math_int_lit16(ins, lambda x, y: x * y)
                elif isinstance(ins, DivIntLit16):
                    self._math_int_lit16(ins, lambda x, y: x // y)
                elif isinstance(ins, RemIntLit16):
                    self._math_int_lit16(ins, lambda x, y: x % y)
                elif isinstance(ins, AndIntLit16):
                    self._math_int_lit16(ins, lambda x, y: x & y)
                elif isinstance(ins, OrIntLit16):
                    self._math_int_lit16(ins, lambda x, y: x | y)
                elif isinstance(ins, XorIntLit16):
                    self._math_int_lit16(ins, lambda x, y: x ^ y)
                elif isinstance(ins, AddIntLit8):
                    self._math_int_lit8(ins, lambda x, y: x + y)
                elif isinstance(ins, RsubIntLit8):
                    self._math_int_lit8(ins, lambda x, y: y - x)
                elif isinstance(ins, MulIntLit8):
                    self._math_int_lit8(ins, lambda x, y: x * y)
                elif isinstance(ins, DivIntLit8):
                    self._math_int_lit8(ins, lambda x, y: x // y)
                elif isinstance(ins, RemIntLit8):
                    self._math_int_lit8(ins, lambda x, y: x % y)
                elif isinstance(ins, AndIntLit8):
                    self._math_int_lit8(ins, lambda x, y: x & y)
                elif isinstance(ins, OrIntLit8):
                    self._math_int_lit8(ins, lambda x, y: x | y)
                elif isinstance(ins, XorIntLit8):
                    self._math_int_lit8(ins, lambda x, y: x ^ y)
                elif isinstance(ins, ShlIntLit8):
                    self._math_int_lit8(ins, lambda x, y: x << y)
                elif isinstance(ins, ShrIntLit8):
                    self._math_int_lit8(ins, lambda x, y: x >> y if y > 0 else x << -y)
                elif isinstance(ins, UshrIntLit8):
                    self._math_int_lit8(
                        ins,
                        lambda x, y: (
                            (x % 0x100000000) >> y if y > 0 else (x % 0x100000000) << -y
                        ),
                    )
                elif isinstance(ins, ConstMethodHandle):
                    self._const_method_handle(ins)
                elif isinstance(ins, ConstMethodType):
                    self._const_method_type(ins)
                else:
                    raise UnsupportedInstructionError(ins)
            except Exception as e:
                if isinstance(e, SmaliFlowError) or not self.__into_try_catch_block:
                    raise e
                for ins2 in self.__iterator:
                    if isinstance(ins2, (Catch, CatchAll)):
                        self.__iterator.seek(self.__iterator.index(ins2))
                        break

            if isinstance(ins, Instruction) and (
                self.__breakpoints.trigger_after(ins, self.__context, self.__iterator)
                == False
            ):
                self.__iterator.stop()
                break
            if isinstance(ins, Instruction) and (
                self.__service_breakpoints.trigger_after(
                    ins, self.__context, self.__iterator
                )
                == False
            ):
                self.__iterator.stop()
                break

            if (
                previous_instruction_result is not None
                and previous_instruction_result == self.__last_instruction_result
            ):
                self.__last_instruction_result = None

            # self.__stack.pop()

        return self.__returned_value

    def run_block(self, block_name: str) -> RegisterValue | None:
        block = self.__blocks[block_name]
        start_ins = block[0]
        start_pos = self.__iterator.index(start_ins)
        self.__iterator.seek(start_pos)
        return self.run()

    def _process_ambiguous_registers(self, positions: list[int]) -> None:
        # TODO: когда-нибудь потом пофиксить, пока останавливаем выполнение
        self.__iterator.stop()
        return

        def breakpoint(
            context: RegistersContext, ins: Instruction | Label | Directive
        ) -> bool | None:
            return False

        self.depth += 1
        # print(f"Depth: {self.depth}")
        if self.depth >= 10:
            self.__iterator.stop()
            return
        # cache_key = (id(self.__method), *sorted(positions))
        # if cache_key not in self.__vm.cache_ambiguous_values:
        values: dict[str, set[RegisterValue]] = {}
        returned_values: set[RegisterValue | None] = set()
        breakpoints_ins: list[Instruction | Label | Directive] = []

        for pos in positions:
            try:
                ins = self.__iterator.get(pos)
                self.__service_breakpoints.add_by_instruction(
                    ins, breakpoint  # pyright: ignore[reportArgumentType]
                )
                breakpoints_ins.append(ins)
            except IndexError:
                pass
        # self.__iterator.save_visited_positions(True)
        # threads: list[threading.Thread] = []
        orig_position = self.__iterator.tell()
        orig_context = self.__context

        for pos in positions:
            self.__iterator.resume()
            self.__returned_value = None
            self.__thrown = False
            # context = copy.copy(self.__context)
            registers: list[Register] = []
            for reg in orig_context.get_registers():
                registers.append(
                    Register(
                        reg.name,
                    )
                )
            self.__context = RegistersContext(registers)
            # runner = InstructionsRunner(
            #     self.__iterator.get_instructions(),
            #     context,
            #     self.__vm,
            #     self.__method,
            #     self.__breakpoints,
            # )
            # runner.get_iterator().save_visited_positions(True)
            # runner.get_iterator().get_visited_positions().update(self.get_iterator().get_visited_positions())
            self.seek(pos)
            # thread = threading.Thread(target=runner.run)
            # threads.append(thread)
            # thread.start()

            # ins: Instruction | Label | Directive | None = None
            # try:
            #     ins = runner.get_iterator().get(pos)
            #     runner.__vm.add_breakpoint_by_instruction(ins, breakpoint)
            # except IndexError:
            #     pass
            # if isinstance(ins, Instruction):
            try:
                returned_value = self.run()
                returned_values.add(returned_value)
            except Exception as e:
                if isinstance(e, SmaliFlowError):
                    raise e
            # if ins is not None:
            #     runner.__vm.remove_breakpoint(breakpoint)

            for reg in self.__context.get_registers():
                if not reg.initialized:
                    continue
                if reg.name not in values:
                    values[reg.name] = set()
                if isinstance(reg.value.get(), AmbiguousValue):
                    for value in reg.value.get_ambiguous().get_values():
                        values[reg.name].add(copy.copy(value))
                else:
                    values[reg.name].add(copy.copy(reg.value))
        self.seek(orig_position)
        self.__context = orig_context

        # self.__breakpoints.remove(breakpoint)
        # for thread in threads:
        #     thread.join()

        # self.__vm.cache_ambiguous_values[cache_key] = (values, returned_values)
        for ins in breakpoints_ins:
            self.__service_breakpoints.remove_by_instruction(
                ins, breakpoint  # pyright: ignore[reportArgumentType]
            )
        self.__iterator.stop()
        # for pos in positions:
        #     try:
        #         ins = self.get_iterator().get(pos)
        #         self.__breakpoints.remove_by_instruction(
        #             ins, breakpoint
        #         )  # pyright: ignore[reportArgumentType]
        #     except IndexError:
        #         pass

        # values, returned_values = self.__vm.cache_ambiguous_values[cache_key]
        for reg_name, reg in values.items():
            if len(reg) == 1:
                self.set_register(reg_name, reg.pop())
            else:
                ambigious_value = AmbiguousValue()
                for value in reg:
                    ambigious_value.add_value(value)
                self.set_register(reg_name, ambigious_value)

        if len(returned_values) == 1:
            self.__returned_value = returned_values.pop()
        elif len(returned_values) > 1:
            ambigious_value = AmbiguousValue()
            for value in returned_values:
                if value is None:
                    value = RegisterValue(NoValue())
                ambigious_value.add_value(value)
            self.__returned_value = RegisterValue(ambigious_value)
        self.depth -= 1

    def _const(
        self,
        ins: (
            Const
            | Const4
            | Const16
            | ConstHigh16
            | ConstWide
            | ConstWide16
            | ConstWide32
            | ConstWideHigh16
        ),
    ):
        wide = isinstance(ins, (ConstWide, ConstWide16, ConstWide32, ConstWideHigh16))
        self.set_register(ins.reg1, ins.data, wide)

    def _const_string(self, ins: ConstString | ConstStringJumbo) -> None:
        self.set_register(ins.reg1, String.FrameworkClass()._init_(ins.data))

    def _const_class(self, ins: ConstClass) -> None:
        self.set_register(ins.reg1, UnknownValue())

    def _move(
        self,
        ins: (
            Move
            | MoveFrom16
            | Move16
            | MoveObject
            | MoveObjectFrom16
            | MoveObject16
            | MoveWide
            | MoveWide16
            | MoveWideFrom16
        ),
    ):
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        if reg2.has_value():
            value = reg2.value
        wide = isinstance(ins, (MoveWide, MoveWide16, MoveWideFrom16))
        self.set_register(ins.reg1, value, wide)

    def _math_int(
        self,
        ins: (
            AddInt
            | SubInt
            | MulInt
            | DivInt
            | RemInt
            | AndInt
            | OrInt
            | XorInt
            | ShlInt
            | ShrInt
            | UshrInt
        ),
        operation: Callable[[int, int], int],
    ) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        reg3 = self.__context.get_register(ins.reg3)
        if reg2.has_value() and reg3.has_value():
            if isinstance(reg2.value.get(), AmbiguousValue) and not isinstance(
                reg3.value.get(), AmbiguousValue
            ):
                value = AmbiguousValue()
                reg3_value = reg3.value.get_int()
                for v in reg2.value.get_ambiguous().get_values():
                    if v.is_unknown():
                        value.add_value(RegisterValue(UnknownValue()))
                    else:
                        value.add_value(
                            RegisterValue(hex(operation(v.get_int(), reg3_value)))
                        )
            elif isinstance(reg3.value.get(), AmbiguousValue) and not isinstance(
                reg2.value.get(), AmbiguousValue
            ):
                value = AmbiguousValue()
                reg2_value = reg2.value.get_int()
                for v in reg3.value.get_ambiguous().get_values():
                    if v.is_unknown():
                        value.add_value(RegisterValue(UnknownValue()))
                    else:
                        value.add_value(
                            RegisterValue(hex(operation(reg2_value, v.get_int())))
                        )
            else:
                value = RegisterValue(
                    hex(operation(reg2.value.get_int(), reg3.value.get_int()))
                )

        self.set_register(ins.reg1, value)

    def _math_int2(
        self,
        ins: NegInt | NotInt,
        operation: Callable[[int], int],
    ) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        if reg2.has_value():
            if isinstance(reg2.value.get(), AmbiguousValue):
                value = AmbiguousValue()
                for v in reg2.value.get_ambiguous().get_values():
                    if v.is_unknown():
                        value.add_value(RegisterValue(UnknownValue()))
                    else:
                        value.add_value(RegisterValue(hex(operation(v.get_int()))))
            else:
                value = RegisterValue(hex(operation(reg2.value.get_int())))

        self.set_register(ins.reg1, value)

    def _math_int_2addr(
        self,
        ins: (
            AddInt2Addr
            | SubInt2Addr
            | MulInt2Addr
            | DivInt2Addr
            | RemInt2Addr
            | AndInt2Addr
            | OrInt2Addr
            | XorInt2Addr
            | ShlInt2Addr
            | ShrInt2Addr
            | UshrInt2Addr
        ),
        operation: Callable[[int, int], int],
    ) -> None:
        value = UnknownValue()
        reg1 = self.__context.get_register(ins.reg1)
        reg2 = self.__context.get_register(ins.reg2)
        if reg1.has_value() and reg2.has_value():
            if isinstance(reg1.value.get(), AmbiguousValue) and not isinstance(
                reg2.value.get(), AmbiguousValue
            ):
                value = AmbiguousValue()
                reg2_value = reg2.value.get_int()
                for v in reg1.value.get_ambiguous().get_values():
                    if v.is_unknown():
                        value.add_value(RegisterValue(UnknownValue()))
                    else:
                        value.add_value(
                            RegisterValue(hex(operation(v.get_int(), reg2_value)))
                        )
            elif isinstance(reg2.value.get(), AmbiguousValue) and not isinstance(
                reg1.value.get(), AmbiguousValue
            ):
                value = AmbiguousValue()
                reg1_value = reg1.value.get_int()
                for v in reg2.value.get_ambiguous().get_values():
                    if v.is_unknown():
                        value.add_value(RegisterValue(UnknownValue()))
                    else:
                        value.add_value(
                            RegisterValue(hex(operation(reg1_value, v.get_int())))
                        )
            else:
                value = RegisterValue(
                    hex(operation(reg1.value.get_int(), reg2.value.get_int()))
                )

        self.set_register(ins.reg1, value)

    def _math_int_lit8(
        self,
        ins: (
            AddIntLit8
            | MulIntLit8
            | DivIntLit8
            | RemIntLit8
            | AndIntLit8
            | OrIntLit8
            | XorIntLit8
            | RsubIntLit8
            | ShlIntLit8
            | ShrIntLit8
            | UshrIntLit8
        ),
        operation: Callable[[int, int], int],
    ) -> None:
        self._math_int_lit16(ins, operation)

    def _math_int_lit16(
        self,
        ins: (
            AddIntLit16
            | MulIntLit16
            | DivIntLit16
            | RemIntLit16
            | AndIntLit16
            | OrIntLit16
            | XorIntLit16
            | RsubInt
            | AddIntLit8
            | MulIntLit8
            | DivIntLit8
            | RemIntLit8
            | AndIntLit8
            | OrIntLit8
            | XorIntLit8
            | RsubIntLit8
            | ShlIntLit8
            | ShrIntLit8
            | UshrIntLit8
        ),
        operation: Callable[[int, int], int],
    ) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        if reg2.has_value():
            if isinstance(reg2.value.get(), AmbiguousValue):
                value = AmbiguousValue()
                for v in reg2.value.get_ambiguous().get_values():
                    if v.is_unknown():
                        value.add_value(RegisterValue(UnknownValue()))
                    else:
                        value.add_value(
                            RegisterValue(
                                hex(operation(v.get_int(), int(ins.data, 16)))
                            )
                        )
            else:
                value = RegisterValue(
                    hex(operation(reg2.value.get_int(), int(ins.data, 16)))
                )

        self.set_register(ins.reg1, value)

    def _math_double(
        self,
        ins: AddDouble | SubDouble | MulDouble | DivDouble | RemDouble,
        operation: Callable[[float, float], float],
    ) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        reg3 = self.__context.get_register(ins.reg3)
        if reg2.has_value() and reg3.has_value():
            value = RegisterValue(
                float.hex(operation(reg2.value.get_double(), reg3.value.get_double()))
            )

        self.set_register(ins.reg1, value)

    def _math_double_2addr(
        self,
        ins: (
            AddDouble2Addr
            | SubDouble2Addr
            | MulDouble2Addr
            | DivDouble2Addr
            | RemDouble2Addr
        ),
        operation: Callable[[float, float], float],
    ) -> None:
        value = UnknownValue()
        reg1 = self.__context.get_register(ins.reg1)
        reg2 = self.__context.get_register(ins.reg2)
        if reg1.has_value() and reg2.has_value():
            if isinstance(reg1.value.get(), AmbiguousValue) and not isinstance(
                reg2.value.get(), AmbiguousValue
            ):
                value = AmbiguousValue()
                reg2_value = reg2.value.get_double()
                for v in reg1.value.get_ambiguous().get_values():
                    if v.is_unknown():
                        value.add_value(RegisterValue(UnknownValue()))
                    else:
                        value.add_value(
                            RegisterValue(
                                float.hex(operation(v.get_double(), reg2_value))
                            )
                        )
            elif isinstance(reg2.value.get(), AmbiguousValue) and not isinstance(
                reg1.value.get(), AmbiguousValue
            ):
                value = AmbiguousValue()
                reg1_value = reg1.value.get_double()
                for v in reg2.value.get_ambiguous().get_values():
                    if v.is_unknown():
                        value.add_value(RegisterValue(UnknownValue()))
                    else:
                        value.add_value(
                            RegisterValue(
                                float.hex(operation(reg1_value, v.get_double()))
                            )
                        )
            else:
                value = RegisterValue(
                    float.hex(
                        operation(reg1.value.get_double(), reg2.value.get_double())
                    )
                )

        self.set_register(ins.reg1, value)

    def _math_double2(
        self,
        ins: NegDouble,
        operation: Callable[[float], float],
    ) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        if reg2.has_value():
            if isinstance(reg2.value.get(), AmbiguousValue):
                value = AmbiguousValue()
                for v in reg2.value.get_ambiguous().get_values():
                    if v.is_unknown():
                        value.add_value(RegisterValue(UnknownValue()))
                    else:
                        value.add_value(
                            RegisterValue(float.hex(operation(v.get_double())))
                        )
            else:
                value = RegisterValue(float.hex(operation(reg2.value.get_double())))

        self.set_register(ins.reg1, value)

    def _math_long(
        self,
        ins: (
            AddLong
            | SubLong
            | MulLong
            | DivLong
            | RemLong
            | AndLong
            | OrLong
            | XorLong
            | ShlLong
            | ShrLong
            | UshrLong
        ),
        operation: Callable[[int, int], int],
    ) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        reg3 = self.__context.get_register(ins.reg3)
        if reg2.has_value() and reg3.has_value():
            value = RegisterValue(
                hex(operation(reg2.value.get_long(), reg3.value.get_long()))
            )

        self.set_register(ins.reg1, value)

    def _math_long2(
        self,
        ins: NegLong | NotLong,
        operation: Callable[[int], int],
    ) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        if reg2.has_value():
            value = RegisterValue(hex(operation(reg2.value.get_long())))

        self.set_register(ins.reg1, value)

    def _math_long_2addr(
        self,
        ins: (
            AddLong2Addr
            | SubLong2Addr
            | MulLong2Addr
            | DivLong2Addr
            | RemLong2Addr
            | AndLong2Addr
            | OrLong2Addr
            | XorLong2Addr
            | ShlLong2Addr
            | ShrLong2Addr
            | UshrLong2Addr
        ),
        operation: Callable[[int, int], int],
    ) -> None:
        value = UnknownValue()
        reg1 = self.__context.get_register(ins.reg1)
        reg2 = self.__context.get_register(ins.reg2)
        if reg1.has_value() and reg2.has_value():
            value = RegisterValue(
                hex(operation(reg1.value.get_long(), reg2.value.get_long()))
            )

        self.set_register(ins.reg1, value)

    def _math_float(
        self,
        ins: AddFloat | SubFloat | MulFloat | DivFloat | RemFloat,
        operation: Callable[[float, float], float],
    ) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        reg3 = self.__context.get_register(ins.reg3)
        if reg2.has_value() and reg3.has_value():
            value = RegisterValue(
                float.hex(operation(reg2.value.get_float(), reg3.value.get_float()))
            )

        self.set_register(ins.reg1, value)

    def _math_float2(
        self,
        ins: NegFloat,
        operation: Callable[[float], float],
    ) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        if reg2.has_value():
            value = RegisterValue(float.hex(operation(reg2.value.get_float())))

        self.set_register(ins.reg1, value)

    def _math_float_2addr(
        self,
        ins: (
            AddFloat2Addr
            | SubFloat2Addr
            | MulFloat2Addr
            | DivFloat2Addr
            | RemFloat2Addr
        ),
        operation: Callable[[float, float], float],
    ) -> None:
        value = UnknownValue()
        reg1 = self.__context.get_register(ins.reg1)
        reg2 = self.__context.get_register(ins.reg2)
        if reg1.has_value() and reg2.has_value():
            value = RegisterValue(
                float.hex(operation(reg1.value.get_float(), reg2.value.get_float()))
            )

        self.set_register(ins.reg1, value)

    def _double_to_int(self, ins: DoubleToInt) -> None:
        value = UnknownValue()
        reg2 = self.__context.get_register(ins.reg2)
        if reg2.has_value():
            value_double = reg2.value.get_double()
            if not math.isnan(value_double) and not math.isinf(value_double):
                value = RegisterValue(hex(int(value_double)))
        self.set_register(ins.reg1, value)

    def _if(self, ins: Instruction22t) -> None:
        # with open("/home/kiber/smaliflow/log.txt", "a") as f:
        #     f.write(str(ins) + "\n")
        reg1 = self.__context.get_register(ins.reg1)
        if not reg1.has_value() or isinstance(reg1.value.get(), AmbiguousValue):
            # if we already visited this block, we don't want to process it again because it will lead to infinite loop in case of ambiguous or unknown values
            # if ins in self._visited_blocks:
            #     # we need to update visited lines because we need to skip the block
            #     self._visited_lines.update(self._visited_blocks[ins])
            #     return
            # visited_lines = set()
            # self._visited_blocks[ins] = visited_lines
            self._process_ambiguous_registers(
                ([self.__iterator.index(ins.label), self.__iterator.tell()])
            )
            return
        reg2 = self.__context.get_register(ins.reg2)
        if not reg2.has_value() or isinstance(reg2.value.get(), AmbiguousValue):
            # if we already visited this block, we don't want to process it again because it will lead to infinite loop in case of ambiguous or unknown values
            # if ins in self._visited_blocks:
            #     # we need to update visited lines because we need to skip the block
            #     self._visited_lines.update(self._visited_blocks[ins])
            #     return
            # visited_lines = set()
            # self._visited_blocks[ins] = visited_lines
            self._process_ambiguous_registers(
                ([self.__iterator.index(ins.label), self.__iterator.tell()]),
            )
            return
        # self._visited_blocks[ins] = set()
        condition = False
        if isinstance(ins, IfEq):
            condition = reg1.value.get() == reg2.value.get()
        elif isinstance(ins, IfNe):
            condition = reg1.value.get() != reg2.value.get()
        elif isinstance(ins, IfLt):
            condition = reg1.value.get_int() < reg2.value.get_int()
        elif isinstance(ins, IfGe):
            condition = reg1.value.get_int() >= reg2.value.get_int()
        elif isinstance(ins, IfGt):
            condition = reg1.value.get_int() > reg2.value.get_int()
        elif isinstance(ins, IfLe):
            condition = reg1.value.get_int() <= reg2.value.get_int()
        else:
            raise UnsupportedInstructionError(ins)

        if condition:
            cur_pos = self.__iterator.tell()
            new_pos = self.__iterator.index(ins.label)
            self.__iterator.seek(new_pos)
            self.run()
            self.__iterator.seek(cur_pos)
            # block = method.blocks[ins.label.name]
            # self.__run(block)
        # else:
        #     pass

        # if self._branch == (self._position, condition):
        #     self._branch = None
        # else:
        #     self._branch = (self._position, condition)

        # if condition:
        #     current_idx = self._position
        #     self.__seek_to(ins.label)
        #     self._analyze()
        #     self._position = current_idx

        # if self._position in self._branches:
        #     branch_list = self._branches[self._position]
        #     if len(branch_list[0]) > 0 and len(branch_list[1]) > 0:
        #         for idx in branch_list[0]:
        #             self._visited_lines.add(idx)
        #         for idx in branch_list[1]:
        #             self._visited_lines.add(idx)
        #         idx = self.__find_instruction(ins.label)
        #         if idx != -1:
        #             self._visited_lines.add(idx)

    def _ifz(self, ins: Instruction21t) -> None:
        # with open("/home/kiber/smaliflow/log.txt", "a") as f:
        #     f.write(str(ins) + "\n")
        reg1 = self.__context.get_register(ins.reg1)
        if not reg1.has_value() or isinstance(reg1.value.get(), AmbiguousValue):
            # if we already visited this block, we don't want to process it again because it will lead to infinite loop in case of ambiguous or unknown values
            # if ins in self._visited_blocks:
            #     # we need to update visited lines because we need to skip the block
            #     self._visited_lines.update(self._visited_blocks[ins])
            #     return
            # visited_lines = set()
            # self._visited_blocks[ins] = visited_lines
            self._process_ambiguous_registers(
                ([self.__iterator.index(ins.label), self.__iterator.tell()])
            )
            return
        condition = False
        if isinstance(ins, IfEqz):
            if reg1.value.is_null():
                condition = True
            elif reg1.value.is_int():
                condition = reg1.value.get_int() == 0
        elif isinstance(ins, IfNez):
            if reg1.value.is_null():
                condition = False
            elif reg1.value.is_int():
                condition = reg1.value.get_int() != 0
        elif isinstance(ins, IfLtz):
            condition = reg1.value.get_int() < 0
        elif isinstance(ins, IfGez):
            condition = reg1.value.get_int() >= 0
        elif isinstance(ins, IfGtz):
            condition = reg1.value.get_int() > 0
        elif isinstance(ins, IfLez):
            condition = reg1.value.get_int() <= 0
        else:
            raise UnsupportedInstructionError(ins)
        if condition:
            cur_pos = self.__iterator.tell()
            new_pos = self.__iterator.index(ins.label)
            self.__iterator.seek(new_pos)
            self.run()
            self.__iterator.seek(cur_pos)
            # if self._branch == (self._position, True):
            #     self._branch = None
            # else:
            #     self._branch = (self._position, True)
            # current_idx = self._position
            # self.__seek_to(ins.label)
            # self._analyze()
            # self._position = current_idx
        # else:
        #     if self._branch == (self._position, False):
        #         self._branch = None
        #     else:
        #         self._branch = (self._position, False)

        # if self._position in self._branches:
        #     branch_list = self._branches[self._position]
        #     if len(branch_list[0]) > 0 and len(branch_list[1]) > 0:
        #         for idx in branch_list[0]:
        #             self._visited_lines.add(idx)
        #         for idx in branch_list[1]:
        #             self._visited_lines.add(idx)
        #         idx = self.__find_instruction(ins.label)
        #         if idx != -1:
        #             self._visited_lines.add(idx)

    def _goto(self, ins: Goto | Goto16 | Goto32) -> None:
        # cur_pos = self.__iterator.tell()
        new_pos = self.__iterator.index(ins.label)

        def breakpoint(
            context: RegistersContext, ins: Instruction | Label | Directive
        ) -> bool | None:
            return False

        self.__breakpoints.add_by_instruction(ins, breakpoint)
        self.__iterator.seek(new_pos)
        self.run()
        self.__breakpoints.remove_by_instruction(ins, breakpoint)
        # self.__iterator.seek(cur_pos)
        # current_idx = self._position
        # self.__seek_to(ins.label)
        # self._analyze()
        # self._position = current_idx

    def _instance_of(self, ins: InstanceOf) -> None:
        self.set_register(ins.reg1, RegisterValue(UnknownValue()))

    def _new_array(self, ins: NewArray) -> None:
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            size = reg2.value.get_int()
            value = Array(size, ins.data)
        self.set_register(ins.reg1, value)

    def _aput(
        self,
        ins: (
            Aput | AputWide | AputObject | AputBoolean | AputByte | AputChar | AputShort
        ),
    ) -> None:
        reg1 = self.__context.get_register(ins.reg1)
        reg2 = self.__context.get_register(ins.reg2)
        reg3 = self.__context.get_register(ins.reg3)
        value = RegisterValue(UnknownValue())
        if not reg2.has_value() or not reg3.has_value():
            return
        if reg1.has_value():
            value = reg1.value

        arr = reg2.value.get_array()
        idx = reg3.value.get_int()
        arr[idx] = value

    def _invoke(
        self,
        ins: (
            InvokeVirtual
            | InvokeStatic
            | InvokeSuper
            | InvokeDirect
            | InvokeInterface
            | InvokePolymorphic
            | InvokeCustom
            | InvokeVirtualRange
            | InvokeStaticRange
            | InvokeSuperRange
            | InvokeDirectRange
            | InvokeInterfaceRange
            | InvokePolymorphicRange
            | InvokeCustomRange
        ),
    ) -> None:
        #! TODO
        # return
        args: list[RegisterValue] = []
        regs = ins.registers
        # prevent recursion calls
        if ins.data in self._invokes_stack:
            return
        self._invokes_stack.append(ins.data)
        is_static = isinstance(ins, (InvokeStatic, InvokeStaticRange))
        if not is_static:
            # remove the first register because it's the instance
            regs = regs[1:]
        for reg in regs:
            reg = self.__context.get_register(reg)
            if reg.has_value():
                args.append(reg.value)
            else:
                args.append(RegisterValue(UnknownValue()))
        value: RegisterValue | None = None
        clazz: Class | None = None
        if is_static:
            clazz = self.__vm.load_class(ins.class_name)
        else:
            reg = self.__context.get_register(ins.registers[0])
            if reg.has_value() and reg.value.is_class():
                clazz = reg.value.get_class()
        # if isinstance(clazz, BaseFrameworkClass):
        #     method_name = method_signature.split("(")[0]
        #     value = clazz.invoke_method(method_name, *args)
        # else:

        if clazz is not None:
            # if is_static:
            #     if isinstance(clazz, BaseFrameworkClass):
            #         method_name = method_signature.split("(")[0]
            #         if clazz.has_method(method_name):
            #             value = clazz.invoke_method(method_name, *args)
            #         else:
            #             value = RegisterValue(UnknownValue())
            #     else:
            #         clazz = cast(Class, clazz)
            #         method = clazz.get_method(method_signature)
            #         if (
            #             method is not None
            #             and not method.is_abstract()
            #             and not method.is_native()
            #         ):
            #             runner = MethodRunner(method, self.__vm, self.__breakpoints)
            #             value = runner.run(*args)
            #         else:
            #             value = RegisterValue(UnknownValue())
            # else:
            if isinstance(clazz, BaseFrameworkClass):
                method_name = ins.method_signature.split("(")[0]
                if clazz.has_method(method_name):
                    value = clazz.invoke_method(method_name, *args)
                else:
                    value = RegisterValue(UnknownValue())
            else:
                clazz = cast(Class, clazz)
                method = clazz.get_method(ins.method_signature)
                if (
                    method is not None
                    and not method.is_abstract()
                    and not method.is_native()
                ):
                    runner = MethodRunner(
                        method, self.__vm, self.__breakpoints, self._invokes_stack
                    )
                    value = runner.run(*args)
                else:
                    value = RegisterValue(UnknownValue())
        else:
            value = RegisterValue(UnknownValue())

        if value is not None:
            self.__last_instruction_result = value.get()

        del self._invokes_stack[self._invokes_stack.index(ins.data)]

    def _move_result(
        self, ins: MoveResult | MoveResultWide | MoveResultObject | MoveException
    ) -> None:
        value = UnknownValue()
        if self.__last_instruction_result is not None:
            value = RegisterValue(self.__last_instruction_result)
            self.__last_instruction_result = None
        wide = isinstance(ins, MoveResultWide)
        self.set_register(ins.reg1, value, wide)

    def _array_length(self, ins: ArrayLength) -> None:
        reg2 = self.__context.get_register(ins.reg2)
        value = UnknownValue()
        if reg2.has_value() and not reg2.value.is_null():
            if not reg2.value.is_array():
                logging.warning("Value is not an array, skipping")
                return
            value = RegisterValue(hex(len(reg2.value.get_array())))
        self.set_register(ins.reg1, value)

    def _new_instance(self, ins: NewInstance) -> None:
        value = UnknownValue()
        clazz = self.__vm.load_class(ins.data)
        if clazz is not None:
            value = clazz
        self.set_register(ins.reg1, RegisterValue(value))

    def _filled_new_array(self, ins: FilledNewArray | FilledNewArrayRange) -> None:
        values: list[RegisterValue] = []
        for reg in ins.registers:
            reg = self.__context.get_register(reg)
            if reg.has_value():
                values.append(reg.value)
            else:
                # logger.debug(
                #     f"[filled-new-array] Source register {reg.name} does not have a value"
                # )
                values.append(RegisterValue(UnknownValue()))
        arr = Array(len(values), ins.data)
        for i, value in enumerate(values):
            arr[i] = value
        self.__last_instruction_result = arr

    def _fill_array_data(self, ins: FillArrayData) -> None:
        reg1 = self.__context.get_register(ins.reg1)
        if not reg1.has_value():
            return
        arr = reg1.value.get_array()
        cur_pos = self.__iterator.tell()
        directive_pos = self.__iterator.index(ins.label)
        self.__iterator.seek(directive_pos)
        array_data = next(self.__iterator)
        self.__iterator.seek(cur_pos)
        if not isinstance(array_data, directives.ArrayData):
            raise ValueError("Invalid array-data instruction")
        for idx, value in enumerate(array_data.values):
            arr[idx] = RegisterValue(value)

    def _packed_switch(self, ins: instructions.PackedSwitch) -> None:
        reg1 = self.__context.get_register(ins.reg1)
        cur_pos = self.__iterator.tell()
        directive_pos = self.__iterator.index(ins.label)
        self.__iterator.seek(directive_pos)
        packed_switch = next(self.__iterator)
        self.__iterator.seek(cur_pos)
        if not isinstance(packed_switch, directives.PackedSwitch):
            raise ValueError("Invalid packed-switch instruction")
        if not reg1.has_value():
            positions: list[int] = []
            for label in packed_switch.labels.values():
                positions.append(self.__iterator.index(label))
            positions.append(cur_pos)
            self._process_ambiguous_registers(positions)
            # registers_values: dict[str, set[RegisterValue]] = {}
            # is_returned = False
            # for label in packed_switch.labels.values():
            #     context = copy.copy(self.__context)
            #     runner = InstructionsRunner(self.__iterator.get_instructions(), context)
            #     pos = self.__iterator.index(label)
            #     runner.seek(pos)
            #     returned_value = runner.run()

            #     for reg in context.get_registers():
            #         if reg.name not in registers_values:
            #             registers_values[reg.name] = set()
            #         registers_values[reg.name].add(copy.copy(reg.value))
            #     if self._returned:
            #         is_returned = True
            #         self._returned = False
            # if is_returned:
            #     self._returned = True
            # for reg_name, reg in registers_values.items():
            #     if len(reg) == 1:
            #         self.set_register(reg_name, reg.pop())
            #     else:
            #         ambigious_value = AmbiguousValue()
            #         for value in reg:
            #             ambigious_value.add_value(value)
            #         self.set_register(reg_name, ambigious_value)
            return

        if reg1.value.get_int() in packed_switch.labels:
            switch = packed_switch.labels[reg1.value.get_int()]
            new_pos = self.__iterator.index(switch)
            self.__iterator.seek(new_pos)
            self.run()

    def _sparse_switch(self, ins: instructions.SparseSwitch):
        reg1 = self.__context.get_register(ins.reg1)
        cur_pos = self.__iterator.tell()
        directive_pos = self.__iterator.index(ins.label)
        self.__iterator.seek(directive_pos)
        sparse_switch = next(self.__iterator)
        self.__iterator.seek(cur_pos)
        if not isinstance(sparse_switch, directives.SparseSwitch):
            raise ValueError("Invalid sparse-switch instruction")
        if not reg1.has_value():
            positions: list[int] = []
            for label in sparse_switch.labels.values():
                positions.append(self.__iterator.index(label))
            positions.append(cur_pos)
            self._process_ambiguous_registers(positions)
            # registers_values: dict[str, set[RegisterValue]] = {}
            # is_returned = False
            # for label in sparse_switch.labels.values():
            #     self.__seek_to(label)
            #     self._analyze()
            #     for reg in self.__context.get_registers():
            #         if reg.name not in registers_values:
            #             registers_values[reg.name] = set()
            #         registers_values[reg.name].add(copy.copy(reg.value))
            #     if self._returned:
            #         is_returned = True
            #         self._returned = False
            # if is_returned:
            #     self._returned = True
            # for reg_name, reg in registers_values.items():
            #     if len(reg) == 1:
            #         self.set_register(reg_name, reg.pop())
            #     else:
            #         ambigious_value = AmbiguousValue()
            #         for value in reg:
            #             ambigious_value.add_value(value)
            #         self.set_register(reg_name, ambigious_value)
            return

        if reg1.value.get_int() in sparse_switch.labels:
            switch = sparse_switch.labels[reg1.value.get_int()]
            new_pos = self.__iterator.index(switch)
            self.__iterator.seek(new_pos)
            self.run()

    def _cmplg_float(self, ins: CmplFloat | CmpgFloat):
        reg2 = self.__context.get_register(ins.reg2)
        reg3 = self.__context.get_register(ins.reg3)
        value = RegisterValue(UnknownValue())
        if reg2.has_value() and reg3.has_value():
            int_value: int
            value1 = reg2.value.get_float()
            value2 = reg3.value.get_float()
            if math.isnan(value1) or math.isnan(value2):
                if isinstance(ins, CmplFloat):
                    int_value = -1
                elif isinstance(ins, CmpgFloat):
                    int_value = 1
                else:
                    raise UnsupportedInstructionError(ins.name)
            elif value1 == value2:
                int_value = 0
            elif value1 < value2:
                int_value = -1
            else:
                int_value = 1
            value = RegisterValue(hex(int_value))

        self.set_register(ins.reg1, value)

    def _cmplg_double(self, ins: CmplDouble | CmpgDouble):
        reg2 = self.__context.get_register(ins.reg2)
        reg3 = self.__context.get_register(ins.reg3)
        value = RegisterValue(UnknownValue())
        if reg2.has_value() and reg3.has_value():
            int_value: int
            value1 = reg2.value.get_double()
            value2 = reg3.value.get_double()
            if math.isnan(value1) or math.isnan(value2):
                if isinstance(ins, CmplDouble):
                    int_value = -1
                elif isinstance(ins, CmpgDouble):
                    int_value = 1
                else:
                    raise UnsupportedInstructionError(op)
            elif value1 == value2:
                int_value = 0
            elif value1 < value2:
                int_value = -1
            else:
                int_value = 1
            value = RegisterValue(hex(int_value))
        self.set_register(ins.reg1, value)

    def _cmp_long(self, ins: CmpLong):
        reg2 = self.__context.get_register(ins.reg2)
        reg3 = self.__context.get_register(ins.reg3)
        value = RegisterValue(UnknownValue())
        if reg2.has_value() and reg3.has_value():
            int_value: int
            value1 = reg2.value.get_long()
            value2 = reg3.value.get_long()
            if value1 == value2:
                int_value = 0
            elif value1 < value2:
                int_value = -1
            else:
                int_value = 1
            value = RegisterValue(hex(int_value))
        self.set_register(ins.reg1, value)

    def _aget(
        self,
        ins: (
            Aget | AgetWide | AgetObject | AgetBoolean | AgetByte | AgetChar | AgetShort
        ),
    ):
        reg2 = self.__context.get_register(ins.reg2)
        reg3 = self.__context.get_register(ins.reg3)
        value = RegisterValue(UnknownValue())
        if reg2.has_value() and reg3.has_value():
            arr = reg2.value.get_array()
            idx = reg3.value.get_int()
            value = arr[idx]
        self.set_register(ins.reg1, value)

    def _iget(
        self,
        ins: (
            Iget | IgetWide | IgetObject | IgetBoolean | IgetByte | IgetChar | IgetShort
        ),
    ):
        value = RegisterValue(UnknownValue())
        self.set_register(ins.reg1, value)

    def _iput(
        self,
        ins: (
            Iput | IputWide | IputObject | IputBoolean | IputByte | IputChar | IputShort
        ),
    ) -> None:
        return

    def _sget(
        self,
        ins: (
            Sget | SgetWide | SgetObject | SgetBoolean | SgetByte | SgetChar | SgetShort
        ),
    ) -> None:
        value = RegisterValue(UnknownValue())
        self.set_register(ins.reg1, value)

    def _sput(
        self,
        ins: (
            Sput | SputWide | SputObject | SputBoolean | SputByte | SputChar | SputShort
        ),
    ) -> None:
        return
        # class_name, field_signature = ins.data.split("->")
        # clazz = self.__vm.load_class(class_name)
        # if clazz is None:
        #     return
        # field_name = field_signature.split(":")[0]
        # field = clazz.find_field(field_name)
        # if field is None:
        #     return
        # reg = self.__context.get_register(ins.reg1)
        # if not reg.has_value():
        #     return
        # raise NotImplementedError()
        # field.value.set_value(reg.value.get())

    def _int_to_long(self, ins: IntToLong):
        reg2 = self.__context.get_register(ins.reg2)
        value = UnknownValue()
        if reg2.has_value():
            value = RegisterValue(hex(reg2.value.get_long()))
        self.set_register(ins.reg1, value)

    def _int_to_float(self, ins: IntToFloat):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(float.hex(float(reg2.value.get_int())))
        self.set_register(ins.reg1, value)

    def _int_to_double(self, ins: IntToDouble):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(float.hex(float(reg2.value.get_int())))
        self.set_register(ins.reg1, value)

    def _long_to_int(self, ins: LongToInt):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(hex(reg2.value.get_long()))
        self.set_register(ins.reg1, value)

    def _long_to_float(self, ins: LongToFloat):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(float.hex(float(reg2.value.get_long())))
        self.set_register(ins.reg1, value)

    def _long_to_double(self, ins: LongToDouble):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(float.hex(float(reg2.value.get_long())))
        self.set_register(ins.reg1, value)

    def _float_to_int(self, ins: FloatToInt):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(hex(int(reg2.value.get_float())))
        self.set_register(ins.reg1, value)

    def _float_to_long(self, ins: FloatToLong):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(hex(int(reg2.value.get_float())))
        self.set_register(ins.reg1, value)

    def _float_to_double(self, ins: FloatToDouble):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(float.hex(reg2.value.get_float()))
        self.set_register(ins.reg1, value)

    def _double_to_long(self, ins: DoubleToLong):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(hex(int(reg2.value.get_double())))
        self.set_register(ins.reg1, value)

    def _double_to_float(self, ins: DoubleToFloat):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(float.hex(reg2.value.get_double()))
        self.set_register(ins.reg1, value)

    def _int_to_byte(self, ins: IntToByte):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(hex(reg2.value.get_int() & 0xFF))
        self.set_register(ins.reg1, value)

    def _int_to_char(self, ins: IntToChar):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(hex(reg2.value.get_int() & 0xFFFF))
        self.set_register(ins.reg1, value)

    def _int_to_short(self, ins: IntToShort):
        reg2 = self.__context.get_register(ins.reg2)
        value = RegisterValue(UnknownValue())
        if reg2.has_value():
            value = RegisterValue(hex(reg2.value.get_int() & 0xFFFF))
        self.set_register(ins.reg1, value)

    def _const_method_handle(self, ins: ConstMethodHandle):
        self.set_register(ins.reg1, RegisterValue(UnknownValue()))

    def _const_method_type(self, ins: ConstMethodType):
        self.set_register(ins.reg1, RegisterValue(UnknownValue()))


class MethodRunner:
    context: RegistersContext
    __method: Method
    __vm: "Vm"
    __breakpoints: Breakpoints

    def __init__(
        self,
        method: Method,
        vm: "Vm",
        breakpoints: Breakpoints,
        invokes_stack: list[str] | None = None,
    ) -> None:
        self.__method = method
        self.__vm = vm
        self.__breakpoints = breakpoints
        self._invokes_stack = invokes_stack if invokes_stack is not None else []

    def __initialize(self):
        registers: list[Register] = []
        reg_num: int = 0
        if "static" not in self.__method.get_flags():
            reg = Register("p0")
            reg.value = RegisterValue(UnknownValue())
            registers.append(reg)
            reg_num += 1

        for param in self.__method.get_parameters_types():
            reg = Register(f"p{reg_num}")
            reg.value = RegisterValue(UnknownValue())
            registers.append(reg)
            if param in ["J", "D"]:
                reg_num += 1
                reg2 = Register(f"p{reg_num}")
                reg2.value = RegisterValue(UnknownValue())
                registers.append(reg2)
            reg_num += 1

        for i in range(self.__method.get_registers_count() - len(registers)):
            reg = Register(f"v{i}")
            reg.value = RegisterValue(UnknownValue())
            registers.append(reg)

        self.context = RegistersContext(registers)

    def run(self, *args: RegisterValue) -> RegisterValue | None:
        # with open("/home/kiber/smaliflow/log.txt", "a") as f:
        #     # print(f"MethodRunner: {self.__method.get_full_signature()}")
        #     f.write(f"MethodRunner: {self.__method.get_full_signature()}\n")
        self.__initialize()

        registers = self.context.get_registers()
        if "static" not in self.__method.get_flags():
            registers = registers[1:]
        for i, arg in enumerate(args):
            reg = registers[i]
            reg.value = arg
        runner = InstructionsRunner(
            self.__method.get_instructions(),
            self.context,
            self.__vm,
            self.__method,
            self.__breakpoints,
            self._invokes_stack,
        )
        return runner.run()
        # for ins in self.__iterator:
        #     if self.__ambiguos_processing:
        #         self.__iterator.save_visited_position()
        #     self.__stack.append(ins)
        #     previous_instruction_result = self.__last_instruction_result
        #     # self._write_branch()
        #     if isinstance(
        #         ins,
        #         (
        #             Label,
        #             Directive,
        #             MonitorEnter,
        #             MonitorExit,
        #             CheckCast,
        #             InstanceOf,
        #             Nop,
        #         ),
        #     ):
        #         pass  # type: ignore
        #     # self._trigger_breakpoint(ins)
        #     elif isinstance(ins, (ReturnVoid, Return, ReturnObject, ReturnWide)):
        #         # self._branch = None
        #         # self._returned = True
        #         self.__iterator.stop()
        #         if isinstance(ins, (Return, ReturnObject, ReturnWide)):
        #             reg = self.__context.get_register(ins.reg1)
        #             if reg.initialized:
        #                 self.__returned_value = reg.value
        #     elif isinstance(ins, Throw):
        #         self._branch = None
        #         self._thrown = True
        #     elif isinstance(
        #         ins,
        #         (
        #             Const,
        #             Const4,
        #             Const16,
        #             ConstHigh16,
        #             ConstWide,
        #             ConstWide16,
        #             ConstWide32,
        #             ConstWideHigh16,
        #         ),
        #     ):
        #         self._const(ins)
        #     elif isinstance(ins, (ConstString, ConstStringJumbo)):
        #         self._const_string(ins)
        #     elif isinstance(ins, ConstClass):
        #         self._const_class(ins)
        #     elif isinstance(
        #         ins,
        #         (
        #             Move,
        #             MoveFrom16,
        #             Move16,
        #             MoveObject,
        #             MoveObjectFrom16,
        #             MoveObject16,
        #             MoveWide,
        #             MoveWide16,
        #             MoveWideFrom16,
        #         ),
        #     ):
        #         self._move(ins)
        #     elif isinstance(ins, Instruction22t):
        #         self._if(ins)
        #     elif isinstance(ins, Instruction21t):
        #         self._ifz(ins)
        #     elif isinstance(ins, (Goto, Goto16, Goto32)):
        #         self._goto(ins)
        #     elif isinstance(ins, AddInt):
        #         self._math_int(ins, lambda x, y: x + y)
        #     elif isinstance(ins, SubInt):
        #         self._math_int(ins, lambda x, y: x - y)
        #     elif isinstance(ins, MulInt):
        #         self._math_int(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivInt):
        #         self._math_int(ins, lambda x, y: x // y)
        #     elif isinstance(ins, RemInt):
        #         self._math_int(ins, lambda x, y: x % y)
        #     elif isinstance(ins, AddDouble):
        #         self._math_double(ins, lambda x, y: x + y)
        #     elif isinstance(ins, SubDouble):
        #         self._math_double(ins, lambda x, y: x - y)
        #     elif isinstance(ins, MulDouble):
        #         self._math_double(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivDouble):
        #         self._math_double(ins, lambda x, y: x / y)
        #     elif isinstance(ins, RemDouble):
        #         self._math_double(ins, lambda x, y: x % y)
        #     elif isinstance(ins, NewArray):
        #         self._new_array(ins)
        #     elif isinstance(
        #         ins,
        #         (
        #             Aput,
        #             AputWide,
        #             AputObject,
        #             AputBoolean,
        #             AputByte,
        #             AputChar,
        #             AputShort,
        #         ),
        #     ):
        #         self._aput(ins)
        #     elif isinstance(
        #         ins,
        #         (
        #             InvokeVirtual,
        #             InvokeStatic,
        #             InvokeSuper,
        #             InvokeDirect,
        #             InvokeInterface,
        #             InvokePolymorphic,
        #             InvokeCustom,
        #             InvokeVirtualRange,
        #             InvokeStaticRange,
        #             InvokeSuperRange,
        #             InvokeDirectRange,
        #             InvokeInterfaceRange,
        #             InvokePolymorphicRange,
        #             InvokeCustomRange,
        #         ),
        #     ):
        #         self._invoke(ins)
        #     elif isinstance(
        #         ins, (MoveResult, MoveResultObject, MoveResultWide, MoveException)
        #     ):
        #         self._move_result(ins)
        #     elif isinstance(ins, ArrayLength):
        #         self._array_length(ins)
        #     elif isinstance(ins, NewInstance):
        #         self._new_instance(ins)
        #     elif isinstance(ins, (FilledNewArray, FilledNewArrayRange)):
        #         self._filled_new_array(ins)
        #     elif isinstance(ins, FillArrayData):
        #         self._fill_array_data(ins)
        #     elif isinstance(ins, PackedSwitch):
        #         self._packed_switch(ins)
        #     elif isinstance(ins, SparseSwitch):
        #         self._sparse_switch(ins)
        #     elif isinstance(ins, (CmplFloat, CmpgFloat)):
        #         self._cmplg_float(ins)
        #     elif isinstance(ins, (CmplDouble, CmpgDouble)):
        #         self._cmplg_double(ins)
        #     elif isinstance(ins, CmpLong):
        #         self._cmp_long(ins)
        #     elif isinstance(
        #         ins,
        #         (
        #             Aget,
        #             AgetWide,
        #             AgetObject,
        #             AgetBoolean,
        #             AgetByte,
        #             AgetChar,
        #             AgetShort,
        #         ),
        #     ):
        #         self._aget(ins)
        #     elif isinstance(
        #         ins,
        #         (
        #             Iget,
        #             IgetWide,
        #             IgetObject,
        #             IgetBoolean,
        #             IgetByte,
        #             IgetChar,
        #             IgetShort,
        #         ),
        #     ):
        #         self._iget(ins)
        #     elif isinstance(
        #         ins,
        #         (
        #             Iput,
        #             IputWide,
        #             IputObject,
        #             IputBoolean,
        #             IputByte,
        #             IputChar,
        #             IputShort,
        #         ),
        #     ):
        #         self._iput(ins)
        #     elif isinstance(
        #         ins,
        #         (
        #             Sget,
        #             SgetWide,
        #             SgetObject,
        #             SgetBoolean,
        #             SgetByte,
        #             SgetChar,
        #             SgetShort,
        #         ),
        #     ):
        #         self._sget(ins)
        #     elif isinstance(
        #         ins,
        #         (
        #             Sput,
        #             SputWide,
        #             SputObject,
        #             SputBoolean,
        #             SputByte,
        #             SputChar,
        #             SputShort,
        #         ),
        #     ):
        #         self._sput(ins)
        #     elif isinstance(ins, NegInt):
        #         self._math_int2(ins, lambda x: -x)
        #     elif isinstance(ins, NotInt):
        #         self._math_int2(ins, lambda x: ~x)
        #     elif isinstance(ins, NegLong):
        #         self._math_long2(ins, lambda x: -x)
        #     elif isinstance(ins, NotLong):
        #         self._math_long2(ins, lambda x: ~x)
        #     elif isinstance(ins, NegFloat):
        #         self._math_float2(ins, lambda x: -x)
        #     elif isinstance(ins, NegDouble):
        #         self._math_double2(ins, lambda x: -x)
        #     elif isinstance(ins, IntToLong):
        #         self._int_to_long(ins)
        #     elif isinstance(ins, IntToFloat):
        #         self._int_to_float(ins)
        #     elif isinstance(ins, IntToDouble):
        #         self._int_to_double(ins)
        #     elif isinstance(ins, LongToInt):
        #         self._long_to_int(ins)
        #     elif isinstance(ins, LongToFloat):
        #         self._long_to_float(ins)
        #     elif isinstance(ins, LongToDouble):
        #         self._long_to_double(ins)
        #     elif isinstance(ins, FloatToInt):
        #         self._float_to_int(ins)
        #     elif isinstance(ins, FloatToLong):
        #         self._float_to_long(ins)
        #     elif isinstance(ins, FloatToDouble):
        #         self._float_to_double(ins)
        #     elif isinstance(ins, DoubleToInt):
        #         self._double_to_int(ins)
        #     elif isinstance(ins, DoubleToLong):
        #         self._double_to_long(ins)
        #     elif isinstance(ins, DoubleToFloat):
        #         self._double_to_float(ins)
        #     elif isinstance(ins, IntToByte):
        #         self._int_to_byte(ins)
        #     elif isinstance(ins, IntToChar):
        #         self._int_to_char(ins)
        #     elif isinstance(ins, IntToShort):
        #         self._int_to_short(ins)
        #     elif isinstance(ins, AndInt):
        #         self._math_int(ins, lambda x, y: x & y)
        #     elif isinstance(ins, OrInt):
        #         self._math_int(ins, lambda x, y: x | y)
        #     elif isinstance(ins, XorInt):
        #         self._math_int(ins, lambda x, y: x ^ y)
        #     elif isinstance(ins, ShlInt):
        #         self._math_int(ins, lambda x, y: x << y)
        #     elif isinstance(ins, ShrInt):
        #         self._math_int(ins, lambda x, y: x >> y)
        #     elif isinstance(ins, UshrInt):
        #         self._math_int(ins, lambda x, y: (x % 0x100000000) >> y)
        #     elif isinstance(ins, AddLong):
        #         self._math_long(ins, lambda x, y: x + y)
        #     elif isinstance(ins, SubLong):
        #         self._math_long(ins, lambda x, y: x - y)
        #     elif isinstance(ins, MulLong):
        #         self._math_long(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivLong):
        #         self._math_long(ins, lambda x, y: x // y)
        #     elif isinstance(ins, RemLong):
        #         self._math_long(ins, lambda x, y: x % y)
        #     elif isinstance(ins, AndLong):
        #         self._math_long(ins, lambda x, y: x & y)
        #     elif isinstance(ins, OrLong):
        #         self._math_long(ins, lambda x, y: x | y)
        #     elif isinstance(ins, XorLong):
        #         self._math_long(ins, lambda x, y: x ^ y)
        #     elif isinstance(ins, ShlLong):
        #         self._math_long(ins, lambda x, y: x << y)
        #     elif isinstance(ins, ShrLong):
        #         self._math_long(ins, lambda x, y: x >> y)
        #     elif isinstance(ins, UshrLong):
        #         self._math_long(ins, lambda x, y: (x % 0x10000000000000000) >> y)
        #     elif isinstance(ins, AddFloat):
        #         self._math_float(ins, lambda x, y: x + y)
        #     elif isinstance(ins, SubFloat):
        #         self._math_float(ins, lambda x, y: x - y)
        #     elif isinstance(ins, MulFloat):
        #         self._math_float(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivFloat):
        #         self._math_float(ins, lambda x, y: x / y)
        #     elif isinstance(ins, RemFloat):
        #         self._math_float(ins, lambda x, y: x % y)
        #     elif isinstance(ins, AddInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x + y)
        #     elif isinstance(ins, SubInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x - y)
        #     elif isinstance(ins, MulInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x // y)
        #     elif isinstance(ins, RemInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x % y)
        #     elif isinstance(ins, AndInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x & y)
        #     elif isinstance(ins, OrInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x | y)
        #     elif isinstance(ins, XorInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x ^ y)
        #     elif isinstance(ins, ShlInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x << y)
        #     elif isinstance(ins, ShrInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: x >> y)
        #     elif isinstance(ins, UshrInt2Addr):
        #         self._math_int_2addr(ins, lambda x, y: (x % 0x100000000) >> y)
        #     elif isinstance(ins, AddLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x + y)
        #     elif isinstance(ins, SubLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x - y)
        #     elif isinstance(ins, MulLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x // y)
        #     elif isinstance(ins, RemLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x % y)
        #     elif isinstance(ins, AndLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x & y)
        #     elif isinstance(ins, OrLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x | y)
        #     elif isinstance(ins, XorLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x ^ y)
        #     elif isinstance(ins, ShlLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x << y)
        #     elif isinstance(ins, ShrLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: x >> y)
        #     elif isinstance(ins, UshrLong2Addr):
        #         self._math_long_2addr(ins, lambda x, y: (x % 0x10000000000000000) >> y)
        #     elif isinstance(ins, AddFloat2Addr):
        #         self._math_float_2addr(ins, lambda x, y: x + y)
        #     elif isinstance(ins, SubFloat2Addr):
        #         self._math_float_2addr(ins, lambda x, y: x - y)
        #     elif isinstance(ins, MulFloat2Addr):
        #         self._math_float_2addr(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivFloat2Addr):
        #         self._math_float_2addr(ins, lambda x, y: x / y)
        #     elif isinstance(ins, RemFloat2Addr):
        #         self._math_float_2addr(ins, lambda x, y: x % y)
        #     elif isinstance(ins, AddDouble2Addr):
        #         self._math_double_2addr(ins, lambda x, y: x + y)
        #     elif isinstance(ins, SubDouble2Addr):
        #         self._math_double_2addr(ins, lambda x, y: x - y)
        #     elif isinstance(ins, MulDouble2Addr):
        #         self._math_double_2addr(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivDouble2Addr):
        #         self._math_double_2addr(ins, lambda x, y: x / y)
        #     elif isinstance(ins, RemDouble2Addr):
        #         self._math_double_2addr(ins, lambda x, y: x % y)
        #     elif isinstance(ins, AddIntLit16):
        #         self._math_int_lit16(ins, lambda x, y: x + y)
        #     elif isinstance(ins, RsubInt):
        #         self._math_int_lit16(ins, lambda x, y: y - x)
        #     elif isinstance(ins, MulIntLit16):
        #         self._math_int_lit16(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivIntLit16):
        #         self._math_int_lit16(ins, lambda x, y: x // y)
        #     elif isinstance(ins, RemIntLit16):
        #         self._math_int_lit16(ins, lambda x, y: x % y)
        #     elif isinstance(ins, AndIntLit16):
        #         self._math_int_lit16(ins, lambda x, y: x & y)
        #     elif isinstance(ins, OrIntLit16):
        #         self._math_int_lit16(ins, lambda x, y: x | y)
        #     elif isinstance(ins, XorIntLit16):
        #         self._math_int_lit16(ins, lambda x, y: x ^ y)
        #     elif isinstance(ins, AddIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: x + y)
        #     elif isinstance(ins, RsubIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: y - x)
        #     elif isinstance(ins, MulIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: x * y)
        #     elif isinstance(ins, DivIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: x // y)
        #     elif isinstance(ins, RemIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: x % y)
        #     elif isinstance(ins, AndIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: x & y)
        #     elif isinstance(ins, OrIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: x | y)
        #     elif isinstance(ins, XorIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: x ^ y)
        #     elif isinstance(ins, ShlIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: x << y)
        #     elif isinstance(ins, ShrIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: x >> y)
        #     elif isinstance(ins, UshrIntLit8):
        #         self._math_int_lit8(ins, lambda x, y: (x % 0x100000000) >> y)
        #     elif isinstance(ins, ConstMethodHandle):
        #         self._const_method_handle(ins)
        #     elif isinstance(ins, ConstMethodType):
        #         self._const_method_type(ins)
        #     else:
        #         raise UnsupportedInstructionError(ins)

        #     if (
        #         previous_instruction_result is not None
        #         and previous_instruction_result == self.__last_instruction_result
        #     ):
        #         self.__last_instruction_result = None

        #     self.__stack.pop()

        # return self.__runner.run()


# class Vm:
#     def invoke(self, method: Method, *args):
#         runner = MethodRunner(method, *args)
#         return runner.run()

#     self.__runners.append(runner)
#     # param_registers = self.__init_registers(method)
#     # for i, arg in enumerate(args):
#     #     reg = param_registers[i]
#     #     reg.value = RegisterValue(arg)

#     self.__run()
#     # for block in method.blocks.values():
#     #     self.__run(block)

# def _write_branch(self):
#     if self._branch is not None:
#         branch_idx, branch_cond = self._branch
#         if branch_idx != self._position:
#             branch_list = [set(), set()]
#             if branch_idx not in self._branches:
#                 self._branches[branch_idx] = branch_list
#             else:
#                 branch_list = self._branches[branch_idx]
#             branch_cond_set = set()
#             branch_cond_idx = 0 if branch_cond else 1
#             if len(branch_list) == 2:
#                 branch_cond_set = branch_list[branch_cond_idx]
#             else:
#                 branch_list[branch_cond_idx] = branch_cond_set
#             branch_cond_set.add(self._position)

# def get_register(self, name: str) -> Register:
#     return self.context.get_register(name)

# @overload
# def set_register(
#     self,
#     name: str,
#     value: RegisterValue,
#     is_wide: bool = False,
# ) -> Register: ...

# @overload
# def set_register(
#     self,
#     name: str,
#     value: AmbiguousValue,
#     is_wide: bool = False,
# ) -> Register: ...

# @overload
# def set_register(
#     self,
#     name: str,
#     value: RegisterValueType,
#     is_wide: bool = False,
# ) -> Register: ...

# def set_register(
#     self,
#     name: str,
#     value: RegisterValueType | RegisterValue | AmbiguousValue,
#     is_wide: bool = False,
# ) -> Register:
#     return self.context.set_register(name, value, is_wide)


class Vm:
    __class_files: dict[str, str]
    __breakpoints: Breakpoints
    __classes_cache: OrderedDict[str, Type[Class]]
    __smali_dir: str | None = None
    cache_ambiguous_values: dict[
        tuple[int, ...],
        tuple[dict[str, set[RegisterValue]], set[RegisterValue | None]],
    ]

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, smali_dir: str) -> None: ...

    def __init__(self, smali_dir=None) -> None:
        self.cache_ambiguous_values = {}
        self.__classes_cache = OrderedDict()
        self.__class_files = {}
        self.__breakpoints = Breakpoints()
        self.__smali_dir = smali_dir

        # def __enter__(self) -> Self:
        if self.__smali_dir is not None:
            files = []
            for p, _, f in os.walk(self.__smali_dir):
                for file in f:
                    if file.endswith(".smali"):
                        files.append(os.path.join(p, file))

            with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                for class_name, path in executor.map(self.__preload_class, files):
                    self.__class_files[class_name] = path
        self.__preload_framework_classes()
        # return self

    # def __exit__(self, exc_type, exc_value, traceback) -> None:
    #     pass
    # self.__classes_cache.clear()
    # self.__class_files.clear()
    # del self.__breakpoints

    def __preload_framework_classes(self) -> None:
        framework_dir = os.path.join(os.path.dirname(__file__), "framework")
        for p, _d, f in os.walk(framework_dir):
            for file in f:
                if (
                    not file.endswith(".py")
                    or file == "base_framework_class.py"
                    or file == "__init__.py"
                ):
                    continue
                class_name = file[:-3]
                pkg = os.path.relpath(p, framework_dir)
                filepath = os.path.join(p, file)
                self.__class_files[f"L{pkg}/{class_name};"] = f"framework:{filepath}"

    def __preload_class(self, path: str) -> tuple[str, str]:
        class_header: str = ""
        with open(path, "r") as f:
            class_header = f.readline().strip()
        class_name = class_header.split(" ")[-1]
        return class_name, path

    @overload
    def invoke_method(self, method: Method, *args: Any) -> RegisterValue | None: ...

    @overload
    def invoke_method(
        self, method: str, parameter_types: list[str], class_name: str, *args: Any
    ) -> RegisterValue | None: ...

    def invoke_method(
        self, method, parameter_types, class_name, *args: Any
    ) -> RegisterValue | None:
        if isinstance(method, str):
            method_name = method
            if not isinstance(class_name, str):
                raise TypeError("class_name must be a string")
            clazz = self.load_class(class_name)
            if clazz is None:
                raise ClassNotFoundError(class_name)
            method = clazz.get_method((method_name, parameter_types))
            if method is None:
                raise MethodNotFoundError(class_name, method_name, parameter_types)
            # if len(methods) == 0:
            #     raise MethodNotFoundError(class_name, method_name, parameter_types)
            # if len(methods) > 1:
            #     raise MethodResolutionError(class_name, method_name, parameter_types)
            # method = methods[0]

        if method.is_abstract() or method.is_native():
            raise AbstractMethodError(method)

        runner = MethodRunner(method, self, self.__breakpoints)
        return runner.run(*args)

    def run_all_methods(self, clazz: Class) -> None:
        # prev_snapshot = None
        idx = 0
        for method in clazz.get_methods():
            # gc.collect()
            # if prev_snapshot is None:
            #     prev_snapshot = snapshot()
            # else:
            #     curr_snapshot = snapshot()
            #     new_objects = {k: v for k, v in curr_snapshot.items() if k not in prev_snapshot}
            #     persistent_objects = {k: v for k, v in prev_snapshot.items() if k in curr_snapshot and isinstance(v, Instruction)}
            #     prev_snapshot = None

            # print(f"run_all_methods [{idx}]: {method.get_full_signature()}")
            # yield idx
            idx += 1
            if method.is_abstract() or method.is_native():
                continue
            # with open("/home/kiber/smaliflow/log.txt", "a") as f:
            #     # print(f"run_all_methods: {method.get_full_signature()}")
            #     f.write(f"run_all_methods: {method.get_full_signature()}\n")
            runner = MethodRunner(method, self, self.__breakpoints)
            runner.run()

    def class_count(self) -> int:
        return len(self.__class_files)

    def iter_classes(self) -> Iterator[Class]:
        for class_name in self.__class_files:
            cls = self.load_class(class_name)
            if cls is not None:
                yield cls
                del cls

    # def create_class(self, class_name: str) -> SmaliClass | None:
    #     clazz: SmaliClass | None = None

    #     type_clazz = self.load_class(class_name)
    #     if type_clazz is not None:
    #         # filepath = self.__class_files[class_name]
    #         # if filepath.startswith("framework:"):
    #         #     clazz = type_clazz()
    #         # else:
    #         # with open(filepath) as f:
    #         #     clazz = type_clazz(f)
    #         clazz = type_clazz.new_instance()

    #     return clazz

    def load_class(self, class_name: str) -> Class | None:
        clazz: Type[Class] | None = None

        # if class_name in self.__classes:
        #     clazz = cloudpickle.loads(zlib.decompress(self.__classes[class_name]))
        # el
        if class_name in self.__class_files:
            # logging.debug(
            #     f"Loading class {class_name} because it was not found in cache"
            # )
            filepath = self.__class_files[class_name]
            load_class_method: Callable[[str], Type[Class] | None]
            class_path: str
            if filepath.startswith("framework:"):
                class_path = class_name
                load_class_method = self.__load_framework_class
                # clazz = self.__load_framework_class(class_name)
            else:
                # if filepath in self.__classes_cache:
                #     clazz = self.__classes_cache[filepath]
                #     self.__classes_cache.move_to_end(filepath)
                # else:
                class_path = filepath
                load_class_method = ClassParser.parse
                # clazz = ClassParser.parse(filepath)
                # if len(self.__classes_cache) >= 1000:
                #     self.__classes_cache.popitem(last=False)
                # self.__classes_cache[filepath] = clazz
            if filepath in self.__classes_cache:
                clazz = self.__classes_cache[filepath]
                self.__classes_cache.move_to_end(filepath)
            else:
                clazz = load_class_method(class_path)
                if clazz is not None:
                    if len(self.__classes_cache) >= 1000:
                        self.__classes_cache.popitem(last=False)
                    self.__classes_cache[filepath] = clazz

            # if clazz is not None:
            #     self.__classes[class_name] = zlib.compress(cloudpickle.dumps(clazz))

        if clazz is not None:
            return clazz()

    def __load_framework_class(self, class_name: str) -> Type[Class] | None:
        framework_dir = os.path.join(os.path.dirname(__file__), "framework")
        full_module_name = "smalivm.framework." + class_name[1:-1].replace("/", ".")
        if full_module_name in sys.modules:
            module = sys.modules[full_module_name]
        else:
            parts = class_name[1:-1].split("/")
            module_name = parts[-1]
            module_path = os.path.join(framework_dir, *parts[:-1], f"{module_name}.py")
            spec = importutil.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                logging.error(f"Failed to load framework class {module_name}")
                return None
            module = importutil.module_from_spec(spec)
            spec.loader.exec_module(module)
        # clazz = type(class_name, (module.FrameworkClass,), {})()
        return module.FrameworkClass

    def add_breakpoint_by_instruction(
        self,
        ins: Instruction,
        callback: Callable[[RegistersContext, Instruction], bool | None],
    ) -> None:
        self.__breakpoints.add_by_instruction(ins, callback)

    def add_breakpoint_by_custom_condition(
        self,
        condition: Callable[[RegistersContext, Instruction], bool],
        calback: Callable[[RegistersContext, Instruction], bool | None],
    ) -> None:
        self.__breakpoints.add_by_custom_condition(condition, calback)

    def add_breakpoint_by_value_type(
        self,
        value_type: Literal["string"],
        callback: Callable[[RegistersContext, Instruction, Register, str], bool | None],
    ) -> None:
        self.__breakpoints.add_by_value_type(value_type, callback)

    def remove_breakpoint_by_instruction(
        self,
        ins: Instruction,
        callback: Callable[[RegistersContext, Instruction], bool | None],
    ) -> None:
        self.__breakpoints.remove_by_instruction(ins, callback)

    def remove_breakpoint_by_custom_condition(
        self,
        condition: Callable[[RegistersContext, Instruction], bool],
        calback: Callable[[RegistersContext, Instruction], bool | None],
    ) -> None:
        self.__breakpoints.remove_by_custom_condition(condition, calback)

    def remove_breakpoint_by_value_type(
        self,
        value_type: Literal["string"],
        callback: Callable[[RegistersContext, Instruction, Register, str], bool | None],
    ) -> None:
        self.__breakpoints.remove_by_value_type(value_type, callback)

    # def load_class(self, clazz: Class) -> None:
    #     self.__classes[clazz.name] = clazz

    # def iter_classes(self) -> Iterable[Class]:
    #     return self.__classes.values()

    # def create_class_instance(self, class_name: str, constructor_types: list[str] | None = None, args: list[Any] | None = None) -> None:
    #     clazz = self.__classes[class_name]
    #     init_method = clazz.find_methods("<init>", constructor_types)
    #     if len(init_method) == 0:
    #         raise MethodNotFoundError(f"Constructor not found in class {class_name}")
    #     elif len(init_method) > 1:
    #         raise MethodNotFoundError(f"Ambigious constructor in class {class_name}")

    # def call_method(
    #     self,
    #     class_name: str,
    #     method_name: str,
    #     parameter_types: list[str] | None = None,
    #     args: list[Any] | None = None,
    # ) -> RegisterValue | None:
    #     clazz = self.__classes[class_name]
    #     methods = clazz.find_methods(method_name, parameter_types)
    #     if len(methods) == 0:
    #         raise MethodNotFoundError(
    #             f"Method {method_name} not found in class {class_name}"
    #         )
    #     elif len(methods) > 1:
    #         raise MethodNotFoundError(
    #             f"Ambigious method {method_name} in class {class_name}"
    #         )

    #     runner = MethodRunner(methods[0], self)
    #     if args is None:
    #         args = []
    #     return runner.run(*args)

    # def find_class(self, class_name: str) -> Class | None:
    #     if class_name not in self.__classes and class_name in self.__class_files:
    #         logging.debug(
    #             f"Loading class {class_name} because it was not found in cache"
    #         )
    #         clazz: Class
    #         with open(self.__class_files[class_name]) as f:
    #             clazz = Class(f)
    #         self.__classes[class_name] = clazz
    #     return self.__classes.get(class_name, None)

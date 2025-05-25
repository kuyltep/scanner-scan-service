# from dataclasses import dataclass
# from typing import Any, Iterator, TypeVar, overload
# from smalivm.smali import labels
# from typing import cast
# from smalivm.breakpoints import Breakpoints
from typing import Type, overload

from smalivm.smali import directives
from smalivm.smali.directives import Directive
from smalivm.smali.instructions import Instruction
from smalivm.smali.labels import Label
from smalivm.smali.utils import parse_method_parameters
from dataclasses import dataclass
# from smalivm.smali.registers import RegisterValue
# from smalivm.smali.registers_values.unknown import UnknownValue
# from smalivm.smalivm import MethodRunner, Vm

# from smalivm.smali.registers import RegisterValue
# from smalivm.smali.parsers import LineParser
# from smalivm.smali.reader import Reader

# from smalivm.smali.registers_values.unknown import UnknownValue
# from smalivm.smali.utils import parse_method_parameters


@dataclass(slots=True, init=False)
class Method:
    # __slots__ = [
    #     "_instructions",
    #     "_branches",
    #     "_branch",
    #     "_returned",
    #     "_thrown",
    #     "_parameters_types",
    #     "_flags",
    #     "_name",
    #     "_virtual",
    #     "_direct",
    #     "_return_type",
    #     "_clazz",
    #     "_registers_count",
    # ]
    # _breakpoints_by_instructions: dict[
    #     Type[Instruction], set[Callable[["Method", Instruction], None]]
    # ]
    # _breakpoints_by_register_value: dict[
    #     Callable[["Method", "Register"], None],
    #     Callable[["Register"], None],
    # ]
    # _breakpoints_by_condition: set[
    #     tuple[
    #         Callable[["Method", Instruction], bool],
    #         Callable[["Method", Instruction], None],
    #     ]
    # ]
    # _position: int = -1
    _instructions: list[Instruction | Label | Directive]
    # blocks: dict[str, list[Instruction | Label | Directive]]
    # blocks_order: list[str]
    # _visited_lines: set[int]
    # _branches: dict[int, list[set[int]]]
    # _branch: tuple[int, bool] | None
    _returned: bool
    _thrown: bool
    # _last_instruction_result: RegisterValueType | None = None
    # _visited_blocks: dict[Instruction22t | Instruction21t, set[int]]
    # _save_visited_lines: bool = False
    # _saved_visited_lines: set[int]

    # registers: RegistersContext
    _parameters_types: list[str]
    _flags: list[str]
    _name: str
    _virtual: bool
    _direct: bool
    _return_type: str
    _clazz: Type["Class"]
    _registers_count: int

    # def __del__(self) -> None:
    #     # for ins in self._instructions:
    #     #     del ins
    #     del self._instructions
    #     del self._clazz

    # @property
    # def signature(self) -> str:
    #     return f"{self.name}({''.join(self.parameters_types)}){self.return_type}"

    # @overload
    # def __init__(self, clazz: "Class") -> None: ...

    # @overload
    # def __init__(self, clazz: "Class", reader: Reader) -> None: ...

    # @overload
    # def __init__(self, clazz: "Class", reader: list[str]) -> None: ...

    # @overload
    # def __init__(self, clazz: "Class", reader: Iterator[str]) -> None: ...

    def __hash__(self) -> int:
        return hash((self._clazz, self._name, tuple(self._parameters_types), self._return_type))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Method):
            return False
        return self.get_full_signature() == other.get_full_signature()

    def __init__(self) -> None:
        # self.registers = RegistersContext()
        # self._visited_lines = set()
        # self._breakpoints_by_instructions = {}
        # self._breakpoints_by_register_value = {}
        # self._breakpoints_by_condition = set()
        self._instructions = []
        self._returned = False
        self._thrown = False
        self._parameters_types = []
        self._flags = []
        self._virtual = False
        self._direct = False
        self._registers_count = 0
        # self.clazz = clazz
        # self.blocks = {}
        # self.blocks_order = []
        # self._branches = {}
        # self._visited_blocks = {}
        # self._branch = None
        # if reader is not None:
        #     if not isinstance(reader, Reader):
        #         reader = Reader(reader)
        #     self._parse_lines(reader)

    def get_name(self) -> str:
        return self._name

    def get_flags(self) -> list[str]:
        return self._flags

    def is_abstract(self) -> bool:
        return "abstract" in self._flags

    def is_native(self) -> bool:
        return "native" in self._flags

    def get_parameters_types(self) -> list[str]:
        return self._parameters_types

    def get_registers_count(self) -> int:
        return self._registers_count

    def get_instructions(self) -> list[Instruction | Label | Directive]:
        return self._instructions

    def get_return_type(self) -> str:
        return self._return_type

    def get_signature(self) -> str:
        return f"{self.get_name()}({''.join(self.get_parameters_types())}){self.get_return_type()}"

    def get_class(self) -> Type["Class"]:
        return self._clazz

    def get_full_signature(self) -> str:
        return f"{self._clazz._name}->{self.get_signature()}"

    # def _parse_lines(self, reader: Reader):
    #     self.instructions = []
    #     labels_context = labels.LabelsContext()
    #     # block: list[Instruction | Label | Directive] = []
    #     # self.blocks["main"] = block
    #     # self.blocks_order.append("main")
    #     for line in reader:
    #         line = line.strip()
    #         if not line:
    #             continue
    #         if line.startswith(".method"):
    #             self._parse_header(line)
    #             continue
    #         elif line == ".end method":
    #             break

    #         reader.prepend(line)
    #         ins = LineParser.parse(self, reader, labels_context)
    #         if isinstance(ins, directives.Registers):
    #             self.registers_count = ins.count
    #         elif isinstance(ins, directives.Locals):
    #             parameters_count = 0
    #             for param in self.parameters_types:
    #                 parameters_count += 1
    #                 if param in ["J", "D"]:
    #                     parameters_count += 1
    #             self.registers_count = (
    #                 ins.count
    #                 + parameters_count
    #                 + (1 if "static" not in self.flags else 0)
    #             )
    #         else:
    #             self.instructions.append(ins)

    # def has_register(self, name: str) -> bool:
    #     return self.registers.has_register(name)

    # def get_registers(self) -> set[Register]:
    #     return self.registers.get_registers()

    # def get_registers_count(self) -> int:
    #     return self.registers.get_registers_count()

    # def get_max_registers_count(self) -> int:
    #     return self.registers.get_max_registers_count()

    # def _parse_header(self, line: str) -> None:
    #     parts = line.split(" ")[1:]
    #     signature = parts[-1]
    #     first_idx = signature.index("(")
    #     last_idx = signature.rindex(")")
    #     self.name = signature[:first_idx]
    #     self.return_type = signature[last_idx + 1 :]
    #     self.parameters_types = parse_method_parameters(
    #         signature[first_idx + 1 : last_idx]
    #     )
    #     self.flags = parts[:-1]

    # def __iter__(self) -> Self:
    #     return self

    # def __next__(self) -> Instruction | Label | Directive:
    #     if self._returned:
    #         raise StopIteration
    #     self._position += 1
    #     for i, ins in enumerate(self.instructions[self._position :]):
    #         i += self._position
    #         if i in self._visited_lines:
    #             continue
    #         self._position = i
    #         if self._save_visited_lines:
    #             self._saved_visited_lines.add(self._position)
    #         return ins
    #     raise StopIteration

    # def _trigger_breakpoint(self, ins: Instruction):
    #     if ins.__class__ in self._breakpoints_by_instructions:
    #         for callback in self._breakpoints_by_instructions[ins.__class__]:
    #             callback(self, ins)
    #     for condition, callback in self._breakpoints_by_condition:
    #         if condition(self, ins):
    #             callback(self, ins)

    # def invoke(self, *args: RegisterValueType) -> None:
    #     self.reset()
    #     reg_num = 0

    #     param_registers: list[Register] = list()
    #     if "static" not in self.flags:
    #         reg = Register("p0")
    #         reg.value = RegisterValue(UnknownValue())
    #         self.registers.add_register(reg)
    #         param_registers.append(reg)
    #         reg_num += 1

    #     for param in self.parameters_types:
    #         reg = Register(f"p{reg_num}")
    #         reg.value = RegisterValue(UnknownValue())
    #         self.registers.add_register(reg)
    #         param_registers.append(reg)
    #         if param in ["J", "D"]:
    #             reg_num += 1
    #             reg2 = Register(f"p{reg_num}")
    #             reg2.value = RegisterValue(UnknownValue())
    #             reg.pair = reg2
    #             reg2.pair = reg
    #         reg_num += 1

    #     for i, arg in enumerate(args):
    #         reg = param_registers[i]
    #         reg.value = RegisterValue(arg)
    #     self._analyze()

    # def _analyze(self):
    #     for ins in self:
    # has_last_instruction_result = self._last_instruction_result is not None
    # self._write_branch()
    # if isinstance(
    #     ins,
    #     (Label, Directive, MonitorEnter, MonitorExit, CheckCast, InstanceOf),
    # ):
    #     continue
    # self._trigger_breakpoint(ins)
    # if isinstance(ins, (ReturnVoid, Return, ReturnObject, ReturnWide)):
    #     self._branch = None
    #     self._returned = True
    # elif isinstance(ins, Throw):
    #     self._branch = None
    #     self._thrown = True
    #     break
    # elif isinstance(ins, (MonitorEnter, MonitorExit, CheckCast, Nop)):
    #     continue
    # elif isinstance(
    #     ins,
    #     (
    #         Const,
    #         Const4,
    #         Const16,
    #         ConstHigh16,
    #         ConstWide,
    #         ConstWide16,
    #         ConstWide32,
    #         ConstWideHigh16,
    #     ),
    # ):
    #     self._const(ins)
    # elif isinstance(ins, (ConstString, ConstStringJumbo)):
    #     self._const_string(ins)
    # elif isinstance(ins, ConstClass):
    #     self._const_class(ins)
    # elif isinstance(
    #     ins,
    #     (
    #         Move,
    #         MoveFrom16,
    #         Move16,
    #         MoveObject,
    #         MoveObjectFrom16,
    #         MoveObject16,
    #         MoveWide,
    #         MoveWide16,
    #         MoveWideFrom16,
    #     ),
    # ):
    #     self._move(ins)
    # elif isinstance(ins, Instruction22t):
    #     self._if(ins)
    # elif isinstance(ins, Instruction21t):
    #     self._ifz(ins)
    # elif isinstance(ins, (Goto, Goto16, Goto32)):
    #     self._goto(ins)
    # elif isinstance(ins, AddInt):
    #     self._math_int(ins, lambda x, y: x + y)
    # elif isinstance(ins, SubInt):
    #     self._math_int(ins, lambda x, y: x - y)
    # elif isinstance(ins, MulInt):
    #     self._math_int(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivInt):
    #     self._math_int(ins, lambda x, y: x // y)
    # elif isinstance(ins, RemInt):
    #     self._math_int(ins, lambda x, y: x % y)
    # elif isinstance(ins, AddDouble):
    #     self._math_double(ins, lambda x, y: x + y)
    # elif isinstance(ins, SubDouble):
    #     self._math_double(ins, lambda x, y: x - y)
    # elif isinstance(ins, MulDouble):
    #     self._math_double(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivDouble):
    #     self._math_double(ins, lambda x, y: x / y)
    # elif isinstance(ins, RemDouble):
    #     self._math_double(ins, lambda x, y: x % y)
    # elif isinstance(ins, NewArray):
    #     self._new_array(ins)
    # elif isinstance(
    #     ins,
    #     (
    #         Aput,
    #         AputWide,
    #         AputObject,
    #         AputBoolean,
    #         AputByte,
    #         AputChar,
    #         AputShort,
    #     ),
    # ):
    #     self._aput(ins)
    # elif isinstance(
    #     ins,
    #     (
    #         InvokeVirtual,
    #         InvokeStatic,
    #         InvokeSuper,
    #         InvokeDirect,
    #         InvokeInterface,
    #         InvokePolymorphic,
    #         InvokeCustom,
    #         InvokeVirtualRange,
    #         InvokeStaticRange,
    #         InvokeSuperRange,
    #         InvokeDirectRange,
    #         InvokeInterfaceRange,
    #         InvokePolymorphicRange,
    #         InvokeCustomRange,
    #     ),
    # ):
    #     self._invoke(ins)
    # elif isinstance(
    #     ins, (MoveResult, MoveResultObject, MoveResultWide, MoveException)
    # ):
    #     self._move_result(ins)
    # elif isinstance(ins, ArrayLength):
    #     self._array_length(ins)
    # elif isinstance(ins, NewInstance):
    #     self._new_instance(ins)
    # elif isinstance(ins, (FilledNewArray, FilledNewArrayRange)):
    #     self._filled_new_array(ins)
    # elif isinstance(ins, FillArrayData):
    #     self._fill_array_data(ins)
    # elif isinstance(ins, PackedSwitch):
    #     self._packed_switch(ins)
    # elif isinstance(ins, SparseSwitch):
    #     self._sparse_switch(ins)
    # elif isinstance(ins, (CmplFloat, CmpgFloat)):
    #     self._cmplg_float(ins)
    # elif isinstance(ins, (CmplDouble, CmpgDouble)):
    #     self._cmplg_double(ins)
    # elif isinstance(ins, CmpLong):
    #     self._cmp_long(ins)
    # elif isinstance(
    #     ins,
    #     (
    #         Aget,
    #         AgetWide,
    #         AgetObject,
    #         AgetBoolean,
    #         AgetByte,
    #         AgetChar,
    #         AgetShort,
    #     ),
    # ):
    #     self._aget(ins)
    # elif isinstance(
    #     ins,
    #     (
    #         Iget,
    #         IgetWide,
    #         IgetObject,
    #         IgetBoolean,
    #         IgetByte,
    #         IgetChar,
    #         IgetShort,
    #     ),
    # ):
    #     self._iget(ins)
    # elif isinstance(
    #     ins,
    #     (
    #         Iput,
    #         IputWide,
    #         IputObject,
    #         IputBoolean,
    #         IputByte,
    #         IputChar,
    #         IputShort,
    #     ),
    # ):
    #     self._iput(ins)
    # elif isinstance(
    #     ins,
    #     (
    #         Sget,
    #         SgetWide,
    #         SgetObject,
    #         SgetBoolean,
    #         SgetByte,
    #         SgetChar,
    #         SgetShort,
    #     ),
    # ):
    #     self._sget(ins)
    # elif isinstance(
    #     ins,
    #     (
    #         Sput,
    #         SputWide,
    #         SputObject,
    #         SputBoolean,
    #         SputByte,
    #         SputChar,
    #         SputShort,
    #     ),
    # ):
    #     self._sput(ins)
    # elif isinstance(ins, NegInt):
    #     self._math_int2(ins, lambda x: -x)
    # elif isinstance(ins, NotInt):
    #     self._math_int2(ins, lambda x: ~x)
    # elif isinstance(ins, NegLong):
    #     self._math_long2(ins, lambda x: -x)
    # elif isinstance(ins, NotLong):
    #     self._math_long2(ins, lambda x: ~x)
    # elif isinstance(ins, NegFloat):
    #     self._math_float2(ins, lambda x: -x)
    # elif isinstance(ins, NegDouble):
    #     self._math_double2(ins, lambda x: -x)
    # elif isinstance(ins, IntToLong):
    #     self._int_to_long(ins)
    # elif isinstance(ins, IntToFloat):
    #     self._int_to_float(ins)
    # elif isinstance(ins, IntToDouble):
    #     self._int_to_double(ins)
    # elif isinstance(ins, LongToInt):
    #     self._long_to_int(ins)
    # elif isinstance(ins, LongToFloat):
    #     self._long_to_float(ins)
    # elif isinstance(ins, LongToDouble):
    #     self._long_to_double(ins)
    # elif isinstance(ins, FloatToInt):
    #     self._float_to_int(ins)
    # elif isinstance(ins, FloatToLong):
    #     self._float_to_long(ins)
    # elif isinstance(ins, FloatToDouble):
    #     self._float_to_double(ins)
    # elif isinstance(ins, DoubleToInt):
    #     self._double_to_int(ins)
    # elif isinstance(ins, DoubleToLong):
    #     self._double_to_long(ins)
    # elif isinstance(ins, DoubleToFloat):
    #     self._double_to_float(ins)
    # elif isinstance(ins, IntToByte):
    #     self._int_to_byte(ins)
    # elif isinstance(ins, IntToChar):
    #     self._int_to_char(ins)
    # elif isinstance(ins, IntToShort):
    #     self._int_to_short(ins)
    # elif isinstance(ins, AndInt):
    #     self._math_int(ins, lambda x, y: x & y)
    # elif isinstance(ins, OrInt):
    #     self._math_int(ins, lambda x, y: x | y)
    # elif isinstance(ins, XorInt):
    #     self._math_int(ins, lambda x, y: x ^ y)
    # elif isinstance(ins, ShlInt):
    #     self._math_int(ins, lambda x, y: x << y)
    # elif isinstance(ins, ShrInt):
    #     self._math_int(ins, lambda x, y: x >> y)
    # elif isinstance(ins, UshrInt):
    #     self._math_int(ins, lambda x, y: (x % 0x100000000) >> y)
    # elif isinstance(ins, AddLong):
    #     self._math_long(ins, lambda x, y: x + y)
    # elif isinstance(ins, SubLong):
    #     self._math_long(ins, lambda x, y: x - y)
    # elif isinstance(ins, MulLong):
    #     self._math_long(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivLong):
    #     self._math_long(ins, lambda x, y: x // y)
    # elif isinstance(ins, RemLong):
    #     self._math_long(ins, lambda x, y: x % y)
    # elif isinstance(ins, AndLong):
    #     self._math_long(ins, lambda x, y: x & y)
    # elif isinstance(ins, OrLong):
    #     self._math_long(ins, lambda x, y: x | y)
    # elif isinstance(ins, XorLong):
    #     self._math_long(ins, lambda x, y: x ^ y)
    # elif isinstance(ins, ShlLong):
    #     self._math_long(ins, lambda x, y: x << y)
    # elif isinstance(ins, ShrLong):
    #     self._math_long(ins, lambda x, y: x >> y)
    # elif isinstance(ins, UshrLong):
    #     self._math_long(ins, lambda x, y: (x % 0x10000000000000000) >> y)
    # elif isinstance(ins, AddFloat):
    #     self._math_float(ins, lambda x, y: x + y)
    # elif isinstance(ins, SubFloat):
    #     self._math_float(ins, lambda x, y: x - y)
    # elif isinstance(ins, MulFloat):
    #     self._math_float(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivFloat):
    #     self._math_float(ins, lambda x, y: x / y)
    # elif isinstance(ins, RemFloat):
    #     self._math_float(ins, lambda x, y: x % y)
    # elif isinstance(ins, AddInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x + y)
    # elif isinstance(ins, SubInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x - y)
    # elif isinstance(ins, MulInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x // y)
    # elif isinstance(ins, RemInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x % y)
    # elif isinstance(ins, AndInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x & y)
    # elif isinstance(ins, OrInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x | y)
    # elif isinstance(ins, XorInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x ^ y)
    # elif isinstance(ins, ShlInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x << y)
    # elif isinstance(ins, ShrInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: x >> y)
    # elif isinstance(ins, UshrInt2Addr):
    #     self._math_int_2addr(ins, lambda x, y: (x % 0x100000000) >> y)
    # elif isinstance(ins, AddLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x + y)
    # elif isinstance(ins, SubLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x - y)
    # elif isinstance(ins, MulLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x // y)
    # elif isinstance(ins, RemLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x % y)
    # elif isinstance(ins, AndLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x & y)
    # elif isinstance(ins, OrLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x | y)
    # elif isinstance(ins, XorLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x ^ y)
    # elif isinstance(ins, ShlLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x << y)
    # elif isinstance(ins, ShrLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: x >> y)
    # elif isinstance(ins, UshrLong2Addr):
    #     self._math_long_2addr(ins, lambda x, y: (x % 0x10000000000000000) >> y)
    # elif isinstance(ins, AddFloat2Addr):
    #     self._math_float_2addr(ins, lambda x, y: x + y)
    # elif isinstance(ins, SubFloat2Addr):
    #     self._math_float_2addr(ins, lambda x, y: x - y)
    # elif isinstance(ins, MulFloat2Addr):
    #     self._math_float_2addr(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivFloat2Addr):
    #     self._math_float_2addr(ins, lambda x, y: x / y)
    # elif isinstance(ins, RemFloat2Addr):
    #     self._math_float_2addr(ins, lambda x, y: x % y)
    # elif isinstance(ins, AddDouble2Addr):
    #     self._math_double_2addr(ins, lambda x, y: x + y)
    # elif isinstance(ins, SubDouble2Addr):
    #     self._math_double_2addr(ins, lambda x, y: x - y)
    # elif isinstance(ins, MulDouble2Addr):
    #     self._math_double_2addr(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivDouble2Addr):
    #     self._math_double_2addr(ins, lambda x, y: x / y)
    # elif isinstance(ins, RemDouble2Addr):
    #     self._math_double_2addr(ins, lambda x, y: x % y)
    # elif isinstance(ins, AddIntLit16):
    #     self._math_int_lit16(ins, lambda x, y: x + y)
    # elif isinstance(ins, RsubInt):
    #     self._math_int_lit16(ins, lambda x, y: y - x)
    # elif isinstance(ins, MulIntLit16):
    #     self._math_int_lit16(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivIntLit16):
    #     self._math_int_lit16(ins, lambda x, y: x // y)
    # elif isinstance(ins, RemIntLit16):
    #     self._math_int_lit16(ins, lambda x, y: x % y)
    # elif isinstance(ins, AndIntLit16):
    #     self._math_int_lit16(ins, lambda x, y: x & y)
    # elif isinstance(ins, OrIntLit16):
    #     self._math_int_lit16(ins, lambda x, y: x | y)
    # elif isinstance(ins, XorIntLit16):
    #     self._math_int_lit16(ins, lambda x, y: x ^ y)
    # elif isinstance(ins, AddIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: x + y)
    # elif isinstance(ins, RsubIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: y - x)
    # elif isinstance(ins, MulIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: x * y)
    # elif isinstance(ins, DivIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: x // y)
    # elif isinstance(ins, RemIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: x % y)
    # elif isinstance(ins, AndIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: x & y)
    # elif isinstance(ins, OrIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: x | y)
    # elif isinstance(ins, XorIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: x ^ y)
    # elif isinstance(ins, ShlIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: x << y)
    # elif isinstance(ins, ShrIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: x >> y)
    # elif isinstance(ins, UshrIntLit8):
    #     self._math_int_lit8(ins, lambda x, y: (x % 0x100000000) >> y)
    # elif isinstance(ins, ConstMethodHandle):
    #     self._const_method_handle(ins)
    # elif isinstance(ins, ConstMethodType):
    #     self._const_method_type(ins)
    # else:
    #     raise UnsupportedInstructionError(ins)

    # if has_last_instruction_result:
    #     self._last_instruction_result = None

    # def add_breakpoint_by_instruction(
    #     self,
    #     instruction: Type[Instruction],
    #     callback: Callable[["Method", Instruction], None],
    # ) -> None:
    #     if instruction.__class__ not in self._breakpoints_by_instructions:
    #         self._breakpoints_by_instructions[instruction] = set()
    #     self._breakpoints_by_instructions[instruction].add(callback)

    # def remove_breakpoint_by_instruction(
    #     self, instruction: str, callback: Callable[["Method", Instruction], None]
    # ) -> None:
    #     if instruction in self._breakpoints_by_instructions:
    #         self._breakpoints_by_instructions[instruction].remove(callback)

    # def add_breakpoint_by_register_value(
    #     self,
    #     register: str,
    #     value: RegisterValue,
    #     callback: Callable[["Method", "Register"], None],
    # ) -> None:
    #     def wrapper(reg: Register) -> None:
    #         callback(self, reg)

    #     self._breakpoints_by_register_value[callback] = wrapper
    #     self.registers.add_breakpoint_by_register_value(register, value, wrapper)

    # def remove_breakpoint_by_register_value(
    #     self,
    #     register: str,
    #     value: RegisterValue,
    #     callback: Callable[["Method", "Register"], None],
    # ) -> None:
    #     if callback not in self._breakpoints_by_register_value:
    #         return
    #     wrapper = self._breakpoints_by_register_value[callback]
    #     del self._breakpoints_by_register_value[callback]
    #     self.registers.remove_breakpoint_by_register_value(register, value, wrapper)

    # def add_breakpoint_by_condition(
    #     self,
    #     condition: Callable[["Method", Instruction], bool],
    #     callback: Callable[["Method", Instruction], None],
    # ) -> None:
    #     item = (condition, callback)
    #     if item not in self._breakpoints_by_condition:
    #         self._breakpoints_by_condition.add(item)

    # def remove_breakpoint_by_condition(
    #     self,
    #     condition: Callable[["Method", Instruction], bool],
    #     callback: Callable[["Method", Instruction], None],
    # ) -> None:
    #     item = (condition, callback)
    #     if item in self._breakpoints_by_condition:
    #         self._breakpoints_by_condition.remove(item)

    # def _get_index(self, lines: "seekable[str]", line: str) -> int:
    #     return lines.elements().index(line)

    def is_returned(self) -> bool:
        return self._returned

    def is_thrown(self) -> bool:
        return self._thrown


@dataclass(slots=True, init=False)
class Field:
    # __slots__ = ["_name", "_type", "_annotations", "_flags", "_initial_value", "_clazz"]

    _name: str
    _type: str
    _annotations: list[directives.Annotation]
    _flags: list[str]
    _initial_value: str | None
    _clazz: Type["Class"]

    # @overload
    # def __init__(self, clazz: "Class", reader: Reader) -> None: ...
    # @overload
    # def __init__(self, clazz: "Class", reader: list[str]) -> None: ...
    # @overload
    # def __init__(self, clazz: "Class", reader: Iterator[str]) -> None: ...
    def __init__(self) -> None:
        self._annotations = []
        self._flags = []
        self._initial_value = None
        # self.clazz = clazz
        # if not isinstance(reader, Reader):
        #     reader = Reader(reader)
        # self._parse_lines(reader)

        # value = UnknownValue()
        # if self.initial_value is not None:
        #     value = self.initial_value
        # self.value = RegisterValue(value, self.type)

    def get_type(self) -> str:
        return self._type

    def get_initial_value(self) -> str | None:
        return self._initial_value

    def get_class(self) -> Type["Class"]:
        return self._clazz

    def get_flags(self) -> list[str]:
        return self._flags

    def get_name(self) -> str:
        return self._name

    def get_signature(self) -> str:
        return f"{self._name}:{self._type}"

    def get_full_signature(self) -> str:
        return f"{self._clazz._name}->{self.get_signature()}"

    # def _parse_lines(self, reader: Reader) -> None:
    #     for line in reader:
    #         if line.startswith(".field "):
    #             parts = line.split(" ")
    #             for idx, part in enumerate(parts[1:]):
    #                 if ":" in part:
    #                     parts = parts[idx + 1 :]
    #                     break
    #                 self.flags.append(part)
    #             signature = parts[0].split(":")
    #             self.name = signature[0]
    #             self.type = signature[1]
    #             if len(parts) > 1:
    #                 self.initial_value = " ".join(parts[2:])

    #             next_line = reader.peek()
    #             if next_line is not None and next_line.startswith(".annotation"):
    #                 for line in reader:
    #                     if line.startswith(".annotation "):
    #                         reader.prepend(line)
    #                         annotation = directives.Annotation(
    #                             reader, labels.LabelsContext()
    #                         )
    #                         self.annotations.append(annotation)
    #                     elif line == ".end field":
    #                         return
    #                     else:
    #                         raise ValueError(f"Invalid line: {line}")
    #             break
    #         else:
    #             raise ValueError(f"Invalid line: {line}")

    # def __str__(self) -> str:
    #     return f"{self.clazz.name}->{self.name}:{self.type}"


@dataclass(slots=True, init=False)
class Class:
    # __slots__ = [
    #     "_methods",
    #     "_fields",
    #     "_annotations",
    #     "_flags",
    #     "_implements",
    #     "_name",
    #     "_source",
    #     "_super",
    #     "__methods_signatures_cache",
    # ]

    _methods: list[Method]
    _fields: list[Field]
    _annotations: list[directives.Annotation]
    _flags: list[str]
    _implements: list[str]
    _name: str
    _source: str | None
    _super: str | None

    # __methods_signatures_cache: dict[str, Method]

    def __hash__(self) -> int:
        return id(self)

    def is_framework(self) -> bool:
        return False

    # def __del__(self) -> None:
        # for method in self._methods:
        #     del method
        # for field in self._fields:
        #     del field
        # for annotation in self._annotations:
        #     del annotation

    # def __init__(self) -> None:
    #     self._source = None
    #     self._super = None
    #     self._methods = set()
    #     self._fields = set()
    #     self._annotations = set()
    #     self._flags = []
    #     self._implements = []

        # self.__methods_signatures_cache = {}

    @classmethod
    def get_name(cls) -> str:
        return cls._name

    def get_methods(self) -> list[Method]:
        return self._methods

    def get_fields(self) -> list[Field]:
        return self._fields

    def get_flags(self) -> list[str]:
        return self._flags

    @overload
    def get_method(self, signature: str) -> Method | None: ...
    @overload
    def get_method(self, signature: tuple[str, list[str]]) -> Method | None: ...

    def get_method(self, signature) -> Method | None:
        method_name: str = ""
        method_parameters: list[str] = []
        if isinstance(signature, str):
            method_name = signature.split("(")[0]
            parameters = signature[signature.index("(")+1:signature.rindex(")")]
            method_parameters = parse_method_parameters(parameters)
        elif isinstance(signature, tuple):
            method_name, method_parameters = signature

        # if signature in self.__methods_signatures_cache:
        #     return self.__methods_signatures_cache[signature]

        for method in self._methods:
            if method.get_name() == method_name and method.get_parameters_types() == method_parameters:
                # self.__methods_signatures_cache[signature] = method
                return method
        return None

    # def new_instance(self) -> "SmaliClass":
    #     return type(self.get_name(), (SmaliClass,), {"_clazz": self})()

    # @overload
    # def __init__(self) -> None: ...

    # @overload
    # def __init__(self, reader: Reader) -> None: ...

    # @overload
    # def __init__(self, reader: list[str]) -> None: ...

    # @overload
    # def __init__(self, reader: Iterator[str]) -> None: ...

    # def __init__(self) -> None:
    #     self._methods = set()
    #     self._fields = set()
    #     self._annotations = []
    #     self._flags = []
    #     self._implements = []

    # if reader is not None:
    #     if not isinstance(reader, Reader):
    #         reader = Reader(reader)
    #     self._parse_lines(reader)

    # def _parse_lines(self, reader: Reader) -> None:
    #     direct_methods_section = False
    #     virtual_methods_section = False
    #     for line in reader:
    #         if line.startswith("#"):
    #             if line == "# direct methods":
    #                 direct_methods_section = True
    #                 continue
    #             elif line == "# virtual methods":
    #                 virtual_methods_section = True
    #                 continue
    #             else:
    #                 raise ValueError(f"Invalid comment: {line} in class {self.name}")

    #         if line.startswith(".class "):
    #             parts = line.split(" ")
    #             self.name = parts[-1]
    #             self.flags = parts[1:-1]
    #         elif line.startswith(".super "):
    #             self.super = line.split(" ")[-1]
    #         elif line.startswith(".source "):
    #             self.source = line.split(" ")[-1][1:-1]
    #         elif line.startswith(".implements "):
    #             self.implements.append(line.split(" ")[-1])
    #         elif line.startswith(".annotation "):
    #             reader.prepend(line)
    #             annotation = directives.Annotation(reader, labels.LabelsContext())
    #             self.annotations.append(annotation)
    #         elif line.startswith(".field "):
    #             reader.prepend(line)
    #             field = Field(self, reader)
    #             self.fields.add(field)
    #         elif line.startswith(".method "):
    #             reader.prepend(line)
    #             method = SmaliMethod(self, reader)
    #             method.clazz = self
    #             if virtual_methods_section:
    #                 method.virtual = True
    #             elif direct_methods_section:
    #                 method.direct = True
    #             else:
    #                 raise ValueError(
    #                     f"Method {method.name} in class {self.name} must be one of virtual or direct"
    #                 )
    #             self.methods.add(method)
    #         else:
    #             raise ValueError(f"Invalid line: {line} in class {self.name}")

    # def find_methods(
    #     self, name: str, parameter_types: list[str] | None = None
    # ) -> list[Method]:
    #     founded: list[Method] = []
    #     for method in self.methods:
    #         if method.name == name:
    #             if parameter_types is None:
    #                 founded.append(method)
    #                 continue
    #             if method.parameters_types == parameter_types:
    #                 founded.append(method)
    #     return founded

    # def find_method_by_signature(self, signature: str) -> Method | None:
    #     for method in self.methods:
    #         if method.signature == signature:
    #             return method
    #     return None

    # @classmethod
    # def find_static_method_by_signature(cls, signature: str) -> Method | None:
    #     for method in cls.methods:
    #         if method.signature == signature and "static" in method.flags:
    #             return method
    #     return None

    # def find_field(self, name: str) -> Field | None:
    #     for field in self.fields:
    #         if field.name == name:
    #             return field
    #     return None


# SmaliClass = TypeVar("SmaliClass", bound=Class)
# class SmaliClass(Class):
#     _clazz: Class

#     # def __init__(self, clazz: Class) -> None:
#     #     self.__clazz = clazz

#     # def get_class(self) -> Class:
#     #     return self._clazz

#     def is_framework(self) -> bool:
#         from smalivm.framework.base_framework_class import BaseFrameworkClass

#         return isinstance(self, BaseFrameworkClass)

# def invoke_method(self, method_signature: str, vm: Vm, breakpoints: Breakpoints, *args) -> RegisterValue | None:
#     from smalivm.framework.base_framework_class import BaseFrameworkClass

#     if self.is_framework():
#         return cast(BaseFrameworkClass, self._clazz).invoke_method(method_signature)
#     else:
#         method = cast(Class, self._clazz).get_method(method_signature)
#         if method is not None:
#             runner = MethodRunner(method, vm, breakpoints)
#             return runner.run(*args)

#     return RegisterValue(UnknownValue())

# def __getattr__(self, name: str) -> Any:
#     return None
#     # return getattr(self._class, name)

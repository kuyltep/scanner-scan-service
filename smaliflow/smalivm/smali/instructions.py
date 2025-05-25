from dataclasses import dataclass
from smalivm.exceptions import UnsupportedInstructionError
from smalivm.smali.labels import Label, LabelsContext
from smalivm.smali.reader import Reader
from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from smalivm.smali.members import Method


@dataclass(slots=True, init=False)
class Instruction:
    _name: str
    method: "Method"

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        # if this constructor is called, it means that the instruction is not implemented, so skip line
        next(reader)

    def __str__(self) -> str:
        return self._name

    def get_name(self) -> str:
        return self._name

    def __hash__(self) -> int:
        return hash(str(self) + "|" + self.method.get_full_signature())

    @staticmethod
    def parse(
        method: "Method", reader: Reader, labels_context: LabelsContext
    ) -> "Instruction":
        data = reader.peek()
        if data is None:
            raise ValueError("No data to parse")
        ins: Instruction
        name: str
        if " " in data:
            name = data[: data.index(" ")]
            data = data[data.index(" ") + 1 :]
        else:
            name = data
            data = ""
        if name in INSTRUCTIONS:
            ins = INSTRUCTIONS[name](reader, labels_context)
        else:
            raise UnsupportedInstructionError(name)
        ins._name = name
        ins.method = method
        return ins

    def _extract_one_register(self, line: str) -> tuple[str, str]:
        idx = line.find(",")
        if idx == -1:
            raise ValueError(f"Invalid line: {line}")
        return line[:idx].rstrip(), line[idx + 1 :].lstrip()

    def _extract_two_registers(self, line: str) -> tuple[str, str, str]:
        reg1, line = self._extract_one_register(line)
        reg2, line = self._extract_one_register(line)
        return reg1, reg2, line

    def _extract_two_registers_without_data(self, line: str) -> tuple[str, str]:
        reg1, reg2 = self._extract_one_register(line)
        return reg1, reg2

    def _extract_three_registers(self, line: str) -> tuple[str, str, str, str]:
        reg1, line = self._extract_one_register(line)
        reg2, line = self._extract_one_register(line)
        reg3, line = self._extract_one_register(line)
        return reg1, reg2, reg3, line

    def _extract_three_registers_without_data(self, line: str) -> tuple[str, str, str]:
        reg1, line = self._extract_one_register(line)
        reg2, reg3 = self._extract_one_register(line)
        return reg1, reg2, reg3

    def __repr__(self) -> str:
        return f"Instruction({self})"

    # def __del__(self) -> None:
    #     del self.method


class Instruction10t(Instruction):
    label: Label

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.label = labels_context.get(data[1:])

    def __str__(self) -> str:
        return f"{self._name} {self.label}"


class Instruction10x(Instruction):
    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        next(reader)

    def __str__(self) -> str:
        return self._name


class Instruction11n(Instruction):
    reg1: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.data = self._extract_one_register(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.data}"


class Instruction11x(Instruction):
    reg1: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1 = data

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}"


class Instruction12x(Instruction):
    reg1: str
    reg2: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.reg2 = self._extract_two_registers_without_data(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.reg2}"


class Instruction20t(Instruction):
    label: Label

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.label = labels_context.get(data[1:])

    def __str__(self) -> str:
        return f"{self._name} {self.label}"


class Instruction21c(Instruction):
    reg1: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.data = self._extract_one_register(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.data}"


class Instruction21s(Instruction):
    reg1: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.data = self._extract_one_register(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.data}"


class Instruction21t(Instruction):
    reg1: str
    label: Label

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, data = self._extract_one_register(data)
        self.label = labels_context.get(data[1:])

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.label}"


class Instruction21h(Instruction):
    reg1: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.data = self._extract_one_register(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.data}"


class Instruction22b(Instruction):
    reg1: str
    reg2: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.reg2, self.data = self._extract_two_registers(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.reg2}, {self.data}"


class Instruction22c(Instruction):
    reg1: str
    reg2: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.reg2, self.data = self._extract_two_registers(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.reg2}, {self.data}"


class Instruction22s(Instruction):
    reg1: str
    reg2: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.reg2, self.data = self._extract_two_registers(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.reg2}, {self.data}"


class Instruction22t(Instruction):
    reg1: str
    reg2: str
    label: Label

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.reg2, data = self._extract_two_registers(data)
        self.label = labels_context.get(data[1:])

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.reg2}, {self.label}"


class Instruction22x(Instruction):
    reg1: str
    reg2: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.reg2 = self._extract_two_registers_without_data(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.reg2}"


class Instruction23x(Instruction):
    reg1: str
    reg2: str
    reg3: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.reg2, self.reg3 = self._extract_three_registers_without_data(
            data
        )

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.reg2}, {self.reg3}"


class Instruction30t(Instruction):
    label: Label

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.label = labels_context.get(data[1:])

    def __str__(self) -> str:
        return f"{self._name} {self.label}"


class Instruction31c(Instruction):
    reg1: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.data = self._extract_one_register(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.data}"


class Instruction31i(Instruction):
    reg1: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.data = self._extract_one_register(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.data}"


class Instruction31t(Instruction):
    reg1: str
    data: str
    label: Label

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, label = self._extract_one_register(data)
        self.label = labels_context.get(label[1:])

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.label}"


class Instruction32x(Instruction):
    reg1: str
    reg2: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.reg2 = self._extract_two_registers_without_data(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.reg2}"


class Instruction35c(Instruction):
    registers: list[str]
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        regs_data = data[data.index("{") + 1 : data.index("}")]
        regs = regs_data.split(", ")
        if len(regs) > 5:
            raise ValueError(f"Invalid registers: {regs_data}")
        self.registers = list(filter(lambda x: x, regs))
        self.data = data[data.index("}") :][2:].strip()

    def __str__(self) -> str:
        return f"{self._name} {{{', '.join(self.registers)}}}, {self.data}"


class Instruction3rc(Instruction):
    registers: list[str]
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        self.registers = []
        data = next(reader)
        regs_data = data[data.index("{") + 1 : data.index("}")]
        regs = regs_data.split(" .. ")
        if len(regs) != 2:
            raise ValueError(f"Invalid registers: {regs_data}")
        start_reg, end_reg = regs
        reg_prefix = start_reg[0]
        start = int(start_reg[1:])
        end = int(end_reg[1:])
        for i in range(start, end + 1):
            self.registers.append(f"{reg_prefix}{i}")
        self.data = data[data.index("}") + 2 :].strip()

    def __str__(self) -> str:
        first_reg = self.registers[0]
        last_reg = self.registers[-1]
        start = int(first_reg[1:])
        end = int(last_reg[1:])
        reg_prefix = first_reg[0]
        return f"{self._name} {{{reg_prefix}{start} .. {reg_prefix}{end}}}, {self.data}"


class Instruction51l(Instruction):
    reg1: str
    data: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        data = data[data.index(" ") + 1 :]
        self.reg1, self.data = self._extract_one_register(data)

    def __str__(self) -> str:
        return f"{self._name} {self.reg1}, {self.data}"


class Nop(Instruction10x):
    pass


class Move(Instruction12x):
    pass


class MoveFrom16(Instruction22x):
    pass


class Move16(Instruction32x):
    pass


class MoveWide(Instruction12x):
    pass


class MoveWideFrom16(Instruction22x):
    pass


class MoveWide16(Instruction32x):
    pass


class MoveObject(Instruction12x):
    pass


class MoveObjectFrom16(Instruction22x):
    pass


class MoveObject16(Instruction32x):
    pass


class MoveResult(Instruction11x):
    pass


class MoveResultWide(Instruction11x):
    pass


class MoveResultObject(Instruction11x):
    pass


class MoveException(Instruction11x):
    pass


class ReturnVoid(Instruction10x):
    pass


class Return(Instruction11x):
    pass


class ReturnWide(Instruction11x):
    pass


class ReturnObject(Instruction11x):
    pass


class MonitorEnter(Instruction11x):
    pass


class MonitorExit(Instruction11x):
    pass


class CheckCast(Instruction21c):
    pass


class InstanceOf(Instruction22c):
    pass


class Const4(Instruction11n):
    pass


class Const16(Instruction21s):
    pass


class ConstHigh16(Instruction21h):
    pass


class ConstClass(Instruction21c):
    pass


class ConstWideHigh16(Instruction21h):
    pass


class ConstWide(Instruction51l):
    pass


class ConstWide16(Instruction21s):
    pass


class ConstWide32(Instruction31i):
    pass


class ConstString(Instruction21c):
    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        super().__init__(reader, labels_context)
        self.data = self.data[1:-1]

    def __str__(self) -> str:
        return f'{self._name} {self.reg1}, "{self.data}"'


class ConstStringJumbo(Instruction31c):
    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        super().__init__(reader, labels_context)
        self.data = self.data[1:-1]

    def __str__(self) -> str:
        return f'{self._name} {self.reg1}, "{self.data}"'


class IfGe(Instruction22t):
    pass


class IfLe(Instruction22t):
    pass


class IfEq(Instruction22t):
    pass


class IfNe(Instruction22t):
    pass


class IfLt(Instruction22t):
    pass


class IfGt(Instruction22t):
    pass


class IfLez(Instruction21t):
    pass


class IfEqz(Instruction21t):
    pass


class IfNez(Instruction21t):
    pass


class IfLtz(Instruction21t):
    pass


class IfGez(Instruction21t):
    pass


class IfGtz(Instruction21t):
    pass


class Goto(Instruction10t):
    pass


class Goto16(Instruction20t):
    pass


class Goto32(Instruction30t):
    pass


class AddInt(Instruction23x):
    pass


class SubInt(Instruction23x):
    pass


class MulInt(Instruction23x):
    pass


class DivInt(Instruction23x):
    pass


class RemInt(Instruction23x):

    pass


class AddDouble(Instruction23x):
    pass


class SubDouble(Instruction23x):
    pass


class MulDouble(Instruction23x):
    pass


class DivDouble(Instruction23x):
    pass


class RemDouble(Instruction23x):
    pass


class DoubleToInt(Instruction12x):
    pass


class NewArray(Instruction22c):
    pass


class Aput(Instruction23x):
    pass


class AputWide(Instruction23x):
    pass


class AputObject(Instruction23x):
    pass


class AputBoolean(Instruction23x):
    pass


class AputByte(Instruction23x):
    pass


class AputChar(Instruction23x):
    pass


class AputShort(Instruction23x):
    pass


class InvokeType(Instruction35c, Instruction3rc):
    class_name: str
    method_signature: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        if isinstance(
            self,
            (
                InvokeVirtual,
                InvokeStatic,
                InvokeSuper,
                InvokeDirect,
                InvokeInterface,
                InvokePolymorphic,
                InvokeCustom,
            ),
        ):
            Instruction35c.__init__(self, reader, labels_context)
        elif isinstance(
            self,
            (
                InvokeVirtualRange,
                InvokeStaticRange,
                InvokeSuperRange,
                InvokeDirectRange,
                InvokeInterfaceRange,
                InvokePolymorphicRange,
                InvokeCustomRange,
            ),
        ):
            Instruction3rc.__init__(self, reader, labels_context)
        self.class_name, self.method_signature = self.data.split("->")


class InvokeVirtual(InvokeType):
    pass


class InvokeStatic(InvokeType):
    pass


class InvokeSuper(InvokeType):
    pass


class InvokeDirect(InvokeType):
    pass


class InvokeInterface(InvokeType):
    pass


class InvokePolymorphic(InvokeType):
    pass


class InvokeCustom(InvokeType):
    pass


# class Invoke3rc(Instruction3rc):
#     class_name: str
#     method_signature: str

#     def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
#         super().__init__(reader, labels_context)
#         self.class_name, self.method_signature = self.data.split("->")


class InvokeVirtualRange(InvokeType):
    pass


class InvokeStaticRange(InvokeType):
    pass


class InvokeSuperRange(InvokeType):
    pass


class InvokeDirectRange(InvokeType):
    pass


class InvokeInterfaceRange(InvokeType):
    pass


class InvokePolymorphicRange(InvokeType):
    pass


class InvokeCustomRange(InvokeType):
    pass


class ArrayLength(Instruction12x):
    pass


class NewInstance(Instruction21c):
    pass


class FilledNewArray(Instruction35c):
    pass


class FilledNewArrayRange(Instruction3rc):
    pass


class FillArrayData(Instruction31t):
    pass


class Throw(Instruction11x):
    pass


class PackedSwitch(Instruction31t):
    pass


class SparseSwitch(Instruction31t):
    pass


class CmplFloat(Instruction23x):
    pass


class CmpgFloat(Instruction23x):
    pass


class CmplDouble(Instruction23x):
    pass


class CmpgDouble(Instruction23x):
    pass


class CmpLong(Instruction23x):
    pass


class Aget(Instruction23x):
    pass


class AgetWide(Instruction23x):
    pass


class AgetObject(Instruction23x):
    pass


class AgetBoolean(Instruction23x):
    pass


class AgetByte(Instruction23x):
    pass


class AgetChar(Instruction23x):
    pass


class AgetShort(Instruction23x):
    pass


class Iget(Instruction22c):
    pass


class IgetWide(Instruction22c):
    pass


class IgetObject(Instruction22c):
    pass


class IgetBoolean(Instruction22c):
    pass


class IgetByte(Instruction22c):
    pass


class IgetChar(Instruction22c):
    pass


class IgetShort(Instruction22c):
    pass


class Iput(Instruction22c):
    pass


class IputWide(Instruction22c):
    pass


class IputObject(Instruction22c):
    pass


class IputBoolean(Instruction22c):
    pass


class Sget(Instruction21c):
    pass


class SgetWide(Instruction21c):
    pass


class SgetObject(Instruction21c):
    pass


class SgetBoolean(Instruction21c):
    pass


class SgetByte(Instruction21c):
    pass


class SgetChar(Instruction21c):
    pass


class SgetShort(Instruction21c):
    pass


class Sput(Instruction21c):
    pass


class SputWide(Instruction21c):
    pass


class SputObject(Instruction21c):
    pass


class SputBoolean(Instruction21c):
    pass


class SputByte(Instruction21c):
    pass


class SputChar(Instruction21c):
    pass


class SputShort(Instruction21c):
    pass


class NegInt(Instruction12x):
    pass


class NotInt(Instruction12x):
    pass


class NegLong(Instruction12x):
    pass


class NotLong(Instruction12x):
    pass


class NegFloat(Instruction12x):
    pass


class NegDouble(Instruction12x):
    pass


class IntToLong(Instruction12x):
    pass


class IntToFloat(Instruction12x):
    pass


class IntToDouble(Instruction12x):
    pass


class LongToInt(Instruction12x):
    pass


class LongToFloat(Instruction12x):
    pass


class LongToDouble(Instruction12x):
    pass


class FloatToInt(Instruction12x):
    pass


class FloatToLong(Instruction12x):
    pass


class FloatToDouble(Instruction12x):
    pass


class DoubleToLong(Instruction12x):
    pass


class DoubleToFloat(Instruction12x):
    pass


class IntToByte(Instruction12x):
    pass


class IntToChar(Instruction12x):
    pass


class IntToShort(Instruction12x):
    pass


class AndInt(Instruction23x):
    pass


class OrInt(Instruction23x):
    pass


class XorInt(Instruction23x):
    pass


class ShlInt(Instruction23x):
    pass


class ShrInt(Instruction23x):
    pass


class UshrInt(Instruction23x):
    pass


class AddLong(Instruction23x):
    pass


class SubLong(Instruction23x):
    pass


class MulLong(Instruction23x):
    pass


class DivLong(Instruction23x):
    pass


class RemLong(Instruction23x):
    pass


class AndLong(Instruction23x):
    pass


class OrLong(Instruction23x):
    pass


class XorLong(Instruction23x):
    pass


class ShlLong(Instruction23x):
    pass


class ShrLong(Instruction23x):
    pass


class UshrLong(Instruction23x):
    pass


class AddFloat(Instruction23x):
    pass


class SubFloat(Instruction23x):
    pass


class MulFloat(Instruction23x):
    pass


class DivFloat(Instruction23x):
    pass


class RemFloat(Instruction23x):
    pass


class AddInt2Addr(Instruction12x):
    pass


class SubInt2Addr(Instruction12x):
    pass


class MulInt2Addr(Instruction12x):
    pass


class DivInt2Addr(Instruction12x):
    pass


class RemInt2Addr(Instruction12x):
    pass


class AndInt2Addr(Instruction12x):
    pass


class OrInt2Addr(Instruction12x):
    pass


class XorInt2Addr(Instruction12x):
    pass


class ShlInt2Addr(Instruction12x):
    pass


class ShrInt2Addr(Instruction12x):
    pass


class UshrInt2Addr(Instruction12x):
    pass


class AddLong2Addr(Instruction12x):
    pass


class SubLong2Addr(Instruction12x):
    pass


class MulLong2Addr(Instruction12x):
    pass


class DivLong2Addr(Instruction12x):
    pass


class RemLong2Addr(Instruction12x):
    pass


class AndLong2Addr(Instruction12x):
    pass


class OrLong2Addr(Instruction12x):
    pass


class XorLong2Addr(Instruction12x):
    pass


class ShlLong2Addr(Instruction12x):
    pass


class ShrLong2Addr(Instruction12x):
    pass


class UshrLong2Addr(Instruction12x):
    pass


class AddFloat2Addr(Instruction12x):
    pass


class SubFloat2Addr(Instruction12x):
    pass


class MulFloat2Addr(Instruction12x):
    pass


class DivFloat2Addr(Instruction12x):
    pass


class RemFloat2Addr(Instruction12x):
    pass


class AddDouble2Addr(Instruction12x):
    pass


class SubDouble2Addr(Instruction12x):
    pass


class MulDouble2Addr(Instruction12x):
    pass


class DivDouble2Addr(Instruction12x):
    pass


class RemDouble2Addr(Instruction12x):
    pass


class AddIntLit16(Instruction22s):
    pass


class RsubInt(Instruction22s):
    pass


class MulIntLit16(Instruction22s):
    pass


class DivIntLit16(Instruction22s):
    pass


class RemIntLit16(Instruction22s):
    pass


class AndIntLit16(Instruction22s):
    pass


class OrIntLit16(Instruction22s):
    pass


class XorIntLit16(Instruction22s):
    pass


class AddIntLit8(Instruction22b):
    pass


class RsubIntLit8(Instruction22b):
    pass


class MulIntLit8(Instruction22b):
    pass


class DivIntLit8(Instruction22b):
    pass


class RemIntLit8(Instruction22b):
    pass


class AndIntLit8(Instruction22b):
    pass


class OrIntLit8(Instruction22b):
    pass


class XorIntLit8(Instruction22b):
    pass


class ShlIntLit8(Instruction22b):
    pass


class ShrIntLit8(Instruction22b):
    pass


class UshrIntLit8(Instruction22b):
    pass


class ConstMethodHandle(Instruction21c):
    pass


class ConstMethodType(Instruction21c):
    pass


class Const(Instruction31i):
    pass


class IputByte(Instruction22c):
    pass


class IputChar(Instruction22c):
    pass


class IputShort(Instruction22c):
    pass


INSTRUCTIONS: dict[str, "Type[Instruction]"] = {
    "nop": Nop,
    "return-void": ReturnVoid,
    "move": Move,
    "return": Return,
    "return-object": ReturnObject,
    "return-wide": ReturnWide,
    "monitor-enter": MonitorEnter,
    "monitor-exit": MonitorExit,
    "check-cast": CheckCast,
    "instance-of": InstanceOf,
    "const/4": Const4,
    "const": Const,
    "const/16": Const16,
    "const/high16": ConstHigh16,
    "const-class": ConstClass,
    "const-wide/high16": ConstWideHigh16,
    "const-wide": ConstWide,
    "const-wide/16": ConstWide16,
    "const-wide/32": ConstWide32,
    "const-string": ConstString,
    "const-string/jumbo": ConstStringJumbo,
    "move/from16": MoveFrom16,
    "move/16": Move16,
    "move-object": MoveObject,
    "move-object/from16": MoveObjectFrom16,
    "move-object/16": MoveObject16,
    "move-wide": MoveWide,
    "move-wide/16": MoveWide16,
    "move-wide/from16": MoveWideFrom16,
    "if-ge": IfGe,
    "if-le": IfLe,
    "if-eq": IfEq,
    "if-ne": IfNe,
    "if-lt": IfLt,
    "if-gt": IfGt,
    "if-lez": IfLez,
    "if-eqz": IfEqz,
    "if-nez": IfNez,
    "if-ltz": IfLtz,
    "if-gez": IfGez,
    "if-gtz": IfGtz,
    "goto": Goto,
    "goto/16": Goto16,
    "goto/32": Goto32,
    "add-int": AddInt,
    "sub-int": SubInt,
    "mul-int": MulInt,
    "div-int": DivInt,
    "rem-int": RemInt,
    "add-double": AddDouble,
    "sub-double": SubDouble,
    "mul-double": MulDouble,
    "div-double": DivDouble,
    "rem-double": RemDouble,
    "double-to-int": DoubleToInt,
    "new-array": NewArray,
    "aput": Aput,
    "aput-wide": AputWide,
    "aput-object": AputObject,
    "aput-boolean": AputBoolean,
    "aput-byte": AputByte,
    "aput-char": AputChar,
    "aput-short": AputShort,
    "invoke-virtual": InvokeVirtual,
    "invoke-static": InvokeStatic,
    "invoke-super": InvokeSuper,
    "invoke-direct": InvokeDirect,
    "invoke-interface": InvokeInterface,
    "invoke-polymorphic": InvokePolymorphic,
    "invoke-custom": InvokeCustom,
    "invoke-virtual/range": InvokeVirtualRange,
    "invoke-static/range": InvokeStaticRange,
    "invoke-super/range": InvokeSuperRange,
    "invoke-direct/range": InvokeDirectRange,
    "invoke-interface/range": InvokeInterfaceRange,
    "invoke-polymorphic/range": InvokePolymorphicRange,
    "invoke-custom/range": InvokeCustomRange,
    "move-result": MoveResult,
    "move-result-object": MoveResultObject,
    "move-exception": MoveException,
    "move-result-wide": MoveResultWide,
    "array-length": ArrayLength,
    "new-instance": NewInstance,
    "filled-new-array": FilledNewArray,
    "filled-new-array/range": FilledNewArrayRange,
    "fill-array-data": FillArrayData,
    "throw": Throw,
    "packed-switch": PackedSwitch,
    "sparse-switch": SparseSwitch,
    "cmpl-float": CmplFloat,
    "cmpg-float": CmpgFloat,
    "cmpl-double": CmplDouble,
    "cmpg-double": CmpgDouble,
    "cmp-long": CmpLong,
    "aget": Aget,
    "aget-wide": AgetWide,
    "aget-object": AgetObject,
    "aget-boolean": AgetBoolean,
    "aget-byte": AgetByte,
    "aget-char": AgetChar,
    "aget-short": AgetShort,
    "iget": Iget,
    "iget-wide": IgetWide,
    "iget-object": IgetObject,
    "iget-boolean": IgetBoolean,
    "iget-byte": IgetByte,
    "iget-char": IgetChar,
    "iget-short": IgetShort,
    "iput": Iput,
    "iput-wide": IputWide,
    "iput-object": IputObject,
    "iput-boolean": IputBoolean,
    "iput-byte": IputByte,
    "iput-char": IputChar,
    "iput-short": IputShort,
    "sget": Sget,
    "sget-wide": SgetWide,
    "sget-object": SgetObject,
    "sget-boolean": SgetBoolean,
    "sget-byte": SgetByte,
    "sget-char": SgetChar,
    "sget-short": SgetShort,
    "sput": Sput,
    "sput-wide": SputWide,
    "sput-object": SputObject,
    "sput-boolean": SputBoolean,
    "sput-byte": SputByte,
    "sput-char": SputChar,
    "sput-short": SputShort,
    "neg-int": NegInt,
    "not-int": NotInt,
    "neg-long": NegLong,
    "not-long": NotLong,
    "neg-float": NegFloat,
    "neg-double": NegDouble,
    "int-to-long": IntToLong,
    "int-to-float": IntToFloat,
    "int-to-double": IntToDouble,
    "long-to-int": LongToInt,
    "long-to-float": LongToFloat,
    "long-to-double": LongToDouble,
    "float-to-int": FloatToInt,
    "float-to-long": FloatToLong,
    "float-to-double": FloatToDouble,
    "double-to-long": DoubleToLong,
    "double-to-float": DoubleToFloat,
    "int-to-byte": IntToByte,
    "int-to-char": IntToChar,
    "int-to-short": IntToShort,
    "and-int": AndInt,
    "or-int": OrInt,
    "xor-int": XorInt,
    "shl-int": ShlInt,
    "shr-int": ShrInt,
    "ushr-int": UshrInt,
    "add-long": AddLong,
    "sub-long": SubLong,
    "mul-long": MulLong,
    "div-long": DivLong,
    "rem-long": RemLong,
    "and-long": AndLong,
    "or-long": OrLong,
    "xor-long": XorLong,
    "shl-long": ShlLong,
    "shr-long": ShrLong,
    "ushr-long": UshrLong,
    "add-float": AddFloat,
    "sub-float": SubFloat,
    "mul-float": MulFloat,
    "div-float": DivFloat,
    "rem-float": RemFloat,
    "add-int/2addr": AddInt2Addr,
    "sub-int/2addr": SubInt2Addr,
    "mul-int/2addr": MulInt2Addr,
    "div-int/2addr": DivInt2Addr,
    "rem-int/2addr": RemInt2Addr,
    "and-int/2addr": AndInt2Addr,
    "or-int/2addr": OrInt2Addr,
    "xor-int/2addr": XorInt2Addr,
    "shl-int/2addr": ShlInt2Addr,
    "shr-int/2addr": ShrInt2Addr,
    "ushr-int/2addr": UshrInt2Addr,
    "add-long/2addr": AddLong2Addr,
    "sub-long/2addr": SubLong2Addr,
    "mul-long/2addr": MulLong2Addr,
    "div-long/2addr": DivLong2Addr,
    "rem-long/2addr": RemLong2Addr,
    "and-long/2addr": AndLong2Addr,
    "or-long/2addr": OrLong2Addr,
    "xor-long/2addr": XorLong2Addr,
    "shl-long/2addr": ShlLong2Addr,
    "shr-long/2addr": ShrLong2Addr,
    "ushr-long/2addr": UshrLong2Addr,
    "add-float/2addr": AddFloat2Addr,
    "sub-float/2addr": SubFloat2Addr,
    "mul-float/2addr": MulFloat2Addr,
    "div-float/2addr": DivFloat2Addr,
    "rem-float/2addr": RemFloat2Addr,
    "add-double/2addr": AddDouble2Addr,
    "sub-double/2addr": SubDouble2Addr,
    "mul-double/2addr": MulDouble2Addr,
    "div-double/2addr": DivDouble2Addr,
    "rem-double/2addr": RemDouble2Addr,
    "add-int/lit16": AddIntLit16,
    "rsub-int": RsubInt,
    "mul-int/lit16": MulIntLit16,
    "div-int/lit16": DivIntLit16,
    "rem-int/lit16": RemIntLit16,
    "and-int/lit16": AndIntLit16,
    "or-int/lit16": OrIntLit16,
    "xor-int/lit16": XorIntLit16,
    "add-int/lit8": AddIntLit8,
    "rsub-int/lit8": RsubIntLit8,
    "mul-int/lit8": MulIntLit8,
    "div-int/lit8": DivIntLit8,
    "rem-int/lit8": RemIntLit8,
    "and-int/lit8": AndIntLit8,
    "or-int/lit8": OrIntLit8,
    "xor-int/lit8": XorIntLit8,
    "shl-int/lit8": ShlIntLit8,
    "shr-int/lit8": ShrIntLit8,
    "ushr-int/lit8": UshrIntLit8,
    "const-method-handle": ConstMethodHandle,
    "const-method-type": ConstMethodType,
}

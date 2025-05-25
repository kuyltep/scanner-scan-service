from doctest import SkipDocTestCase
from smalivm.smali.labels import Label, LabelsContext
from smalivm.smali.reader import Reader
from dataclasses import dataclass


@dataclass(slots=True, init=False)
class Directive:
    _name: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        # if this constructor is called, it means the directive is not implemented, so skip line
        next(reader)

    @staticmethod
    def parse(reader: Reader, labels_context: LabelsContext) -> "Directive | None":
        directive: Directive
        data = reader.peek()
        if data is None:
            raise ValueError("No directive name")
        parts = data.split(" ")
        name = parts[0][1:]
        if name in ("end", "restart"):
            name = f"{name} {parts[1]}"
        if name in DIRECTIVES:
            directive = DIRECTIVES[name](reader, labels_context)
        elif name in SKIP_DIRECTIVES:
            SKIP_DIRECTIVES[name](reader, labels_context)
            return None
        else:
            raise ValueError(f"Invalid directive: {name}")
        directive._name = name

        return directive

    def get_name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return f".{self._name}"

    def __repr__(self) -> str:
        return f"Directive({self._name})"


@dataclass(slots=True, init=False)
class Catch(Directive):
    exc_type: str
    start_label: Label
    end_label: Label
    catch_label: Label

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        self.exc_type = data[: data.index("{")].strip()
        labels_data = data[data.index("{") + 1 : data.index("}")]
        start_label, end_label = labels_data.split("..")
        start_label = start_label.strip()[1:]
        end_label = end_label.strip()[1:]
        catch_label = data.split(" ")[-1][1:]
        self.start_label = labels_context.get(start_label)
        self.end_label = labels_context.get(end_label)
        self.catch_label = labels_context.get(catch_label)


@dataclass(slots=True, init=False)
class CatchAll(Directive):
    exc_type: str
    start_label: Label
    end_label: Label
    catch_label: Label

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        catch = Catch(reader, labels_context)
        self.exc_type = catch.exc_type
        self.start_label = catch.start_label
        self.end_label = catch.end_label
        self.catch_label = catch.catch_label


@dataclass(slots=True, init=False)
class Registers(Directive):
    count: int

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        count_str = next(reader).split(" ")[-1]
        self.count = int(count_str)


@dataclass(slots=True, init=False)
class Locals(Directive):
    count: int

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        count_str = next(reader).split(" ")[-1]
        self.count = int(count_str)


@dataclass(slots=True, init=False)
class ArrayData(Directive):
    values: list[str]

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        self.values = []
        next(reader)
        has_end = False
        for item in reader:
            if item == ".end array-data":
                has_end = True
                break
            self.values.append(item)
        if not has_end:
            raise ValueError("ArrayData missing .end array-data")


@dataclass(slots=True, init=False)
class PackedSwitch(Directive):
    labels: dict[int, Label]

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        self.labels = {}
        data = next(reader)
        idx = int(data.split(" ")[1], 16)
        has_end = False
        for item in reader:
            if item == ".end packed-switch":
                has_end = True
                break
            self.labels[idx] = labels_context.get(item[1:])
            idx += 1
        if not has_end:
            raise ValueError("PackedSwitch missing .end packed-switch")


@dataclass(slots=True, init=False)
class SparseSwitch(Directive):
    labels: dict[int, Label]

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        self.labels = {}
        next(reader)
        has_end = False
        for item in reader:
            if item == ".end sparse-switch":
                has_end = True
                break
            idx, label = item.split("->")
            self.labels[int(idx, 16)] = labels_context.get(label.strip()[1:])
        if not has_end:
            raise ValueError("SparseSwitch missing .end sparse-switch")


@dataclass(slots=True, init=False)
class Prologue(Directive):
    pass


@dataclass(slots=True, init=False)
class Line(Directive):
    num: int

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        self.num = int(data.split(" ")[-1])


@dataclass(slots=True, init=False)
class Local(Directive):
    reg: str
    name: str | None = None
    type: str | None = None

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        parts = data.split(",")
        self.reg = parts[0].split(" ")[1]
        if len(parts) > 1:
            data = parts[1].strip()
            self.name, self.type = data.split(":")
            self.name = self.name[1:-1]

    def __str__(self) -> str:
        data = f".{self._name} {self.reg}"
        if self.name and self.type is not None:
            data += f', "{self.name}":{self.type}'
        return data


@dataclass(slots=True, init=False)
class EndLocal(Directive):
    reg: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        self.reg = data[data.rindex(" ") + 1 :]


@dataclass(slots=True, init=False)
class Param(Directive):
    reg: str
    name: str | None
    annotations: list["Annotation"]

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        self.annotations = []
        self._name = "param"
        self.name = None
        data = next(reader)
        # if "#" in data:
        #     data = data[data.index("#") + 1 :]
        parts = data.split(" ")[1:]
        reg = parts[0]
        if reg.endswith(","):
            reg = reg[:-1]
        self.reg = reg
        if len(parts) > 1:
            self.name = parts[1][1:-1]
        lines = []
        multiline = False
        annotation = False
        for line in reader:
            lines.append(line)
            if line is not None:
                if annotation:
                    if line == ".end annotation":
                        annotation = False
                    continue
                if line.startswith(".annotation "):
                    annotation = True
                    continue
                elif line == ".end param":
                    multiline = True
                break
        reader.prepend(*lines)
        if multiline:
            for line in reader:
                if line.startswith(".annotation "):
                    reader.prepend(line)
                    self.annotations.append(Annotation(reader, labels_context))
                elif line == ".end param":
                    break


@dataclass(slots=True, init=False)
class Annotation(Directive):
    visibility: str | None
    name: str
    values: dict[str, "str | list[str] | Annotation"]

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        self._name = "annotation"
        self.values = {}
        self.visibility = None
        data = next(reader)
        parts = data.split(" ")
        if data.startswith(".annotation "):
            self.visibility = parts[1]
            self.name = parts[2]
        elif data.startswith(".subannotation "):
            self.name = parts[1]
        else:
            raise SyntaxError(f'Invalid annotation: "{data}"')

        for line in reader:
            if (
                line == ".end annotation"
                or line == ".end subannotation"
                or line == ".end subannotation,"
            ):
                break

            first_idx = line.index("=")
            var_name = line[:first_idx].strip()
            value = line[first_idx + 1 :].strip()
            if value.startswith(".subannotation "):
                reader.prepend(value)
                subannotation = Annotation(reader, labels_context)
                self.values[var_name] = subannotation
                continue

            if value == "{}":
                self.values[var_name] = []
            elif value == "{":
                values = []
                for line in reader:
                    line = line.strip()
                    if line.startswith(".subannotation "):
                        reader.prepend(line)
                        subannotation = Annotation(reader, labels_context)
                        values.append(subannotation)
                        continue
                    elif line == "}":
                        break
                    elif line.endswith(","):
                        line = line[:-1]
                    values.append(line)
                self.values[var_name] = values
            else:
                self.values[var_name] = value


@dataclass(slots=True, init=False)
class RestartLocal(Directive):
    reg: str

    def __init__(self, reader: Reader, labels_context: LabelsContext) -> None:
        data = next(reader)
        self.reg = data.split(" ")[-1]


DIRECTIVES = {
    "registers": Registers,
    "locals": Locals,
    "catch": Catch,
    "catchall": CatchAll,
    "array-data": ArrayData,
    "packed-switch": PackedSwitch,
    "sparse-switch": SparseSwitch,
    "annotation": Annotation,
}

SKIP_DIRECTIVES = {
    "prologue": Prologue,
    "line": Line,
    "local": Local,
    "end local": EndLocal,
    "param": Param,
    "restart local": RestartLocal,
}

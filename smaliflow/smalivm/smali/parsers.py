from functools import lru_cache
from typing import Type
from smalivm.smali import directives, instructions, labels
from smalivm.smali.reader import Reader
from smalivm.smali.utils import parse_method_parameters
from smalivm.smali.members import Class, Method, Field


class LineParser:
    @staticmethod
    def parse(
        method: "Method", reader: Reader, labels_context: labels.LabelsContext
    ) -> instructions.Instruction | labels.Label | directives.Directive | None:
        result: instructions.Instruction | labels.Label | directives.Directive
        data = reader.peek()
        if data is None:
            raise ValueError("No data to parse")
        if data.startswith("."):
            directive = directives.Directive.parse(reader, labels_context)
            if directive is None:
                return None
            result = directive
        elif data.startswith(":"):
            result = labels.Label.parse(reader, labels_context)
        else:
            result = instructions.Instruction.parse(method, reader, labels_context)

        return result


# class SmaliParser:
#     __files: list[str]
#     # __cache_classes: dict[str, Class]
#     # __cache_strings: dict[str, str]

#     def __init__(self, path: str) -> None:
#         self.__files = []
#         # self.__cache_classes = {}
#         # self.__cache_strings = {}

#         for p, _d, f in os.walk(path):
#             for file in f:
#                 if not file.endswith(".smali"):
#                     continue
#                 file_path = os.path.join(p, file)
#                 self.__files.append(file_path)

#     # def iter_classes(self) -> Iterator[Class]:
#     #     for file in self.__files:
#     #         if file not in self.__cache_classes:
#     #             with open(file, "r") as f:
#     #                 clazz = Class(f)
#     #                 self.__cache_classes[file] = clazz
#     #         yield self.__cache_classes[file]

#     # def iter_strings(self) -> Iterator[str]:
#     #     for file in self.__files:
#     #         if file not in self.__cache_strings:
#     #             strings = smali_parser.extract_strings(file)
#     #             self.__cache_strings[file] = strings
#     #         yield from self.__cache_strings[file]

#     # def get_classes_count(self) -> int:
#     #     return len(self.__files)

#         # return smali_parser.find_smali_strings(smali_dir)
#         # strings: list[str] = []
#         # for file in self.__files:
#         #     with open(file, "r") as f:
#         #         for line in f:
#         #             if line.strip().startswith("const-string "):
#         #                 strings.append(line[line.index('"') + 1 : line.rindex('"')])
#         # return strings


# class Method:
#     _name: str
#     _clazz: "Class"
#     _virtual: bool
#     _direct: bool

#     def get_name(self) -> str:
#         return self._name


# class Class:
#     _name: str
#     _flags: list[str]
#     _super: str
#     _source: str
#     _implements: list[str]
#     _annotations: list[directives.Annotation]
#     _methods: set[Method]

#     def __init__(self) -> None:
#         self._implements = []
#         self._annotations = []

#     def get_name(self) -> str:
#         return self._name


class FieldParser:
    @staticmethod
    def parse(reader: Reader) -> "Field":
        field = Field()
        for line in reader:
            if line.startswith(".field "):
                parts = line.split(" ")
                for idx, part in enumerate(parts[1:]):
                    if ":" in part:
                        parts = parts[idx + 1 :]
                        break
                    field._flags.append(part)
                signature = parts[0].split(":")
                field._name = signature[0]
                field._type = signature[1]
                if len(parts) > 1:
                    field._initial_value = " ".join(parts[2:])
                    if field._type == "Ljava/lang/String;":
                        field._initial_value = field._initial_value[1:-1]

                next_line = reader.peek()
                if next_line is not None and next_line.startswith(".annotation"):
                    for line in reader:
                        if line.startswith(".annotation "):
                            reader.prepend(line)
                            annotation = directives.Annotation(
                                reader, labels.LabelsContext()
                            )
                            field._annotations.append(annotation)
                        elif line == ".end field":
                            break
                        else:
                            raise ValueError(f"Invalid line: {line}")
                break
            else:
                raise ValueError(f"Invalid line: {line}")

        return field


class MethodParser:
    @staticmethod
    def parse(reader: Reader) -> "Method":
        method = Method()
        labels_context = labels.LabelsContext()
        for line in reader:
            line = line.strip()
            if not line:
                continue
            if line.startswith(".method"):
                parts = line.split(" ")[1:]
                signature = parts[-1]
                first_idx = signature.index("(")
                last_idx = signature.rindex(")")
                method._name = signature[:first_idx]
                method._return_type = signature[last_idx + 1 :]
                method._parameters_types = parse_method_parameters(
                    signature[first_idx + 1 : last_idx]
                )
                method._flags = parts[:-1]
                continue
            elif line == ".end method":
                break

            reader.prepend(line)
            ins = LineParser.parse(method, reader, labels_context)
            if isinstance(ins, directives.Registers):
                method._registers_count = ins.count
            elif isinstance(ins, directives.Locals):
                parameters_count = 0
                for param in method._parameters_types:
                    parameters_count += 1
                    if param in ["J", "D"]:
                        parameters_count += 1
                method._registers_count = (
                    ins.count
                    + parameters_count
                    + (1 if "static" not in method._flags else 0)
                )
            elif ins is not None:
                method._instructions.append(ins)

        return method


class ClassParser:
    @staticmethod
    # @lru_cache(maxsize=1000)
    def parse(path: str) -> Type[Class]:
        clazz = type("Class", (Class,), {
            "_implements": [],
            "_annotations": [],
            "_fields": [],
            "_methods": [],
            "_flags": [],
            "_source": None,
            "_super": None,
        })
        with open(path, "r") as f:
            reader = Reader(f)
            direct_methods_section = False
            virtual_methods_section = False
            for line in reader:
                if line.startswith("#"):
                    if line == "# direct methods":
                        direct_methods_section = True
                        continue
                    elif line == "# virtual methods":
                        virtual_methods_section = True
                        continue
                    else:
                        raise ValueError(
                            f"Invalid comment: {line} in class {clazz._name}"
                        )

                if line.startswith(".class "):
                    parts = line.split(" ")
                    clazz._name = parts[-1]
                    clazz._flags = parts[1:-1]
                elif line.startswith(".super "):
                    clazz._super = line.split(" ")[-1]
                elif line.startswith(".source "):
                    clazz._source = line.split(" ")[-1][1:-1]
                elif line.startswith(".implements "):
                    clazz._implements.append(line.split(" ")[-1])
                elif line.startswith(".annotation "):
                    reader.prepend(line)
                    annotation = directives.Annotation(reader, labels.LabelsContext())
                    clazz._annotations.append(annotation)
                elif line.startswith(".field "):
                    reader.prepend(line)
                    field = FieldParser.parse(reader)
                    field._clazz = clazz
                    clazz._fields.append(field)
                elif line.startswith(".method "):
                    reader.prepend(line)
                    method = MethodParser.parse(reader)
                    method._clazz = clazz
                    if virtual_methods_section:
                        method._virtual = True
                    elif direct_methods_section:
                        method._direct = True
                    else:
                        raise ValueError(
                            f"Method {method.get_name()} in class {clazz._name} must be one of virtual or direct"
                        )
                    clazz._methods.append(method)
                else:
                    raise ValueError(
                        f"Invalid line: {line} in class {clazz._name}"
                    )
        return clazz


# class FileParser:
#     @staticmethod
#     def parse(path: str) -> Class:
#         return ClassParser.parse(path)

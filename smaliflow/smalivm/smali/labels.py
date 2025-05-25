from smalivm.smali.reader import Reader
from dataclasses import dataclass


@dataclass(slots=True, init=False)
class Label:
    name: str

    def __init__(self, name: str) -> None:
        if name.startswith(":"):
            raise ValueError(f"Invalid label name: {name}")
        self.name = name

    @staticmethod
    def parse(reader: Reader, labels_context: "LabelsContext") -> "Label":
        name = next(reader)[1:]
        return labels_context.get(name)

    def __str__(self) -> str:
        return f":{self.name}"

    def __repr__(self) -> str:
        return f"Label({self.name})"

    def __hash__(self) -> int:
        return id(self)


@dataclass(slots=True, init=False)
class LabelsContext:
    _labels: dict[str, Label]

    def __init__(self) -> None:
        self._labels = {}

    def get(self, name: str) -> Label:
        if name not in self._labels:
            self._labels[name] = Label(name)
        return self._labels[name]

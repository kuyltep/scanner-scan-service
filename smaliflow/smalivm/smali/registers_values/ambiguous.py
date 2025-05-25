from smalivm.smali.registers import RegisterValue


class AmbiguousValue:
    _values: set[RegisterValue]

    def __init__(self) -> None:
        self._values = set()

    def __repr__(self) -> str:
        return "<ambiguous>"

    def __str__(self) -> str:
        return "<ambiguous>"

    def add_value(self, value: "RegisterValue") -> None:
        self._values.add(value)

    def get_values(self) -> set["RegisterValue"]:
        return self._values

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, AmbiguousValue):
            return False
        return self._values == value._values

    def __hash__(self) -> int:
        return hash(tuple(self._values))

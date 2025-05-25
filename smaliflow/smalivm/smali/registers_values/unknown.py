class UnknownValue:
    def __repr__(self) -> str:
        return "<unknown>"

    def __eq__(self, value: object) -> bool:
        return isinstance(value, UnknownValue)

    def __hash__(self) -> int:
        return id(self)

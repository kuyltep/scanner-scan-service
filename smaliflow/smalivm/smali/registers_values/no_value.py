class NoValue:
    def __hash__(self) -> int:
        return id(self)

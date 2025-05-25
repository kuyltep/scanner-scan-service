import random
from smalivm.framework.base_framework_class import BaseFrameworkClass


class FrameworkClass(BaseFrameworkClass):
    def __init__(self) -> None:
        super().__init__()
        self._source = "Math.java"

        self.flags = ["public", "final"]

    def random(self) -> str:
        return float.hex(random.random())

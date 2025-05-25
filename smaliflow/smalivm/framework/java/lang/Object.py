from typing import Self
from smalivm.framework.base_framework_class import BaseFrameworkClass


class FrameworkClass(BaseFrameworkClass):
    def _init_(self) -> Self:
        self._source = "Object.java"
        return self

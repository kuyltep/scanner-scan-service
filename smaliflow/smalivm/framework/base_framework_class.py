from typing import Self
from smalivm.exceptions import MethodNotFoundError
from smalivm.smali.members import Class
from smalivm.smali.registers import RegisterValue


class BaseFrameworkClass(Class):
    def __init__(self):
        self._methods = []
        self._fields = []
        self._annotations = []
        self._flags = []
        self._implements = []
        self._name = "FrameworkClass"
        self._source = ""
        self._super = ""

    def invoke_method(self, method: str, *args) -> RegisterValue | None:
        method = method.replace("<", "_").replace(">", "_")
        if not self.has_method(method):
            raise MethodNotFoundError(self.get_name(), method)

        value = getattr(self, method)(*args)
        if value is not None and not isinstance(value, RegisterValue):
            value = RegisterValue(value)
        return value

    @property
    def initialized(self) -> bool:
        return True

    # @classmethod
    # def invoke_static_method(cls, method: str, *args) -> RegisterValue | None:
    #     method = method.replace("<", "_").replace(">", "_")
    #     if not cls.has_static_method(method):
    #         raise MethodNotFoundError(cls.name, method)

    #     value = getattr(cls, method)(*args)
    #     if value is not None and not isinstance(value, RegisterValue):
    #         value = RegisterValue(value)
    #     return value

    def has_method(self, method: str) -> bool:
        method = method.replace("<", "_").replace(">", "_")
        return hasattr(self, method)

    # def new_instance(self) -> SmaliClass:
    #     return type(f"{self.__module__}", (self.__class__,), {"_clazz": self})()

    def is_framework(self) -> bool:
        return True

    def __hash__(self) -> int:
        return id(self)

    # @classmethod
    # def has_static_method(cls, method: str) -> bool:
    #     method = method.replace("<", "_").replace(">", "_")
    #     return hasattr(cls, method)

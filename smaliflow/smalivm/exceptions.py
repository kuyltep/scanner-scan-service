class SmaliFlowError(RuntimeError):
    pass


class UnsupportedInstructionError(SmaliFlowError):
    pass


class InvalidRegisterTypeError(SmaliFlowError):
    pass


class InvalidMethodHeaderError(SmaliFlowError):
    pass


class RegisterNotInitialized(SmaliFlowError):
    pass


class RegisterNotFound(SmaliFlowError):
    pass


class RegisterInvalidValue(SmaliFlowError):
    def __init__(self, expected_type: str) -> None:
        super().__init__(f"Register value is not of type {expected_type}")


class MethodNotFoundError(SmaliFlowError):
    def __init__(
        self,
        class_name: str,
        method_name: str,
        method_parameter_types: list[str] | None = None,
    ) -> None:
        if method_parameter_types is None:
            method_parameter_types = []
        super().__init__(
            f"Method {class_name}.{method_name}{''.join(method_parameter_types)} not found"
        )


class ClassNotFoundError(SmaliFlowError):
    def __init__(self, class_name: str) -> None:
        super().__init__(f"Class {class_name} not found")


class MethodResolutionError(SmaliFlowError):

    def __init__(
        self,
        class_name: str,
        method_name: str,
        method_parameter_types: list[str] | None = None,
    ) -> None:
        if method_parameter_types is None:
            method_parameter_types = []
        super().__init__(
            "Method resolution error: %s.%s%s"
            % (class_name, method_name, "".join(method_parameter_types))
        )


class AbstractMethodError(SmaliFlowError):
    pass

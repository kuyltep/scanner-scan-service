import logging

from apk import Apk
from plugins.base_plugin import BasePlugin
from problem import Problem
from smalivm import Vm
from smalivm.smali.directives import Directive
from smalivm.smali.instructions import Instruction, InvokeStatic
from smalivm.smali.labels import Label
from smalivm.smali.registers import RegistersContext


class OutdatedAlgorithms(Problem):
    def __init__(self, ins: Instruction, algorithm: str) -> None:
        super().__init__(f'Outdated cryptographic algorithm "{algorithm}"', ins)


class Plugin(BasePlugin):
    __visited_instructions: set[Instruction]

    def __init__(self) -> None:
        super().__init__()

        self.__visited_instructions = set()

    def __breakpoint(
        self, context: RegistersContext, ins: Instruction | Label | Directive
    ) -> None:
        if ins in self.__visited_instructions:
            return
        if not isinstance(ins, InvokeStatic):
            return
        self.__visited_instructions.add(ins)
        reg_name = ins.registers[0]
        reg = context.get_register(reg_name)
        if not reg.has_value():
            return
        try:
            algorithm = reg.value.get_string()
        except Exception as e:
            logging.error(f"Failed to get algorithm: {e}")
            return
        if algorithm in ["MD5", "SHA-1"]:
            self.problems.append(OutdatedAlgorithms(ins, algorithm))

    def on_start(self, apk: Apk, vm: Vm) -> None:
        self.problems.clear()
        vm.add_breakpoint_by_custom_condition(
            lambda ctx, ins: isinstance(ins, InvokeStatic)
            and ins.method_signature
            == "getInstance(Ljava/lang/String;)Ljava/security/MessageDigest;",
            self.__breakpoint,
        )

    # def run(self, vm: Vm, clazz: Class):
    #     self.__current_class = clazz
    #     for method in clazz.methods:
    #         self.__current_method = method
    #         for ins in method.instructions:
    #             if (
    #                 isinstance(ins, InvokeStatic)
    #                 and ins.method_signature
    #                 == "getInstance(Ljava/lang/String;)Ljava/security/MessageDigest;"
    #             ):
    #                 vm.breakpoints.add(method, ins, self.__breakpoint)
    #                 vm.invoke_method(method)
    #                 vm.breakpoints.remove(method, ins, self.__breakpoint)

import logging

from apk import Apk
from plugins.base_plugin import BasePlugin
from problem import Problem
from smalivm import Vm
from smalivm.smali.directives import Directive
from smalivm.smali.instructions import Instruction, InvokeVirtual, InvokeVirtualRange
from smalivm.smali.labels import Label
from smalivm.smali.registers import RegistersContext


class WorldReadableSharedPrefs(Problem):
    def __init__(self, ins: Instruction) -> None:
        super().__init__("World-readable shared preferences", ins)


class WorldWriteableSharedPrefs(Problem):
    def __init__(self, ins: Instruction) -> None:
        super().__init__("World-writeable shared preferences", ins)


class Plugin(BasePlugin):
    __visited_instructions: set[Instruction]

    def __init__(self) -> None:
        super().__init__()

        self.__visited_instructions = set()

    def __breakpoint(
        self, context: RegistersContext, ins: Instruction | Label | Directive
    ) -> bool | None:
        if ins in self.__visited_instructions:
            return
        if not isinstance(ins, (InvokeVirtual, InvokeVirtualRange)):
            return
        self.__visited_instructions.add(ins)
        reg_name = ins.registers[2]
        reg = context.get_register(reg_name)
        if not reg.has_value():
            return
        try:
            shared_prefs_mode = reg.value.get_int()
        except Exception as e:
            logging.error(f"Failed to get shared prefs mode: {e}")
            return
        if shared_prefs_mode == 1:
            self.problems.append(WorldReadableSharedPrefs(ins))
            return False
        elif shared_prefs_mode == 2:
            self.problems.append(WorldWriteableSharedPrefs(ins))

    def on_start(self, apk: Apk, vm: Vm) -> None:
        self.problems.clear()
        vm.add_breakpoint_by_custom_condition(
            lambda ctx, ins: isinstance(ins, (InvokeVirtual, InvokeVirtualRange))
            and ins.method_signature
            == "getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;",
            self.__breakpoint,
        )

    # def run(self, vm: Vm, clazz: Class) -> None:
    #     self.problems.clear()
    #     self.__current_class = clazz
    #     for method in clazz.methods:
    #         self.__current_method = method
    #         for ins in method.instructions:
    #             if (
    #                 isinstance(ins, (InvokeVirtual, InvokeVirtualRange))
    #                 and ins.method_signature
    #                 == "getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;"
    #             ):
    #                 vm.breakpoints.add(method, ins, self.__breakpoint)
    #                 vm.invoke_method(method)
    #                 vm.breakpoints.remove(method, ins, self.__breakpoint)

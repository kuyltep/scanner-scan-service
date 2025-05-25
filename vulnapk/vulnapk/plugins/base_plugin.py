from apk import Apk
from problem import Problem
from smalivm import Vm
from smalivm.smali.members import Class


class BasePlugin:
    problems: list[Problem]
    enabled: bool = True

    def __init__(self) -> None:
        self.problems = []

    def on_class(self, vm: Vm, clazz: Class) -> None:
        return

    def on_start(self, apk: Apk, vm: Vm) -> None:
        return

    def add_problem(self, problem: Problem) -> None:
        self.problems.append(problem)

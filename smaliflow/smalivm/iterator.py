from typing import Self
from smalivm.smali.directives import Directive
from smalivm.smali.instructions import Instruction
from smalivm.smali.labels import Label


class InstructionsIterator:
    __items: list[Instruction | Label | Directive]
    __pos: int
    __stopped: bool
    __visited_positions: set[int]
    __save_visited_positions: bool = False

    def __init__(self, instructions: list[Instruction | Label | Directive]) -> None:
        self.__items = instructions
        self.__pos = -1
        self.__stopped = False
        self.__visited_positions = set()
        # self.__blocks = {}

        # self.__init_blocks(instructions)

    def save_visited_positions(self, save: bool) -> None:
        self.__save_visited_positions = save

    def get_visited_positions(self) -> set[int]:
        return self.__visited_positions

    def peek(self) -> Instruction | Label | Directive:
        next_pos = self.__pos + 1
        if next_pos >= len(self.__items):
            raise StopIteration
        return self.__items[next_pos]

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> Instruction | Label | Directive:
        if self.__stopped:
            raise StopIteration
        # block_names = list(self.__blocks.keys())
        # for block_name in block_names:
        #     if self.__switched_block is not None:
        #         block_names.insert(0, block_name)
        #         block_name = self.__switched_block
        #         self.__switched_block = None

        #     for ins in self.__blocks[block_name]:
        #         return ins
        self.__pos += 1
        for i, ins in enumerate(self.__items[self.__pos :]):
            i += self.__pos
            if i in self.__visited_positions:
                continue
            if self.__save_visited_positions:
                self.__visited_positions.add(i)
            self.__pos = i
            return ins
        raise StopIteration

    def back(self) -> Instruction | Label | Directive:
        if self.__pos == 0:
            raise StopIteration
        self.__pos -= 1
        return self.__items[self.__pos]

    # def switch_block(self, block_name: str) -> None:
    #     pass

    def index(self, ins: Instruction | Label | Directive) -> int:
        for i, line in enumerate(self.__items):
            if line == ins:
                return i
        return -1

    def get(self, pos: int) -> Instruction | Label | Directive:
        return self.__items[pos]

    def tell(self) -> int:
        return self.__pos

    def seek(self, pos: int):
        self.__pos = pos

    def stop(self) -> None:
        self.__stopped = True

    def is_stopped(self) -> bool:
        return self.__stopped

    def resume(self) -> None:
        self.__stopped = False

    # def save_visited_position(self) -> None:
    #     self.__visited_positions.add(self.__pos)

    def get_instructions(self) -> list[Instruction | Label | Directive]:
        return self.__items

    # def seek(self, ins: Instruction | Label | Directive) -> int:
    #     idx = self.index(ins)
    #     if idx == -1:
    #         raise ValueError(f"Instruction {ins} not found")
    #     self._position = idx
    #     return idx

import os
from typing import Generator


class SmaliParser:
    def __iter_lines(self, path: str) -> Generator[str, None, None]:
        with open(path, "r") as f:
            for line in f.readline():
                yield line

    def iter_methods(
        self, path: str
    ) -> Generator[Generator[str, None, None], None, None]:
        for p, _d, f in os.walk(path):
            for file in f:
                if file.endswith(".smali"):
                    yield self.__iter_lines(os.path.join(p, file))

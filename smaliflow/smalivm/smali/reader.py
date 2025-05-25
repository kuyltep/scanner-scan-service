import re
from typing import Any, Iterator, LiteralString, overload
from more_itertools import peekable
# import cstrip

class Reader:
    __peekable: "peekable[str]"
    _preserve_comments: set[str]

    @overload
    def __init__(self, content: list[str]) -> None: ...
    @overload
    def __init__(self, content: Iterator[str]) -> None: ...
    @overload
    def __init__(self, content: LiteralString) -> None: ...

    def __init__(self, content) -> None:
        if isinstance(content, str):
            content = content.split("\n")
        self.__peekable = peekable(content)
        self._preserve_comments = {
            "# direct methods",
            "# virtual methods",
        }

    def __next__(self) -> str:
        for line in self.__peekable:
            line = self.__clean_line(line)
            if not line:
                continue
            return line
        raise StopIteration

    def __clean_line(self, line: str) -> str:
        if not line:
            return ""
        line = line.strip()
        if "#" in line and line not in self._preserve_comments:
            line = self._remove_comments(line)
        if not line:
            return ""
        return line

    def __iter__(self) -> "Reader":
        return self

    def _remove_comments(self, line: str) -> str:
        if '"' not in line:
            return re.split(r'(?<!\\)#', line, maxsplit=1)[0]

        in_string = False
        result = []

        for i, char in enumerate(line):
            if char == "\\" and i + 1 < len(line) and line[i + 1] == '"':
                result.append(char + line[i + 1])
                continue

            if char == '"':
                in_string = not in_string

            if char == "#" and not in_string:
                break

            result.append(char)

        return "".join(result)

    def peek(self) -> str | None:
        peeked = self.__peekable.peek(None)
        if peeked is None:
            return None
        peeked = self.__clean_line(peeked)
        while not peeked:
            next(self.__peekable)
            peeked = self.__peekable.peek()
            peeked = self.__clean_line(peeked)

        return peeked

    def prepend(self, *items: Any) -> None:
        self.__peekable.prepend(*items)
# from typing import overload
from smalivm.smali.instructions import Instruction
from smalivm.smali.members import Field


# PlaceType = Union[Literal["file", "instruction", "field"]]


class Problem:
    # message: str
    # place: Instruction | Field | str

    # @overload
    # def __init__(self, message: str, place: Instruction) -> None: ...
    # @overload
    # def __init__(self, message: str, place: Field) -> None: ...
    # @overload
    # def __init__(self, message: str, place: str) -> None: ...

    # def __init__(self, message: str, place: Instruction | Field | str) -> None:
    #     self.message = message
    #     self.place = place

    # def __str__(self) -> str:
    #     return f"{self.message} at {self.line}"

    __data: dict[str, str | dict[str, str]]

    def __init__(
        self,
        name: str,
        place: Instruction | Field | str,
        **kwargs: str | dict[str, str]
    ) -> None:
        self.__data = {
            "name": name,
        }

        if isinstance(place, str):
            self.__data["place"] = {
                "type": "file",
                "value": place,
            }
        elif isinstance(place, Field):
            self.__data["place"] = {
                "type": "field",
                "class": place.get_class().get_name(),
                "value": place.get_name(),
            }
        else:
            self.__data["place"] = {
                "type": "instruction",
                "value": str(place),
                "class": place.method.get_class().get_name(),
                "method": place.method.get_name(),
            }

        self.__data.update(kwargs)

    def get_data(self) -> dict[str, str | dict[str, str]]:
        return self.__data

    # def set_name(self, name: str) -> None:
    #     self.__data["name"] = name

    # def set_field(self, key: str, value: Any) -> None:
    #     self.__data[key] = value

    # @overload
    # def set_place(self, place_type: Literal["file"], place: str) -> None: ...
    # @overload
    # def set_place(self, place_type: Literal["instruction"], place: str, clazz: str, method: str) -> None: ...
    # @overload
    # def set_place(self, place_type: Literal["field"], place: str, clazz: str) -> None: ...

    # def set_place(self, place: Instruction | Field | str) -> None:
    #     if isinstance(place, str):
    #         self.__data["place"] = {
    #             "type": "file",
    #             "value": place,
    #         }
    #     elif isinstance(place, Field):
    #         self.__data["place"] = {
    #             "type": "field",
    #             "class": place.get_class().get_name(),
    #             "value": place.get_name(),
    #         }
    #     else:
    #         self.__data["place"] = {
    #             "type": "instruction",
    #             "value": place,
    #             "class": place.method.get_class().get_name(),
    #             "method": place.method.get_name(),
    #         }

    # def set_place(
    #     self, place_type: Literal["file", "instruction", "field"], place: str
    # ) -> None:
    #     self.set_field(
    #         "place",
    #         {
    #             "type": place_type,
    #             "value": place,
    #         },
    #     )

    # def to_dict(self) -> dict[str, str]:
    #     output = {
    #         "message": self.message,
    #     }
    #     if isinstance(self.place, Instruction):
    #         output["method"] = self.place.method.get_signature()
    #         output["instruction"] = str(self.place)
    #     elif isinstance(self.place, Field):
    #         output["field"] = self.place.get_full_signature()
    #     else:
    #         output["place"] = self.place

    #     return output

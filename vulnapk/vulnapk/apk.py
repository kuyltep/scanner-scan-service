import os

from xmlreader import XmlReader


class Apk:
    __path: str

    def __init__(self, path: str) -> None:
        self.__path = path

    def get_smali_dir(self) -> str:
        return os.path.join(self.__path, "smali")

    def get_manifest(self) -> XmlReader:
        manifest_path = os.path.join(self.__path, "AndroidManifest.xml")
        return XmlReader.from_file(manifest_path)

from typing import Any
import bs4


class XmlReader(bs4.BeautifulSoup):
    ANDROID_NS_URI = "http://schemas.android.com/apk/res/android"
    ANDROID_NS_PREFIX = "android"

    @staticmethod
    def from_file(file_path: str):
        content = ""
        with open(file_path, "r+b") as f:
            content = f.read()
        return XmlReader(content, features="xml")

    def to_file(self, file_path: str):
        with open(file_path, "wb") as f:
            f.write(self.encode(encoding="utf8"))

    def find(
        self, name: str | None = None, *args: Any, **kwargs: Any
    ) -> bs4.element.Tag | bs4.element.NavigableString | None:
        if name is not None:
            parts = name.split("/")
            this = self
            for part in parts:
                if this is None:
                    break
                if isinstance(this, XmlReader):
                    this = super(XmlReader, this).find(part, *args, **kwargs)
                else:
                    this = this.find(part, *args, **kwargs)
            return this
        else:
            return super().find(name, *args, **kwargs)

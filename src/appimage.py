import re
import subprocess
from pathlib import Path


class AppImage:
    def __init__(
        self, installer: Path, name: str, has_version_file: bool, icon: Path, exe: Path
    ):
        self.installer = installer
        self.name = name
        self.has_version_file = has_version_file
        self.icon = icon
        self.exe = exe

    def __repr__(self) -> str:
        return f"AppImage(installer={self.installer}, name={self.name}, has_version_file={self.has_version_file}, icon={self.icon}, exe={self.exe})"

    def __eq__(self, value: object) -> bool:
        if isinstance(value, AppImage):
            return self.installer == value.installer
        return False

    def get_version(self) -> str | None:
        if not self.has_version_file:
            # 1.17.10b is the version - below currently captures without b
            try:
                version_output = subprocess.check_output(
                    [self.exe, "--version"]
                ).decode("utf-8")
                print("version_output", version_output)
                version = re.search(r"(\d+\.\d+\.\d+)", version_output).group(1)  # type: ignore #
                print("version", version)
                self.version = version
                return version
            except Exception as e:
                print(f"Unable to get version: {e}")
                return None
        else:
            return self.get_version_from_file()

    def get_version_from_file(self) -> str:
        with open(self.has_version_file) as f:
            # TODO parse the file and look for the version (heroic.desktop, X-AppImage-Version=2.18.1)
            return f.read().strip()

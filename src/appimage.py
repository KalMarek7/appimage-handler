import re
import subprocess
from pathlib import Path

import requests
from packaging.version import Version


class AppImage:
    def __init__(
        self,
        name: str,
        installer: Path,
        latest_release_url: str,
        exe: Path | None = None,
        version_file: Path | None = None,
        version: str | None = None,
        icon: Path | None = None,
    ):
        self.name = name
        self.installer = installer
        self.latest_release_url = latest_release_url
        self.exe = exe
        self.version_file = version_file
        self.version = version
        self.icon = icon

    def __repr__(self) -> str:
        return f"AppImage(name={self.name}, installer={self.installer}, exe={self.exe}, version_file={self.version_file}, version={self.version}, latest_release_url={self.latest_release_url}, icon={self.icon})"

    def __eq__(self, value: object) -> bool:
        if isinstance(value, AppImage):
            return (
                self.name == value.name
                and self.installer == value.installer
                and self.exe == value.exe
                and self.version_file == value.version_file
                and self.version == value.version
                and self.icon == value.icon
                and self.latest_release_url == value.latest_release_url
            )
        return False

    def get_version(self) -> str | None:
        if not self.version_file:
            if self.exe:
                try:
                    version_output = subprocess.check_output(
                        [self.exe, "--version"]
                    ).decode("utf-8")
                    # print("version_output", version_output)
                    # 1.17.10b is zen's version - below currently captures without b
                    version = re.search(r"(\d+\.\d+\.\d+)", version_output).group(1)  # type: ignore
                    print("version:", version)
                    self.version = version
                    return version
                except Exception as e:
                    print(f"Unable to get version: {e}")
                    return None
            else:
                print("Exe not set")
                return None
        else:
            return self._get_version_from_file()

    def update(self) -> None:
        self.version = self.get_version()
        if self.version is None:
            print("Update failed: unable to get version")
            return
        latest_release = self._get_latest_release()
        if latest_release == {}:
            print("Update failed: unable to get latest release")
            return
        print("Everything is good, start the update")
        # TODO Version comparison (using 'packaging')
        if Version(self.version) < Version(latest_release["version"]):
            print("Update available")
            # TODO Download (to some temp dir)
            print("Will start the download from", latest_release["asset_url"])
            # TODO Extract (to existing path (self.exe?), replace all files)
        else:
            print("No update available")

    def _get_version_from_file(self) -> str | None:
        if self.version_file:
            with open(self.version_file) as f:
                try:
                    file_contents = f.read().strip()
                    version = re.search(r"(\d+\.\d+\.\d+)", file_contents).group(1)  # type: ignore
                    print("version:", version)
                    self.version = version
                    return version
                except Exception as e:
                    print(f"Unable to get version from file: {e}")
                    return None

    def _get_latest_release(self) -> dict:
        if self.latest_release_url:
            try:
                response = requests.get(self.latest_release_url)
                if response.status_code == 200:
                    latest_release = {}
                    latest_version = re.search(
                        r"(?:v)?(\d+\.\d+\.\d+)", response.json()["tag_name"]
                    ).group(1)  # type: ignore
                    print("latest_version:", latest_version)
                    latest_release["version"] = latest_version
                    for asset in response.json()["assets"]:
                        if asset["name"] == self.installer.name:
                            latest_release["asset_url"] = asset["browser_download_url"]
                    return latest_release
            except Exception as e:
                print(f"Unable to get latest release: {e}")
                return {}
        print("No latest release url set")
        return {}

    def _download(self, url: str, path: Path) -> None:
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                # Handle File System (I/O) Errors
                try:
                    with open(path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                except OSError as io_error:
                    # Catch PermissionError, Disk Full, Quota Exceeded, etc.
                    error_message = (
                        f"File system error occurred while saving {path}: {io_error}"
                    )
                    raise Exception(error_message)
        except requests.exceptions.RequestException as e:
            error_message = f"Download failed for {url}: {e}"
            raise Exception(error_message)

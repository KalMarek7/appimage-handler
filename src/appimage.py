import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import requests
from packaging.version import Version

from src.config import CONFIG


class AppImage:
    def __init__(
        self,
        name: str,
        base_dir: Path,
        latest_release_url: str,
        version_file: Path | None = None,
        version: str | None = None,
        icon: Path | None = None,
    ):
        self.name = name
        self.base_dir = base_dir
        self.latest_release_url = latest_release_url
        self.version_file = version_file
        self.version = version
        self.icon = icon

    def __repr__(self) -> str:
        return f"AppImage(name={self.name}, base_dir={self.base_dir}, latest_release_url={self.latest_release_url} version_file={self.version_file}, version={self.version}, icon={self.icon})"

    def __eq__(self, value: object) -> bool:
        if isinstance(value, AppImage):
            return (
                self.name == value.name
                and self.base_dir == value.base_dir
                and self.latest_release_url == value.latest_release_url
                and self.version_file == value.version_file
                and self.version == value.version
                and self.icon == value.icon
            )
        return False

    def get_version(self) -> str | None:
        if not self.version_file:
            try:
                path = self.base_dir / self.name
                version_output = subprocess.check_output([path, "--version"]).decode(
                    "utf-8"
                )
                # 1.17.10b is zen's version - below currently captures without b
                version = re.search(r"(\d+\.\d+\.\d+)", version_output).group(1)  # type: ignore
                print("version:", version)
                self.version = version
                return version
            except Exception as e:
                print(f"Unable to get version: {e}")
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
        if Version(self.version) < Version(latest_release["version"]):
            print("Update available")
            print("Will start the download from", latest_release["asset_url"])
            self._download(latest_release["asset_url"], latest_release["asset_name"])
            self._extract(latest_release["asset_name"])
            print("Done")
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
                        # Find asset with .AppImage extension and containing x86_64 or x86 architecture
                        if (
                            asset["name"].endswith(".AppImage")
                            and "x86_64" in asset["name"]
                        ):
                            latest_release["asset_url"] = asset["browser_download_url"]
                            latest_release["asset_name"] = asset["name"]
                        # Error handling?
                    return latest_release
            except Exception as e:
                print(f"Unable to get latest release: {e}")
                return {}
        print("No latest release url set")
        return {}

    def _download(self, url: str, filename: str) -> None:
        print(CONFIG.get("paths", {}))
        path = CONFIG.get("paths", {}).get("download", {}).get("path", "/tmp")
        path = Path(path) / filename
        print("Downloading", url, "to", path)
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                try:
                    with open(path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                except OSError as io_error:
                    error_message = (
                        f"File system error occurred while saving {path}: {io_error}"
                    )
                    raise Exception(error_message)
        except requests.exceptions.RequestException as e:
            error_message = f"Download failed for {url}: {e}"
            raise Exception(error_message)

    def _extract(self, filename: str) -> str:
        download_dir = CONFIG.get("paths", {}).get("download", {}).get("path", "/tmp")
        path = Path(download_dir) / filename
        print("Extracting", path)
        # --- 1. Set Executable Permission ---
        try:
            current_stat = os.stat(path)
            new_mode = current_stat.st_mode | stat.S_IXUSR
            os.chmod(path, new_mode)
            print(f"Set executable permission on: {path}")
        except Exception as e:
            raise Exception(f"Unable to set executable permission on {path}: {e}")
        # --- 2. Extract ---
        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"Extracting to: {tmpdir}")
            try:
                extract_output = subprocess.check_output(
                    [
                        path,
                        "--appimage-extract",
                    ],
                    cwd=Path(tmpdir),
                ).decode("utf-8")
                print(f"EXTRACTED TO {tmpdir}\n{extract_output}")
            except Exception as e:
                raise Exception(f"Unable to extract {path}: {e}")
            # --- 3. Move ---
            self._move(f"{tmpdir}/squashfs-root")
            return "Extracted to " + tmpdir

    def _move(self, temp_path: str) -> None:
        to_path = Path(self.base_dir)
        print("Moving", temp_path, "to", to_path)
        if to_path.is_dir():
            try:
                if to_path:
                    shutil.rmtree(to_path)
                    os.mkdir(to_path)
                for item_name in os.listdir(temp_path):
                    source_item = Path(temp_path) / item_name
                    destination_item = to_path / item_name
                    shutil.move(str(source_item), str(destination_item))
            except Exception as e:
                raise Exception(f"Unable to move {temp_path} to {to_path}: {e}")
        else:
            raise Exception(f"{to_path} is not a directory")

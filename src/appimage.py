import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

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
        if self.version_file:
            return self._get_version_from_file(self.version_file)

        version = self._get_version_from_cli()
        if version:
            return version

        version = self._get_version_from_desktop_file()
        if version:
            return version

        raise Exception(
            f"Failed to obtain version for {self.name}. The app might not be installed. Check .desktop entry or consider adding a version_file to the config."
        )

    def update(self) -> None:
        try:
            self.version = self.get_version()
        except Exception as e:
            raise Exception(f"Update failed: {e}")
        latest_release = self._get_latest_release()
        if latest_release == {}:
            print("Update failed: unable to get latest release")
            return
        print("Everything is good, start the update")
        if self.version:
            if Version(self.version) < Version(latest_release["version"]):
                print("Update available")
                print("Will start the download from", latest_release["asset_url"])
                self._download(
                    latest_release["asset_url"], latest_release["asset_name"]
                )
                self._extract(latest_release["asset_name"])
                self._inject_version_line(
                    Path(f"{self.base_dir / self.name}.desktop"),
                    latest_release["asset_name"],
                )
                print("Done")
            else:
                print("No update available")

    def install(self) -> None:
        latest_release = self._get_latest_release()
        if latest_release == {}:
            print("Install failed: unable to get latest release")
            return
        print("Everything is good, start the install")
        print("Will start the download from", latest_release["asset_url"])
        self._download(latest_release["asset_url"], latest_release["asset_name"])
        self._extract(latest_release["asset_name"])
        files = self._create_desktop_entry(latest_release["asset_name"])
        if files:
            self._inject_wm_class_line(files[0], files[1])
        print("Done")

    def remove(self) -> None:
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
            print(f"Removed {self.base_dir}")
        else:
            print(f"{self.base_dir} does not exist.")
        self._remove_desktop_entry()
        print("Done")

    def _remove_desktop_entry(self) -> None:
        applications_path = Path(
            CONFIG.get("paths", {}).get("desktop", {}).get("path", {})
        ).expanduser()
        desktop_entry_path = applications_path / f"{self.name}.desktop"
        if desktop_entry_path.exists():
            os.remove(desktop_entry_path)
            print(f"Removed {desktop_entry_path}")
        else:
            print(f"{desktop_entry_path} does not exist.")

    def _get_version_from_cli(self) -> str | None:
        print("Running --version")
        path = self.base_dir / self.name
        if not self.base_dir.exists():
            print(f"Directory {self.base_dir} doesn't exist. The app is not installed.")
            return None
        if not path.exists():
            print(f"File {path} doesn't exist.")
            return None
        try:
            version_output = subprocess.check_output([path, "--version"]).decode(
                "utf-8"
            )
            # Improved regex to capture versions like 1.2.3, 1.2.3a, 1.2
            match = re.search(r"(\d+(?:\.\d+)+[a-zA-Z]*)", version_output)
            if match:
                version = match.group(1)
                print("version:", version)
                self.version = version
                return version
            else:
                print(f"No version match found in output: {version_output}")
                return None
        except subprocess.CalledProcessError as e:
            print(f"Failed to get version from CLI: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def _get_version_from_desktop_file(self) -> str | None:
        print("No version_file set. Looking for .desktop entry.")
        if not self.base_dir.exists():
            return None
        for i in os.listdir(self.base_dir):
            if i.endswith(".desktop"):
                print(f"Found {i}")
                return self._get_version_from_file(self.base_dir / i)
        else:
            print("No .desktop file found")
            return None

    def _get_version_from_file(self, file_path: Path) -> str | None:
        print(f"Attempting to get version from file: {file_path}")
        try:
            with open(file_path) as f:
                file_contents = f.read().strip()
                # Improved regex to capture versions like 1.2.3, 1.2.3a, 1.2
                match = re.search(r"(\d+(?:\.\d+)+[a-zA-Z]*)", file_contents)
                if match:
                    version = match.group(1)
                    print("version:", version)
                    self.version = version
                    return version
                else:
                    print(f"No version match found in {f.name}")
                    return None
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except Exception as e:
            print(f"Unable to get version from file {file_path}: {e}")
            return None

    def _get_latest_release(self) -> dict:
        if self.latest_release_url:
            try:
                response = requests.get(self.latest_release_url)
                if response.status_code == 200:
                    latest_release = {}
                    latest_version = re.search(
                        r"(?:v)?(\d+(?:\.\d+)+[a-zA-Z]*)", response.json()["tag_name"]
                    ).group(1)  # type: ignore
                    print("latest_version:", latest_version)
                    latest_release["version"] = latest_version
                    # Github API
                    if urlparse(self.latest_release_url).netloc == "api.github.com":
                        for asset in response.json()["assets"]:
                            # Find asset with .AppImage extension and containing x86_64 or x86 architecture
                            if asset["name"].endswith(".AppImage") and (
                                "x86_64" in asset["name"] or "x64" in asset["name"]
                            ):
                                latest_release["asset_url"] = asset[
                                    "browser_download_url"
                                ]
                                latest_release["asset_name"] = asset["name"]
                                break
                        else:
                            raise Exception(
                                "No x86_64 AppImage found in Github API response"
                            )
                    # Gitlab API (only 1 app (missioncenter) tested
                    elif urlparse(self.latest_release_url).netloc == "gitlab.com":
                        for link in response.json()["assets"]["links"]:
                            if "AppImage" in link["name"] and "x86_64" in link["name"]:
                                latest_release["asset_url"] = link["url"]
                                filename = re.search(
                                    r"[\w.-]+\.AppImage$", link["url"]
                                ).group()  # type: ignore
                                latest_release["asset_name"] = filename
                                break
                        else:
                            raise Exception(
                                "No x86_64 AppImage found in Gitlab API response"
                            )
                    return latest_release
                else:
                    print(
                        f"Not 200 response from {self.latest_release_url}. Response: {response.status_code} - {response.reason}"
                    )
                    return {}
            except Exception as e:
                print(f"Error in _get_latest_release: {e}")
                return {}
        print("No latest release url set")
        return {}

    def _download(self, url: str, filename: str) -> None:
        print(CONFIG.get("paths", {}))
        path = CONFIG.get("paths", {}).get("download", {}).get("path", "/tmp")
        path = Path(path).expanduser() / filename
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
        path = Path(download_dir).expanduser() / filename
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
            self._move_to_base_dir(f"{tmpdir}/squashfs-root")
            return "Extracted to " + tmpdir

    def _move_to_base_dir(self, temp_path: str) -> None:
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
            print(f"{to_path} is not a directory")
            os.mkdir(to_path)
            for item_name in os.listdir(temp_path):
                source_item = Path(temp_path) / item_name
                destination_item = to_path / item_name
                shutil.move(str(source_item), str(destination_item))

    def _create_desktop_entry(
        self, downloaded_file_name: str
    ) -> tuple[Path, Path] | None:
        desktop_entry_path = self.base_dir / f"{self.name}.desktop"
        print(f"Looking for .desktop entry at {desktop_entry_path}")
        applications_path = Path(
            CONFIG.get("paths", {}).get("desktop", {}).get("path", {})
        ).expanduser()
        if desktop_entry_path.is_file():
            print(
                f"Desktop entry already exists. Copying {desktop_entry_path} to {applications_path}"
            )
            if applications_path.is_dir():
                shutil.copy(desktop_entry_path, applications_path)
            self._replace_exec_and_icon_lines(
                desktop_entry_path, applications_path / f"{self.name}.desktop"
            )
            self._inject_version_line(
                applications_path / f"{self.name}.desktop", downloaded_file_name
            )
            self._inject_version_line(desktop_entry_path, downloaded_file_name)
            return (desktop_entry_path, desktop_entry_path)
        else:
            # TODO: create .desktop entry?
            """
            [Desktop Entry]
            Type=Application
            Name=My App Name
            Exec=/path/to/executable
            Icon=/path/to/icon.png
            """
            print(f"No {self.name}.desktop entry found in extracted files.")
            print("Looking for any .desktop entries in extracted files")
            for i in os.listdir(self.base_dir):
                if i.endswith(".desktop"):
                    print(f"Found {i}")
                    shutil.copy(
                        self.base_dir / i, applications_path / f"{self.name}.desktop"
                    )
                    self._replace_exec_and_icon_lines(
                        self.base_dir / i, applications_path / f"{self.name}.desktop"
                    )
                    self._inject_version_line(
                        applications_path / f"{self.name}.desktop", downloaded_file_name
                    )
                    return (
                        applications_path / f"{self.name}.desktop",
                        self.base_dir / i,
                    )

    def _replace_exec_and_icon_lines(
        self, source_path: Path, destination_path: Path
    ) -> None:
        print("Replacing Exec and Icon lines in .desktop entry")
        with open(source_path, "r") as f:
            lines = f.readlines()
        with open(destination_path, "w") as f:
            for line in lines:
                if line.startswith("Exec="):
                    print("Found Exec line:", line.strip())
                    s = line.split(" ")
                    # s[0] = f"Exec={self.base_dir}/{self.name}"
                    if (self.base_dir / self.name).exists():
                        s[0] = (
                            f"Exec={self.base_dir}/{self.name}{'\n' if len(s) == 1 else ''}"
                        )
                        line = " ".join(s)
                    elif (self.base_dir / "AppRun").exists():
                        s[0] = (
                            f"Exec={self.base_dir}/AppRun{'\n' if len(s) == 1 else ''}"
                        )
                        line = " ".join(s)
                elif line.startswith("Icon="):
                    print("Found Icon line:", line.strip())
                    if self.icon:
                        line = f"Icon={self.icon}\n"
                    else:
                        line = f"Icon={self.base_dir}/.DirIcon\n"
                f.write(line)

    def _inject_version_line(
        self, desktop_file: Path, downloaded_file_name: str
    ) -> None:
        replaced = False
        print("Injecting version line in .desktop entry")
        with open(desktop_file, "r") as fr:
            lines = fr.readlines()
        with open(desktop_file, "w") as f:
            for line in lines:
                desktop_match = re.search(r"(\d+(?:\.\d+)+[a-zA-Z]*)", line)
                filename_match = re.search(
                    r"(\d+(?:\.\d+)+[a-zA-Z]*)", downloaded_file_name
                )
                if desktop_match and filename_match:
                    desktop_version = desktop_match.group(1)
                    print("Desktop version:", desktop_version, f)
                    filename_version = filename_match.group(1)
                    print("Filename version:", filename_version, f)
                    line = f"Version={filename_version}\n"
                    f.write(line)
                    print("Replaced version in .desktop entry at", desktop_file)
                    replaced = True
                else:
                    f.write(line)
            if not replaced:
                print("No version found in file:", desktop_file)
                print(
                    "Looking for version in downloaded file name:", downloaded_file_name
                )
                match = re.search(r"(\d+(?:\.\d+)+[a-zA-Z]*)", downloaded_file_name)
                if match:
                    version = match.group(1)
                    print("version:", version, f)
                    f.seek(0, os.SEEK_END)
                    f.write(f"Version={version}\n")
                    print("Appended version in .desktop entry at", desktop_file)
                else:
                    print(
                        "No version found in downloaded file name:",
                        downloaded_file_name,
                    )

    def _inject_wm_class_line(
        self, desktop_file: Path, original_file_name: Path
    ) -> None:
        StartupWMClass = original_file_name.stem
        print(StartupWMClass)
        replaced = False
        print("Injecting wm_class line in .desktop entry")
        with open(desktop_file, "r") as fr:
            lines = fr.readlines()
        with open(desktop_file, "w") as f:
            for line in lines:
                if line.startswith("StartupWMClass="):
                    print("Found StartupWMClass line:", line.strip())
                    line = f"StartupWMClass={StartupWMClass}\n"
                    f.write(line)
                    replaced = True
                else:
                    f.write(line)
            if not replaced:
                print("No StartupWMClass found in file:", desktop_file)
                line = f"StartupWMClass={StartupWMClass}\n"
                f.write(line)

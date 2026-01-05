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
            if not self.version:
                print("Update failed: could not determine current version.")
                return
        except Exception as e:
            raise Exception(f"Update failed: {e}")

        latest_release = self._get_latest_release()
        if not latest_release:
            print("Update failed: unable to get latest release information.")
            return

        if Version(self.version) >= Version(latest_release["version"]):
            print("No update available.")
            return

        print("Update available. Starting download...")
        self._download(latest_release["asset_url"], latest_release["asset_name"])
        self._extract(latest_release["asset_name"])
        self._inject_version_line(
            Path(f"{self.base_dir / self.name}.desktop"),
            latest_release["asset_name"],
        )
        print("Update complete.")

    def install(self) -> None:
        latest_release = self._get_latest_release()
        if not latest_release:
            print("Install failed: unable to get latest release information.")
            return

        print("Starting install...")
        self._download(latest_release["asset_url"], latest_release["asset_name"])
        self._extract(latest_release["asset_name"])
        desktop_files = self._create_desktop_entry(latest_release["asset_name"])
        if desktop_files:
            self._inject_wm_class_line(desktop_files[0], desktop_files[1])
        print("Install complete.")

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
        if not self.latest_release_url:
            print("No latest release url set")
            return {}

        try:
            response = requests.get(self.latest_release_url)
            response.raise_for_status()
            data = response.json()

            hostname = urlparse(self.latest_release_url).netloc
            if "api.github.com" in hostname:
                return self._get_latest_from_github(data)
            elif "gitlab.com" in hostname:
                return self._get_latest_from_gitlab(data)
            else:
                print(f"Unsupported provider: {hostname}")
                return {}
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch latest release: {e}")
            return {}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return {}

    def _get_latest_from_github(self, data: dict) -> dict:
        latest_release = {}
        tag_name = data.get("tag_name", "")
        version_match = re.search(r"(?:v)?(\d+(?:\.\d+)+[a-zA-Z]*)", tag_name)
        if not version_match:
            raise Exception("Could not find version in tag name")
        latest_release["version"] = version_match.group(1)

        for asset in data.get("assets", []):
            if asset.get("name", "").endswith(".AppImage") and (
                "x86_64" in asset.get("name", "") or "x64" in asset.get("name", "")
            ):
                latest_release["asset_url"] = asset.get("browser_download_url")
                latest_release["asset_name"] = asset.get("name")
                return latest_release
        raise Exception("No compatible AppImage found in GitHub release")

    def _get_latest_from_gitlab(self, data: dict) -> dict:
        latest_release = {}
        tag_name = data.get("tag_name", "")
        version_match = re.search(r"(?:v)?(\d+(?:\.\d+)+[a-zA-Z]*)", tag_name)
        if not version_match:
            raise Exception("Could not find version in tag name")
        latest_release["version"] = version_match.group(1)

        for link in data.get("assets", {}).get("links", []):
            if "AppImage" in link.get("name", "") and "x86_64" in link.get("name", ""):
                latest_release["asset_url"] = link.get("url")
                filename_match = re.search(r"[\w.-]+\.AppImage$", link.get("url", ""))
                if filename_match:
                    latest_release["asset_name"] = filename_match.group()
                    return latest_release
        raise Exception("No compatible AppImage found in GitLab release")

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
            path.chmod(path.stat().st_mode | stat.S_IXUSR)
            print(f"Set executable permission on: {path}")
        except OSError as e:
            raise Exception(
                f"Unable to set executable permission on {path}: {e}"
            ) from e
        # --- 2. Extract ---
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            print(f"Extracting to: {tmpdir_path}")
            try:
                extract_output = subprocess.check_output(
                    [
                        path,
                        "--appimage-extract",
                    ],
                    cwd=tmpdir_path,
                ).decode("utf-8")
                print(f"EXTRACTED TO {tmpdir_path}\n{extract_output}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise Exception(f"Unable to extract {path}: {e}") from e
            # --- 3. Move ---
            self._move_to_base_dir(tmpdir_path / "squashfs-root")
            return f"Extracted to {tmpdir_path}"

    def _move_to_base_dir(self, from_path: Path) -> None:
        to_path = self.base_dir
        print(f"Moving {from_path} to {to_path}")
        try:
            if to_path.exists():
                shutil.rmtree(to_path)
            shutil.move(str(from_path), str(to_path))
        except OSError as e:
            raise Exception(f"Unable to move {from_path} to {to_path}: {e}") from e

    def _create_desktop_entry(
        self, downloaded_file_name: str
    ) -> tuple[Path, Path] | None:
        local_desktop_candidate_path = self.base_dir / f"{self.name}.desktop"
        applications_path = Path(
            CONFIG.get("paths", {}).get("desktop", {}).get("path", {})
        ).expanduser()
        global_desktop_path = applications_path / f"{self.name}.desktop"

        desktop_file_to_copy = None

        if local_desktop_candidate_path.is_file():
            print(f"Desktop entry found locally: {local_desktop_candidate_path}.")
            desktop_file_to_copy = local_desktop_candidate_path
        else:
            print(
                f"No {self.name}.desktop entry found locally. Checking for any .desktop files in extracted directory."
            )
            for item in os.listdir(self.base_dir):
                if item.endswith(".desktop"):
                    extracted_desktop_path = self.base_dir / item
                    print(f"Found {extracted_desktop_path} in extracted files.")
                    desktop_file_to_copy = extracted_desktop_path
                    break  # Use the first one found

        if desktop_file_to_copy:
            print(f"Copying {desktop_file_to_copy} to {global_desktop_path}")
            if applications_path.is_dir():
                shutil.copy(desktop_file_to_copy, global_desktop_path)
            self._replace_exec_and_icon_lines(desktop_file_to_copy, global_desktop_path)
            self._inject_version_line(global_desktop_path, downloaded_file_name)
            return (global_desktop_path, desktop_file_to_copy)
        else:
            print(
                f"No .desktop entry found in {self.base_dir} to create an entry for {self.name}."
            )
            return None

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
        print("Injecting version line in .desktop entry")
        version_match = re.search(r"(\d+(?:\.\d+)+[a-zA-Z]*)", downloaded_file_name)
        if not version_match:
            print("No version found in downloaded file name:", downloaded_file_name)
            return

        new_version = version_match.group(1)
        lines = []
        found_version = False
        try:
            with open(desktop_file, "r") as f:
                lines = f.readlines()

            with open(desktop_file, "w") as f:
                for line in lines:
                    if line.startswith("Version="):
                        f.write(f"Version={new_version}\n")
                        found_version = True
                    else:
                        f.write(line)
                if not found_version:
                    f.write(f"Version={new_version}\n")
            print("Successfully injected version in .desktop entry at", desktop_file)
        except FileNotFoundError:
            print(f"File not found: {desktop_file}")

    def _inject_wm_class_line(
        self, desktop_file: Path, original_file_name: Path
    ) -> None:
        StartupWMClass = original_file_name.stem
        print(StartupWMClass)
        replaced = False
        print("Injecting wm_class line in .desktop entry")
        try:
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
        except FileNotFoundError:
            print(f"File not found: {desktop_file}")

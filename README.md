# AppImage Handler

A simple CLI tool to manage AppImage applications.

## Overview

This tool is developed with and for Ubuntu 24.04.3 LTS to automate the process of 'installing', updating and removing AppImage applications. It works by reading a `config.toml` file where you define the applications you want to manage. For each application, it checks for new versions on GitHub or Gitlab latest releases, and if an update is found, it downloads and extracts the new AppImage, replacing the old version.

## Features

-   **Manage Multiple Applications**: Configure and manage multiple AppImage applications.
-   **Simple Configuration**: Uses a simple TOML file for configuration.
-   **Install AppImages**: Download and extract AppImages from the latest release page.
-   **Update AppImages**: Check for new versions of your AppImages from the latest release page and update them.
-   **Remove AppImages**: Remove installed AppImages.
-   **CLI Interface**: All functions are available through a simple command-line interface.

## Installation using uv

1. Clone the repository and make sure you're in the root directory.
2. Create the Environment:

```bash
uv venv
```

3. Install the dependencies:

```bash
uv sync
```

## Configuration

Create a configuration file at `~/.config/appimage-handler/config.toml`. Refer to `example_config.toml`.

```toml
[paths.download]
path = "~/Downloads/App Installers"

[paths.desktop]
path = "~/.local/share/applications"

[apps.zen]
name = "zen"
base_dir = "~/.local/share/zen"
latest_release_url = "https://api.github.com/repos/zen-browser/desktop/releases/latest"
# optional
user_data_dir = "~/.zen" # not used, just for reference
icon = "zen"

[apps.heroic]
name = "heroic"
base_dir = "~/.local/share/heroic"
latest_release_url = "https://api.github.com/repos/Heroic-Games-Launcher/HeroicGamesLauncher/releases/latest"
version_file = "~/.local/share/heroic/heroic.desktop"
user_data_dir = "~/.config/heroic"
icon = "~/.local/share/heroic/resources/app.asar.unpacked/build/icon-light.png"

[apps.protonup]
name = "protonup"
base_dir = "~/.local/share/protonup"
latest_release_url = "https://api.github.com/repos/DavidoTek/ProtonUp-Qt/releases/latest"

[apps.peazip]
name = "peazip"
base_dir = "~/.local/share/peazip"
latest_release_url = "https://api.github.com/repos/ferion11/PeaZip_Appimage/releases/latest"

[apps.missioncenter]
name = "missioncenter"
base_dir = "~/.local/share/missioncenter"
latest_release_url = "https://gitlab.com/api/v4/projects/mission-center-devs%2Fmission-center/releases/permalink/latest"

[apps.audacity]
name = "audacity"
base_dir = "~/.local/share/audacity"
latest_release_url = "https://api.github.com/repos/audacity/audacity/releases/latests"
```

## Usage

The main entry point is `src/main.py`. You can run it directly with `uv run -m src.main` or create an alias. Refer to `main.sh`.

```bash
#!/bin/bash
uv run -m src.main "$@"
```

Run `uv run -m src.main --help` for more information.

# AppImage Handler

A simple CLI tool to manage AppImage applications on Ubuntu.

## Overview

This tool is developed with and for Ubuntu to automate the process of 'installing', updating and removing AppImage applications. It works by reading a `config.toml` file where you define the applications you want to manage. For each application, it checks for new versions on GitHub or Gitlab latest releases, and if an update is found, it downloads and extracts the new AppImage, replacing the old version.

Tested on Ubuntu 24 and 26 LTS releases.

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

### Commands

The script provides several commands to manage your AppImages. In all commands, if you do not specify an application name, the command will be run for all applications defined in your `config.toml`.

#### `list`

Lists all the applications that are configured in your `config.toml` file.

#### `install`

Installs one or more applications. The installation process involves downloading the latest AppImage release, extracting it, and creating a desktop entry.

#### `update`

Updates one or more applications. The update process checks for a new version, downloads it, and replaces the existing installation.

#### `version`

Displays the currently installed version of one or more applications.

#### `remove`

Removes one or more applications. This will delete the application directory and its desktop entry.

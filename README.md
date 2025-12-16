# AppImage Handler

A simple CLI tool to manage and update your AppImage applications.

## Overview

This tool is designed for Linux systems like Ubuntu 24.04.3 LTS to automate the process of updating AppImage applications. It works by reading a `config.toml` file where you define the applications you want to manage. For each application, it checks for new versions from sources like GitHub, and if an update is found, it downloads and extracts the new AppImage, replacing the old version.

## Features

-   **Update AppImages**: Check for new versions of your AppImages from a GitHub release page and update them.
-   **Manage Multiple Applications**: Configure and manage multiple AppImage applications.
-   **Simple Configuration**: Uses a simple TOML file for configuration.
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
user_data_dir = "~/.zen"

[apps.heroic]
name = "heroic"
base_dir = "~/.local/share/heroic"
latest_release_url = "https://api.github.com/repos/Heroic-Games-Launcher/HeroicGamesLauncher/releases/latest"
version_file = "~/.local/share/heroic/heroic.desktop"
user_data_dir = "~/.config/heroic"
```

## Usage

The main entry point is `src/main.py`. You can run it directly with `uv run -m src.main` or create an alias.

```bash
#!/bin/bash
uv run -m src.main "$@"
```

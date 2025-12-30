from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from src.appimage import AppImage
from src.config import CONFIG

app = typer.Typer(
    help="Tool to handle .AppImage updates.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def get_app(app_name: str) -> AppImage | None:
    """
    Retrieves an AppImage object from the configuration.
    """
    apps_config = CONFIG.get("apps", {})
    app_details = apps_config.get(app_name)
    typer.echo(f"App details: {app_details}")

    if not app_details:
        typer.echo(f"Error: App '{app_name}' not found in configuration.", err=True)
        return None

    return AppImage(
        name=app_name,
        base_dir=Path(app_details.get("base_dir")).expanduser(),
        latest_release_url=app_details.get("latest_release_url"),
        version_file=(
            Path(app_details.get("version_file")).expanduser()
            if app_details.get("version_file")
            else None
        ),
        icon=Path(app_details.get("icon")).expanduser()
        if app_details.get("icon")
        else None,
    )


@app.command(name="list", help="List all configured applications.")
def list_apps():
    """
    Lists all applications found in the config file.
    """
    apps_config = CONFIG.get("apps", {})
    if not apps_config:
        typer.echo("No applications configured in your config.toml. Nothing to do.")
        raise typer.Exit()

    typer.echo("Configured applications:")
    for app_name in apps_config.keys():
        typer.echo(f"- {app_name}")


@app.command(help="Update one or all applications.")
def update(
    app_name: Annotated[
        Optional[str],
        typer.Argument(
            help="The name of the app to update. If not provided, all apps will be updated."
        ),
    ] = None,
):
    """
    Updates a specific application or all of them.
    """
    apps_config = CONFIG.get("apps", {})
    if not apps_config:
        typer.echo("No applications configured in your config.toml. Nothing to do.")
        raise typer.Exit()

    if app_name:
        app_to_update = get_app(app_name)
        if app_to_update:
            typer.echo(f"Checking for updates for {app_name}...")
            app_to_update.update()
    else:
        typer.echo("Updating all configured applications...")
        for name in apps_config.keys():
            app_to_update = get_app(name)
            if app_to_update:
                typer.echo(f"Checking for updates for {name}...")
                app_to_update.update()
                typer.echo("-" * 20)


@app.command(
    help="Get the currently installed version of an application or all applications."
)
def version(
    app_name: Annotated[
        Optional[str],
        typer.Argument(
            help="The name of the app to get the version of. If not provided, all apps will be updated."
        ),
    ] = None,
):
    """
    Gets the version of a specific application or all of them.
    """
    apps_config = CONFIG.get("apps", {})
    if not apps_config:
        typer.echo("No applications configured in your config.toml. Nothing to do.")
        raise typer.Exit()

    if app_name:
        app_to_get = get_app(app_name)
        if app_to_get:
            typer.echo(f"Getting version for {app_name}...")
            version = app_to_get.get_version()
            typer.echo(f"{app_name} version: {version}")
    else:
        typer.echo("Getting version for all configured applications...")
        for name in apps_config.keys():
            app_to_get = get_app(name)
            if app_to_get:
                typer.echo(f"Getting version for {name}...")
                version = app_to_get.get_version()
                typer.echo(f"{name} version: {version}")
                typer.echo("-" * 20)


@app.command(help="Install one or all applications.")
def install(
    app_name: Annotated[
        Optional[str],
        typer.Argument(
            help="The name of the app to install. If not provided, all apps will be installed."
        ),
    ] = None,
):
    """
    Installs a specific application or all of them.
    """
    apps_config = CONFIG.get("apps", {})
    if not apps_config:
        typer.echo("No applications configured in your config.toml. Nothing to do.")
        raise typer.Exit()

    if app_name:
        app_to_install = get_app(app_name)
        if app_to_install:
            typer.echo(f"Installing {app_name}...")
            app_to_install.install()
    else:
        typer.echo("Installing all configured applications...")
        for name in apps_config.keys():
            app_to_install = get_app(name)
            if app_to_install:
                typer.echo(f"Installing {name}...")
                app_to_install.install()
                typer.echo("-" * 20)


def main():
    app()


if __name__ == "__main__":
    main()

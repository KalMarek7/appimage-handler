from pathlib import Path
from typing import Callable, List, Optional

import typer
from typing_extensions import Annotated

from src.appimage import AppImage
from src.config import CONFIG

app = typer.Typer(
    help="Tool to manage .AppImage applications.",
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


def _process_apps(
    app_names: Optional[List[str]],
    action_func: Callable[[AppImage], None],
    all_msg: str,
):
    """
    Helper function to process one or more applications.
    """
    apps_config = CONFIG.get("apps", {})
    if not apps_config:
        typer.echo("No applications configured in your config.toml. Nothing to do.")
        raise typer.Exit()

    apps_to_process = app_names if app_names else apps_config.keys()
    if not app_names:
        typer.echo(all_msg)

    for app_name in apps_to_process:
        app = get_app(app_name)
        if app:
            try:
                action_func(app)
            except Exception as e:
                typer.echo(f"Error processing {app_name}: {e}", err=True)
            typer.echo("-" * 20)


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


@app.command(help="Update one or more applications.")
def update(
    app_names: Annotated[
        Optional[List[str]],
        typer.Argument(
            help="The names of the apps to update. If not provided, all apps will be updated."
        ),
    ] = None,
):
    """
    Updates one or more applications.
    """

    def update_action(app: AppImage):
        typer.echo(f"Checking for updates for {app.name}...")
        app.update()

    _process_apps(app_names, update_action, "Updating all configured applications...")


@app.command(help="Get the currently installed version of one or more applications.")
def version(
    app_names: Annotated[
        Optional[List[str]],
        typer.Argument(
            help="The names of the apps to get the version of. If not provided, all apps will be processed."
        ),
    ] = None,
):
    """
    Gets the version of one or more applications.
    """

    def version_action(app: AppImage):
        typer.echo(f"Getting version for {app.name}...")
        version = app.get_version()
        typer.echo(f"{app.name} version: {version}")

    _process_apps(
        app_names, version_action, "Getting version for all configured applications..."
    )


@app.command(help="Install one or more applications.")
def install(
    app_names: Annotated[
        Optional[List[str]],
        typer.Argument(
            help="The names of the apps to install. If not provided, all apps will be installed."
        ),
    ] = None,
):
    """
    Installs one or more applications.
    """

    def install_action(app: AppImage):
        typer.echo(f"Installing {app.name}...")
        app.install()

    _process_apps(
        app_names, install_action, "Installing all configured applications..."
    )


@app.command(help="Remove one or more applications.")
def remove(
    app_names: Annotated[
        Optional[List[str]],
        typer.Argument(
            help="The names of the apps to remove. If not provided, all apps will be removed."
        ),
    ] = None,
):
    """
    Removes one or more applications.
    """

    def remove_action(app: AppImage):
        typer.echo(f"Removing {app.name}...")
        app.remove()

    _process_apps(app_names, remove_action, "Removing all configured applications...")


def main():
    app()


if __name__ == "__main__":
    main()

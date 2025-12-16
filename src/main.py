from pathlib import Path

from src.appimage import AppImage
from src.config import CONFIG


def main():
    """
    Loads AppImage configurations and performs actions on them.
    """
    apps_config = CONFIG.get("apps", {})
    print(apps_config)
    if not apps_config:
        print("No applications configured in your config.toml. Nothing to do.")
        return
    for app_name, app_details in apps_config.items():
        print(f"Checking for updates for {app_name}...")
        if app_name == "zen":
            app = AppImage(
                name=app_name,
                base_dir=Path(app_details.get("base_dir")).expanduser(),
                latest_release_url=app_details.get("latest_release_url"),
            )
            print(app)
            app.update()


if __name__ == "__main__":
    main()

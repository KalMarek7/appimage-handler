import tomllib
from pathlib import Path


def load_config() -> dict:
    """
    Loads the TOML configuration file from the default path.

    The expected path is ~/.config/appimage-handler/config.toml.
    If the file doesn't exist, it returns an empty dictionary.
    """
    config_path = Path.home() / ".config" / "appimage_handler" / "example_config.toml"
    if not config_path.is_file():
        # You could also implement default values here
        return {}

    with open(config_path, "rb") as f:
        try:
            return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            print(f"Error: Could not parse {config_path}: {e}")
            return {}


# Load the configuration once when this module is first imported
CONFIG = load_config()

if __name__ == "__main__":
    print(CONFIG)

import unittest
from pathlib import Path

from src.appimage import AppImage


class TestInstall(unittest.TestCase):
    def test_install(self):
        appimage = AppImage(
            name="zen",
            base_dir=Path("~/.local/share/zen").expanduser(),
            latest_release_url="https://api.github.com/repos/zen-browser/desktop/releases/latest",
        )
        appimage.install()


if __name__ == "__main__":
    unittest.main()

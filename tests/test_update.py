import unittest
from pathlib import Path

from src.appimage import AppImage


class TestUpdate(unittest.TestCase):
    def test_update(self):
        print("Testing update")
        appimage = AppImage(
            name="zen",
            base_dir=Path("/home/marek/.local/share/zen"),
            latest_release_url="https://api.github.com/repos/zen-browser/desktop/releases/latest",
        )
        appimage.update()
        self.assertTrue(
            Path("/home/marek/Downloads/App Installers/scripts/zen").exists()
        )
        # self.assertEqual(appimage._get_latest_release().get("version"), "1.17.13")
        """ appimage._download(
            "https://github.com/zen-browser/desktop/releases/download/1.17.14b/zen-x86_64.AppImage",
            Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage"),
        ) """
        """ appimage2 = AppImage(
            name="heroic",
            installer=Path(
                "/home/marek/Downloads/App Installers/Heroic-2.18.1-linux-x86_64.AppImage"
            ),
            latest_release_url="https://api.github.com/repos/Heroic-Games-Launcher/HeroicGamesLauncher/releases/latest",
            version_file=Path("/home/marek/.local/share/heroic/heroic.desktop"),
        ) """
        """ appimage2._download(
            "https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher/releases/download/v2.18.1/Heroic-2.18.1-linux-x86_64.AppImage",
            Path(
                "/home/marek/Downloads/App Installers/Heroic-2.18.1-linux-x86_64.AppImage"
            ),
        ) """
        # appimage2.update()
        # self.assertEqual(appimage2.version, "2.18.1")
        # self.assertEqual(appimage2._get_latest_release().get("version"), "2.18.1")


if __name__ == "__main__":
    unittest.main()

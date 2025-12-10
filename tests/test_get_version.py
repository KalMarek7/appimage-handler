import unittest
from pathlib import Path

from src.appimage import AppImage


class TestAppImage(unittest.TestCase):
    """
    Test the AppImage class init, repr and eq
    """

    def test_appimage_init(self):
        print("Testing AppImage init, repr and eq")
        appimage = AppImage(
            name="zen",
            installer=Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage"),
        )
        print(appimage)
        self.assertEqual(
            appimage,
            AppImage(
                "zen",
                Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage"),
                None,
                None,
                None,
                None,
                None,
            ),
        )


class TestGetVersion(unittest.TestCase):
    def test_get_version(self):
        print("Testing get_version")
        appimage = AppImage(
            name="zen",
            installer=Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage"),
            exe=Path("/home/marek/.local/share/zen/zen"),
        )
        version = appimage.get_version()
        self.assertEqual(version, "1.17.10")

    def test_get_version_from_file(self):
        print("Testing get_version_from_file")
        appimage = AppImage(
            name="heroic",
            installer=Path(
                "/home/marek/Downloads/App Installers/Heroic-2.18.1-linux-x86_64.AppImage"
            ),
            version_file=Path("/home/marek/.local/share/heroic/heroic.desktop"),
        )
        version = appimage._get_version_from_file()
        self.assertEqual(version, "2.18.1")


class TestGetLatestRelease(unittest.TestCase):
    def test_get_latest_release(self):
        print("Testing get_latest_release")
        appimage = AppImage(
            name="zen",
            installer=Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage"),
            latest_release_url="https://api.github.com/repos/zen-browser/desktop/releases/latest",
        )
        version = appimage._get_latest_release()
        self.assertEqual(version, "1.17.12")


class TestUpdate(unittest.TestCase):
    def test_update(self):
        print("Testing update")
        appimage = AppImage(
            name="zen",
            installer=Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage"),
            exe=Path("/home/marek/.local/share/zen/zen"),
            latest_release_url="https://api.github.com/repos/zen-browser/desktop/releases/latest",
        )
        appimage.update()
        self.assertEqual(appimage.version, "1.17.10")
        self.assertEqual(appimage._get_latest_release(), "1.17.12")
        appimage2 = AppImage(
            name="heroic",
            installer=Path(
                "/home/marek/Downloads/App Installers/Heroic-2.18.1-linux-x86_64.AppImage"
            ),
            version_file=Path("/home/marek/.local/share/heroic/heroic.desktop"),
            latest_release_url="https://api.github.com/repos/Heroic-Games-Launcher/HeroicGamesLauncher/releases/latest",
        )
        appimage2.update()
        self.assertEqual(appimage2.version, "2.18.1")
        self.assertEqual(appimage2._get_latest_release(), "2.18.1")


if __name__ == "__main__":
    unittest.main()

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
            base_dir=Path("/home/marek/.local/share/zen"),
            latest_release_url="https://api.github.com/repos/zen-browser/desktop/releases/latest",
        )
        print(appimage)
        self.assertEqual(
            appimage,
            AppImage(
                "zen",
                Path("/home/marek/.local/share/zen"),
                "https://api.github.com/repos/zen-browser/desktop/releases/latest",
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
            base_dir=Path("/home/marek/.local/share/zen"),
            latest_release_url="https://api.github.com/repos/zen-browser/desktop/releases/latest",
        )
        version = appimage.get_version()
        self.assertEqual(version, "1.17.10")

    def test_get_version_from_file(self):
        print("Testing get_version_from_file")
        appimage = AppImage(
            name="heroic",
            base_dir=Path("/home/marek/.local/share/heroic"),
            latest_release_url="https://api.github.com/repos/Heroic-Games-Launcher/HeroicGamesLauncher/releases/latest",
            version_file=Path("/home/marek/.local/share/heroic/heroic.desktop"),
        )
        version = appimage._get_version_from_file()
        self.assertEqual(version, "2.18.1")


class TestGetLatestRelease(unittest.TestCase):
    def test_get_latest_release(self):
        print("Testing _get_latest_release")
        appimage = AppImage(
            name="zen",
            base_dir=Path("/home/marek/.local/share/zen"),
            latest_release_url="https://api.github.com/repos/zen-browser/desktop/releases/latest",
        )
        latest_release = appimage._get_latest_release()
        self.assertEqual(latest_release.get("version"), "1.17.14")
        self.assertEqual(
            latest_release.get("asset_url"),
            "https://github.com/zen-browser/desktop/releases/download/1.17.14b/zen-x86_64.AppImage",
        )
        appimage2 = AppImage(
            name="heroic",
            base_dir=Path("/home/marek/.local/share/heroic"),
            latest_release_url="https://api.github.com/repos/Heroic-Games-Launcher/HeroicGamesLauncher/releases/latest",
            version_file=Path("/home/marek/.local/share/heroic/heroic.desktop"),
        )
        self.assertEqual(appimage2._get_latest_release().get("version"), "2.18.1")
        self.assertEqual(
            appimage2._get_latest_release().get("asset_url"),
            "https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher/releases/download/v2.18.1/Heroic-2.18.1-linux-x86_64.AppImage",
        )


class TestDownload(unittest.TestCase):
    def test_download(self):
        print("Testing download")
        appimage = AppImage(
            name="zen",
            base_dir=Path("/home/marek/.local/share/zen"),
            latest_release_url="https://api.github.com/repos/zen-browser/desktop/releases/latest",
        )
        appimage._download(
            "https://github.com/zen-browser/desktop/releases/download/1.17.14b/zen-x86_64.AppImage",
            "zen-x86_64.AppImage",
        )
        self.assertTrue(
            Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage").exists()
        )


class TestExtract(unittest.TestCase):
    def test_extract_and_move(self):
        print("Testing extract")
        appimage = AppImage(
            name="zen",
            base_dir=Path("/home/marek/.local/share/zen"),
            latest_release_url="https://api.github.com/repos/zen-browser/desktop/releases/latest",
        )
        print(appimage._extract("zen-x86_64.AppImage"))
        self.assertTrue(
            Path("/home/marek/Downloads/App Installers/scripts/zen").exists()
        )
        """ appimage = AppImage(
            name="heroic",
            base_dir=Path("/home/marek/.local/share/heroic"),
            latest_release_url="https://api.github.com/repos/Heroic-Games-Launcher/HeroicGamesLauncher/releases/latest",
            version_file=Path("/home/marek/.local/share/heroic/heroic.desktop"),
        )
        print(appimage._extract("Heroic-2.18.1-linux-x86_64.AppImage"))
        self.assertTrue(
            Path("/home/marek/Downloads/App Installers/scripts/heroic").exists()
        ) """


if __name__ == "__main__":
    unittest.main()

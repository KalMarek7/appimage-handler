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
            installer=Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage"),
            name="zen",
            has_version_file=False,
            icon=Path("/home/marek/.local/share/zen/zen.png"),
            exe=Path("/home/marek/.local/share/zen/zen"),
        )
        print(appimage)
        self.assertEqual(
            appimage,
            AppImage(
                Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage"),
                "zen",
                False,
                Path("/home/marek/.local/share/zen/zen.png"),
                Path("/home/marek/.local/share/zen/zen"),
            ),
        )


class TestGetVersion(unittest.TestCase):
    def test_get_version(self):
        print("Testing get_version")
        appimage = AppImage(
            installer=Path("/home/marek/Downloads/App Installers/zen-x86_64.AppImage"),
            name="zen",
            has_version_file=False,
            icon=Path("/home/marek/.local/share/zen/zen.png"),
            exe=Path("/home/marek/.local/share/zen/zen"),
        )
        version = appimage.get_version()
        self.assertEqual(version, "1.17.10")


if __name__ == "__main__":
    unittest.main()

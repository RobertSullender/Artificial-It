from pathlib import Path

from PyQt6.QtWidgets import QApplication


class ThemeManager:
    THEMES = {
        "Dark": "dark.qss",
        "Light": "light.qss",
        "Blue": "blue.qss",
    }

    def __init__(self, app: QApplication):
        self.app = app
        self.current_theme = None

        # Path to:
        # src/ui/themes/
        self.themes_directory = Path(__file__).parent / "themes"

    def apply_theme(self, theme_name: str):
        if theme_name not in self.THEMES:
            raise ValueError(f"Unknown theme: {theme_name}")

        theme_file = self.themes_directory / self.THEMES[theme_name]

        if not theme_file.exists():
            raise FileNotFoundError(
                f"Theme file not found: {theme_file}"
            )

        stylesheet = theme_file.read_text(encoding="utf-8")
        self.app.setStyleSheet(stylesheet)
        self.current_theme = theme_name

# SPDX-License-Identifier: MIT
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.loop_manager import instance as loop_manager
from ui.theme_manager import ThemeManager


def main():
    app = QApplication(sys.argv)
    theme_manager = ThemeManager(app)
    theme_manager.apply_theme("Dark")
    
    # Start the asyncio background loop
    loop_manager.start()
    
    try:
        window = MainWindow(theme_manager)
        window.show()
        sys.exit(app.exec())
    finally:
        # Ensure loop is stopped on exit
        loop_manager.stop()

if __name__ == "__main__":
    main()
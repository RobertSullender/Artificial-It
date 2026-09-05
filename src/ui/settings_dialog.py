# SPDX-License-Identifier: MIT
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout

from utils.config_manager import settings


class SettingsDialog(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(360, 180)
        self.resize(400, 210)

        layout = QFormLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setHorizontalSpacing(16)

        self.theme_input = QComboBox()
        self.theme_input.addItems(list(theme_manager.THEMES))
        self.theme_input.setCurrentText(theme_manager.current_theme or "Dark")
        layout.addRow("Theme:", self.theme_input)

        self.preview_input = QCheckBox("Live denoising preview")
        self.preview_input.setChecked(settings.get("ui.live_preview", True))
        layout.addRow("Preview:", self.preview_input)

        self.resources_input = QCheckBox("Resource monitoring")
        self.resources_input.setChecked(settings.get("ui.resource_monitor", True))
        layout.addRow("Resources:", self.resources_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self):
        settings.set("ui.live_preview", self.preview_input.isChecked())
        settings.set("ui.resource_monitor", self.resources_input.isChecked())
        self.theme_manager.apply_theme(self.theme_input.currentText())
        super().accept()
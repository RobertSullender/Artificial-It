# SPDX-License-Identifier: MIT
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
class PreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Image Preview Label
        self.image_label = QLabel("No image preview available")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(""
            "background-color: #2b2b2b;"
            "border: 1px solid #444;"
            "border-radius: 4px;"
            "min-height: 300px;"
            "")
        self.layout.addWidget(self.image_label)

        # Text Preview Area (Hidden by default, can be toggled or used for chat/logs)
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setPlaceholderText("Text output will appear here...")
        self.text_preview.setVisible(False)  # Hide by default, can be shown for Talk-2-It
        self.layout.addWidget(self.text_preview)

    def display_image(self, image_path):
        """Displays an image and hides the text area."""
        # Ensure the image label is visible (it might have been hidden by a progress message)
        self.image_label.setVisible(True)
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
                # Scale image to fit label while keeping aspect ratio
                scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.text_preview.setVisible(False)
        else:
            self.image_label.setText("Failed to load image.")

    def display_text(self, text):
        """Displays text and hides the image preview."""
        self.text_preview.setPlainText(text)
        self.text_preview.setVisible(True)
        self.image_label.setVisible(False)

    def toggle_view(self, mode="image"):
        """Manually switch between image and text views."""
        if mode == "image":
            self.image_label.setVisible(True)
            self.text_preview.setVisible(False)
        else:
            self.image_label.setVisible(False)
            self.text_preview.setVisible(True)


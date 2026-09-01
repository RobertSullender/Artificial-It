# SPDX-License-Identifier: MIT
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt

class Talk2ItTab(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Header
        header = QLabel("Talk-2-It")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(header)

        # Not_Implemented message - displayed immediately on tab load
        self.status_label = QLabel("Not_Implemented: Coming Soon!")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            background-color: #2b2b2b;
            color: #ff6b6b;
            padding: 40px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            margin: 20px;
        """)
        self.layout.addWidget(self.status_label)

    # Tab is not implemented - no interaction possible

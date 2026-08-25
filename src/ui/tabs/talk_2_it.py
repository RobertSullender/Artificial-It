# SPDX-License-Identifier: MIT
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout, QLineEdit, QPushButton
from ui.components.preview_widget import PreviewWidget
import uuid

class Talk2ItTab(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.layout = QVBoxLayout(self)

        # Header
        header = QLabel("Talk-2-It")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(header)

        # Chat History Area
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("Conversation will appear here...")
        self.layout.addWidget(self.chat_history)

        # Input Area
        input_layout = QHBoxLayout()
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Ask something...")
        self.send_button = QPushButton("Send")
        
        input_layout.addWidget(self.user_input)
        input_layout.addWidget(self.send_button)
        self.layout.addLayout(input_layout)

        # Preview Area
        self.preview = PreviewWidget()
        self.layout.addWidget(self.preview)

        # Connect button
        self.send_button.clicked.connect(self.handle_send)
        
        # Connect engine signals
        self.engine.progress_updated.connect(self.on_progress_updated)
        self.engine.task_completed.connect(self.on_task_completed)

    def handle_send(self):
        text = self.user_input.text()
        if text:
            self.chat_history.append(f"<b>User:</b> {text}")
            self.user_input.clear()
            
            # Submit to engine
            task_id = str(uuid.uuid4())
            params = {
                'model': 'default_llm',  # Placeholder model name
                'prompt': text,
                'steps': 1  # LLMs usually don't have "steps" like diffusion but for now we use it
            }
            self.engine.submit_task(task_id, params)

    def on_progress_updated(self, data):
        status = data.get('status', '')
        if "Processing" in status:
             self.chat_history.append(f"<i>AI is thinking... ({status})</i>")

    def on_task_completed(self, task_id, result):
        self.chat_history.append(f"<b>AI:</b> {result}")

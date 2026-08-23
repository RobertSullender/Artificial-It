from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
from ui.components.preview_widget import PreviewWidget
import uuid

class StructureItTab(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.layout = QVBoxLayout(self)

        # Header
        header = QLabel("Structure-It")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(header)

        # Configuration Area (Simplified for now)
        config_layout = QVBoxLayout()
        self.info_label = QLabel("Select a reference structure or ControlNet map.")
        config_layout.addWidget(self.info_label)

        btn_layout = QHBoxLayout()
        self.upload_button = QPushButton("Upload Reference")
        self.apply_button = QPushButton("Apply Structure")
        btn_layout.addWidget(self.upload_button)
        btn_layout.addWidget(self.apply_button)
        config_layout.addLayout(btn_layout)

        self.layout.addLayout(config_layout)

        # Preview Area for the structure map
        self.preview = PreviewWidget()
        self.layout.addWidget(self.preview)

        # Connect buttons
        self.upload_button.clicked.connect(self.handle_upload)
        self.apply_button.clicked.connect(self.handle_apply)

        # Connect engine signals
        self.engine.progress_updated.connect(self.on_progress_updated)
        self.engine.task_completed.connect(self.on_task_completed)

    def handle_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Reference Image", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.preview.display_image(file_path)
            self.info_label.setText(f"Loaded: {file_path.split('/')[-1]}")

    def handle_apply(self):
        # Submit a task to the engine
        task_id = str(uuid.uuid4())
        params = {
            'model': 'default_controlnet', # Placeholder model name
            'prompt': "Apply structure guidance",
            'steps': 5
        }
        self.engine.submit_task(task_id, params)

    def on_progress_updated(self, data):
        status = data.get('status', '')
        self.preview.display_text(f"Status: {status}")

    def on_task_completed(self, task_id, result):
        self.preview.display_text(f"Done! Result: {result}")

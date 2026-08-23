from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox
from PyQt6.QtCore import Qt
from ui.components.preview_widget import PreviewWidget
import uuid

class TrainItTab(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.layout = QVBoxLayout(self)

        # Header
        header = QLabel("Train-It")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(header)

        # Parameters Area
        params_layout = QVBoxLayout()
        params_layout.addWidget(QLabel("Training Configuration"))

        # Learning Rate Slider
        lr_layout = QHBoxLayout()
        lr_layout.addWidget(QLabel("Learning Rate:"))
        self.lr_slider = QSlider(Qt.Orientation.Horizontal)
        self.lr_slider.setRange(1, 1000)  # Representing values like 1e-5 to 1e-1
        lr_layout.addWidget(self.lr_slider)
        params_layout.addLayout(lr_layout)

        # Epochs SpinBox
        epoch_layout = QHBoxLayout()
        epoch_layout.addWidget(QLabel("Epochs:"))
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 5000)
        epoch_layout.addWidget(self.epochs_spin)
        params_layout.addLayout(epoch_layout)

        # Start Button
        self.train_button = QPushButton("Start Training")
        self.train_button.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px;")
        params_layout.addWidget(self.train_button)

        self.layout.addLayout(params_layout)

        # Preview Area (For training progress/logs)
        self.preview = PreviewWidget()
        self.layout.addWidget(self.preview)

        # Connect button
        self.train_button.clicked.connect(self.handle_train)

        # Connect engine signals
        self.engine.progress_updated.connect(self.on_progress_updated)
        self.engine.task_completed.connect(self.on_task_completed)

    def handle_train(self):
        lr = self.lr_slider.value()
        epochs = self.epochs_spin.value()
        
        # Submit a task to the engine
        task_id = str(uuid.uuid4())
        params = {
            'model': 'default_train_model', # Placeholder model name
            'prompt': f"Training with LR: {lr}, Epochs: {epochs}",
            'steps': epochs
        }
        self.engine.submit_task(task_id, params)

    def on_progress_updated(self, data):
        status = data.get('status', '')
        self.preview.display_text(f"Status: {status}")

    def on_task_completed(self, task_id, result):
        self.preview.display_text(f"Training Complete! Result: {result}")

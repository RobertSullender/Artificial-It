from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QFormLayout, QSpinBox, QComboBox)
from PyQt6.QtCore import QTimer, QDateTime
from ui.components.preview_widget import PreviewWidget
from utils.token_counter import TokenCounter
from core.model_manager import ModelManager
import uuid
import os

class ImagineItTab(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        # Get model manager from the engine's attributes or pass it in
        self.model_manager = engine.model_manager
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self._current_image_path = None

        # Header
        header = QLabel("Imagine-It")
        header.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(header)

        # --- PERSISTENT INPUT SECTION ---
        input_group = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Model Selection Row (New!)
        self.model_selector = QComboBox()
        self.model_selector.addItems(self.model_manager.list_all_models())
        self.model_selector.currentTextChanged.connect(self.on_model_changed)
        form_layout.addRow("Model:", self.model_selector)

        # Primary Prompt Area
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Enter your prompt here...")
        self.prompt_input.setMinimumHeight(45)
        self.prompt_token_count = QLabel("0 / 77")
        self.prompt_token_count.setStyleSheet("color: #888;")
        form_layout.addRow("Prompt:", self.prompt_input)
        form_layout.addRow("", self.prompt_token_count)

        self.negative_prompt_input = QLineEdit()
        self.negative_prompt_input.setPlaceholderText("Enter negative prompt...")
        self.negative_prompt_input.setMinimumHeight(40)
        self.negative_token_count = QLabel("0 / 77")
        self.negative_token_count.setStyleSheet("color: #888;")
        form_layout.addRow("Negative Prompt:", self.negative_prompt_input)
        form_layout.addRow("", self.negative_token_count)

        # Pro Parameters Row 1: Seed, Steps, CFG
        seed_layout = QHBoxLayout()
        self.seed_input = QSpinBox()
        self.seed_input.setRange(-1, 2147483647)
        self.seed_input.setSuffix(" (Seed)")
        self.seed_input.setValue(-1)
        
        self.steps_input = QSpinBox()
        self.steps_input.setRange(1, 200)
        self.steps_input.setSuffix(" Steps")
        self.steps_input.setValue(20)

        self.cfg_input = QSpinBox()
        self.cfg_input.setRange(1, 30)
        self.cfg_input.setSuffix(" CFG")
        self.cfg_input.setValue(7)

        seed_layout.addWidget(self.seed_input)
        seed_layout.addWidget(self.steps_input)
        seed_layout.addWidget(self.cfg_input)
        form_layout.addRow("Parameters:", seed_layout)

        # Pro Parameters Row 2: Resolution, Sampler
        res_layout = QHBoxLayout()
        self.width_input = QSpinBox()
        self.width_input.setRange(64, 2048)
        self.width_input.setValue(512)
        self.width_input.setSuffix(" W")

        self.height_input = QSpinBox()
        self.height_input.setRange(64, 2048)
        self.height_input.setValue(512)
        self.height_input.setSuffix(" H")

        self.sampler_input = QComboBox()
        self.sampler_input.addItems(["Euler a", "DPM++ 2M", "DDIM", "Euler", "UniPC"])
        # Default will be set by on_model_changed
        
        res_layout.addWidget(self.width_input)
        res_layout.addWidget(self.height_input)
        res_layout.addWidget(QLabel(" | ")) 
        res_layout.addWidget(self.sampler_input)
        form_layout.addRow("Resolution & Sampler:", res_layout)

        input_group.addLayout(form_layout)

        # Generate Button
        self.generate_button = QPushButton("Generate")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setStyleSheet("font-weight: bold; background-color: #4a90e2; color: white;")
        input_group.addWidget(self.generate_button)
        
        self.layout.addLayout(input_group)

        # --- STATUS SECTION ---
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #aaa; font-style: italic;")
        self.layout.addWidget(self.status_label)


        # Connect signals
        self.generate_button.clicked.connect(self.handle_generation)
        self.engine.progress_updated.connect(self.on_progress_updated)
        self.engine.task_completed.connect(self.on_task_completed)

        # Token Count Signals
        self.prompt_input.textChanged.connect(lambda text: self.update_token_counts())
        self.negative_prompt_input.textChanged.connect(lambda text: self.update_token_counts())

        # Initialize defaults for the current selection
        if self.model_selector.currentText():
            self.on_model_changed(self.model_selector.currentText())

    def on_model_changed(self, model_name):     
        meta = self.model_manager.models.get(model_name)
        if meta:
            available_samplers = [self.sampler_input.itemText(i) for i in range(self.sampler_input.count())]
            if meta.default_sampler in available_samplers:
                self.sampler_input.setCurrentText(meta.default_sampler)
            else:
                self.sampler_input.setCurrentText("Euler a")

    def update_token_counts(self):
        p_count = TokenCounter.count_tokens(self.prompt_input.text())
        n_count = TokenCounter.count_tokens(self.negative_prompt_input.text())
        limit = 77 # Hardcoded for SD1.5 as per current project scope

        # Update Prompt Count
        self.prompt_token_count.setText(f"{p_count} / {limit}")
        if p_count > limit:
            self.prompt_token_count.setStyleSheet("color: #ff4444; font-weight: bold;")
        else:
            self.prompt_token_count.setStyleSheet("color: #888;")

        # Update Negative Count
        self.negative_token_count.setText(f"{n_count} / {limit}")
        if n_count > limit:
            self.negative_token_count.setStyleSheet("color: #ff4444; font-weight: bold;")
        else:
            self.negative_token_count.setStyleSheet("color: #888;")

    def handle_generation(self):
        prompt = self.prompt_input.text()
        neg_prompt = self.negative_prompt_input.text()
        
        if prompt and TokenCounter.count_tokens(prompt) <= 77:
            # Update UI state immediately
            self.generate_button.setEnabled(False)
            self.status_label.setText("Initializing...")
            
            task_id = str(uuid.uuid4())
            params = {
                'model': self.model_selector.currentText(), 
                'prompt': prompt,
                'negative_prompt': neg_prompt,
                'seed': self.seed_input.value(),
                'steps': self.steps_input.value(),
                'guidance_scale': self.cfg_input.value(),
                'width': self.width_input.value(),
                'height': self.height_input.value(),
                'sampler': self.sampler_input.currentText()
            }
            self.engine.submit_task(task_id, params)
        elif TokenCounter.count_tokens(prompt) > 77:
            self.status_label.setText("Error: Prompt exceeds 77 tokens!")
        else:
            self.status_label.setText("Error: Prompt is empty.")

    def on_task_completed(self, task_id, result):
        self.generate_button.setEnabled(True)
        self.status_label.setText("Generation Complete")
        if result and result.lower().endswith(".png"):
            self.preview.display_image(result)
        else:
            self.preview.display_text(f"Done! Result: {result}")

    def on_progress_updated(self, data):
        """Updates the status label and checks if the image is ready to display."""
        try:
            # 1. Update the status text (Standard update)
            status = data.get('status', '')
            self.status_label.setText(f"Status: {status}")
            
            # 2. Check for an image path
            image_path = data.get('image_path')
            if image_path:
                # If we get a new path, store it as the 'pending' image
                self._current_image_path = image_path
                
                # Immediately check if it's ready
                self._check_and_display(image_path)
            else:
                # Even if there's no image_path in THIS specific update, 
                # the engine might still be writing the file from a previous update.
                # So we check our 'pending' path again.
                if self._current_image_path:
                    self._check_and_display(self._current_image_path)
        except Exception as e:
            print(f"Error in on_progress_updated: {e}")

    def _check_and_display(self, filepath):
        """Internal helper to verify file exists and is ready."""
        import os
        try:
            # Only display if the file exists AND is not empty
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                self.preview.display_image(filepath)
                # Reset our pending path so we don't keep trying to display it
                self._current_image_path = None 
        except Exception as e:
            # If the file is locked by the OS, just wait for the next progress update
            print(f"File not ready yet or locked: {e}")

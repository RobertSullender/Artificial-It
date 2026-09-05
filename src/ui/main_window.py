# SPDX-License-Identifier: MIT
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt
from core.resource_monitor import ResourceMonitor
from core.model_manager import ModelManager
from core.engine import ExecutionEngine
from ui.tabs.imagine_it import ImagineItTab
from ui.tabs.talk_2_it import Talk2ItTab
from ui.tabs.structure_it import StructureItTab
from ui.tabs.train_it import TrainItTab
from ui.settings_dialog import SettingsDialog
from utils.config_manager import settings
import shutil

class MainWindow(QMainWindow):

    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.setWindowTitle("Artificial-It")
        self.resize(1280, 720)

        # Core Components
        self.model_manager = ModelManager()
        self.engine = ExecutionEngine(self.model_manager)
        # Initialize Resource Monitor
        self.monitor = None
        self.start_resource_monitor()

        # Central Widget and Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(True)

        # Initialize Tabs with injected engines/managers
        self.imagine_tab = ImagineItTab(self.engine)
        self.tabs.addTab(self.imagine_tab, "Imagine-It")
        self.tabs.addTab(Talk2ItTab(self.engine), "Talk-2-It")
        self.tabs.addTab(StructureItTab(self.engine), "Structure-It")
        self.tabs.addTab(TrainItTab(self.engine), "Train-It")

        tabs_row = QWidget()
        tabs_layout = QVBoxLayout(tabs_row)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.addWidget(self.tabs)

        self.settings_button = QToolButton()
        self.settings_button.setText("⚙")
        self.settings_button.setToolTip("Settings")
        self.settings_button.setAccessibleName("Settings")
        self.settings_button.setFixedSize(36, 28)
        self.settings_button.setStyleSheet(
            "QToolButton { padding-bottom: 5px; padding-right: 13px; }"
        )

        self.settings_button.clicked.connect(self.open_settings)
        self.tabs.setCornerWidget(self.settings_button, Qt.Corner.TopRightCorner)

        layout.addWidget(tabs_row)
        # Status Bar for Resource Monitor
        self.status_bar = self.statusBar()
        self.stats_label = QLabel("Initializing resources...")
        self.status_bar.addWidget(self.stats_label)

    def start_resource_monitor(self):
        if self.monitor is None:
            self.monitor = ResourceMonitor()
            self.monitor.stats_updated.connect(self.update_resource_stats)
        self.monitor.start()

    def open_settings(self):
        dialog = SettingsDialog(self.theme_manager, self)
        if dialog.exec():
            self.apply_resource_setting()
            self.imagine_tab.set_live_preview_enabled(
                dialog.preview_input.isChecked()
            )

    def apply_resource_setting(self):
        enabled = settings.get("ui.resource_monitor", True)
        if enabled:
            if self.monitor is None or not self.monitor.isRunning():
                self.monitor = ResourceMonitor()
                self.monitor.stats_updated.connect(self.update_resource_stats)
                self.monitor.start()
        elif self.monitor is not None:
            self.monitor.stop()
            self.stats_label.setText("Resources Off")

    def update_resource_stats(self, stats):
        if not settings.get("ui.resource_monitor", True):
            self.stats_label.setText("Resources Off")
            return
        cpu = stats.get('cpu_percent', 0)
        ram = stats.get('ram_percent', 0)
        gpu_p = stats.get('gpu_percent', 0)
        gpu_m = stats.get('gpu_mem_used_gb', 0)
        
        self.stats_label.setText(
            f"CPU: {cpu}% | RAM: {ram}% ({stats.get('ram_used_gb', 0)}GB) | "
            f"GPU: {gpu_p}% ({gpu_m}GB)"
        )

    def closeEvent(self, process):
        if self.monitor is not None:
            self.monitor.stop()
        
        # ✅ NEW: Delete entire temp directory when app closes (final safety net)
        if hasattr(self.engine, 'temp_dir') and self.engine.temp_dir.exists():
            try:
                shutil.rmtree(str(self.engine.temp_dir))
                print(f"Cleaned up temporary files: {self.engine.temp_dir}")
            except Exception as e:
                print(f"Warning: Could not cleanup temp dir on exit: {e}")
        
        super().closeEvent(process)


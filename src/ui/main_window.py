from PyQt6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel
from core.resource_monitor import ResourceMonitor
from core.model_manager import ModelManager
from core.engine import ExecutionEngine
from ui.tabs.imagine_it import ImagineItTab
from ui.tabs.talk_2_it import Talk2ItTab
from ui.tabs.structure_it import StructureItTab
from ui.tabs.train_it import TrainItTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Artificial-It")
        self.resize(1280, 720)

        # Core Components
        self.model_manager = ModelManager()
        self.engine = ExecutionEngine(self.model_manager)
        # Initialize Resource Monitor
        self.monitor = ResourceMonitor()
        self.monitor.stats_updated.connect(self.update_resource_stats)
        self.monitor.start()

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
        self.tabs.addTab(ImagineItTab(self.engine), "Imagine-It")
        self.tabs.addTab(Talk2ItTab(self.engine), "Talk-2-It")
        self.tabs.addTab(StructureItTab(self.engine), "Structure-It")
        self.tabs.addTab(TrainItTab(self.engine), "Train-It")

        layout.addWidget(self.tabs)
        # Status Bar for Resource Monitor
        self.status_bar = self.statusBar()
        self.stats_label = QLabel("Initializing resources...")
        self.status_bar.addWidget(self.stats_label)

    def update_resource_stats(self, stats):
        cpu = stats.get('cpu_percent', 0)
        ram = stats.get('ram_percent', 0)
        gpu_p = stats.get('gpu_percent', 0)
        gpu_m = stats.get('gpu_mem_used_gb', 0)
        
        self.stats_label.setText(
            f"CPU: {cpu}% | RAM: {ram}% ({stats.get('ram_used_gb', 0)}GB) | "
            f"GPU: {gpu_p}% ({gpu_m}GB)"
        )

    def closeEvent(self, process):
        self.monitor.stop()
        super().closeEvent(process)


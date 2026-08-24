# 🏛️ Architecture Documentation: Technical Design & Patterns

**Project**: Artificial-It  
**Last Updated**: 2025-08-23  
**Version**: v1.0 (Initial Technical Documentation)

---

## System Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Artificial-It Application                │
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   MainWindow │◄───►│  Tab System  │◄───►│ Feature Tabs │    │
│  │  (Entry Pt)  │     │(QTabWidget)  │     │  - Imagine   │    │
│  └──────────────┘     └──────┬───────┘     │  - Structure │    │
│                              │             │  - Talk       │    │
│                              │             │  - Train      │    │
│                              ▼             └──────────────┘    │
│                    ┌──────────────────────────────┐            │
│                    │     UI Layer (PyQt6)         │            │
│                    │  - Signals/Slots            │            │
│                    │  - Custom Widgets           │            │
│                    │  - Event Loop Integration   │            │
│                    └──────────────┬───────────────┘            │
│                                  │                             │
│                              ┌───▼──────────────────┐          │
│                              │ Core Engine Layer    │          │
│                              │                      │          │
│              ┌───────────────┴────┐  ┌─────────────┴──┐       │
│              │ ExecutionEngine    │◄─┤ LoopManager    │       │
│              │ (Task Coordination)│   │(Async Event    │       │
│              └────────────────────┘   │ Loop Handling)│       │
│                                       └───────────────┘       │
│                                                                  │
│                              ┌──────────────┐                  │
│                              │ ModelManager │◄────────────────┤
│                              │(Model Loading│  Direct          │
│                              │& Caching)    │   Integration    │
│                              └──────────────┘                  │
│                                                                  │
│                              ┌──────────────────┐              │
│                              │  GPU Inference   │              │
│                              │ (PyTorch + CUDA) │              │
│                              │  ThreadPoolExec. │              │
│                              └──────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Architectural Decisions

### 1. **Async-Await Pattern for Non-Blocking Operations** 🔄

**Decision**: Use Python's `asyncio` framework with strategic thread offloading

**Rationale**:
- PyQt6 event loop must remain responsive during long-running operations
- GPU inference is I/O bound (waiting on hardware), ideal for async context
- Model loading is CPU/GPU intensive, should not block UI thread

**Implementation Pattern**:
```python
async def run_task(self, task_id: str, params: Dict[str, Any]):
    # Update UI without blocking
    self.progress_updated.emit({"task_id": task_id, "status": "Starting..."})
    
    # Offload synchronous work to background thread
    model_obj = await asyncio.to_thread(
        self.model_manager.load_model, 
        model_name
    )
    
    # GPU inference runs in executor workers (still non-blocking)
    result = await run_pipeline_inference(model_obj, params)
    
    # Emission processed on main event loop thread
    self.task_completed.emit(result)
```

**Trade-offs Considered**:
| Approach | Pros | Cons | Selected? |
|----------|------|------|-----------|
| Pure synchronous | Simple implementation | Blocks UI, poor UX | ❌ Rejected |
| Thread pool only | Proven pattern | Complex state management | ❌ Partially used |
| **Asyncio + threading** | Event loop friendly, clean code | Requires async knowledge | ✅ **Chosen** |

**Documentation Reference**: [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)

---

### 2. **Signal-Slot Communication for UI Updates** 📡

**Decision**: Leverage PyQt6's built-in signal-slot system for decoupled component communication

**Rationale**:
- Thread-safe across event loop and worker threads
- Automatic queue management prevents race conditions
- Built-in disconnect/cleanup prevents memory leaks

**Pattern Used**:
```python
# Engine emits signal (can be from any thread):
self.progress_updated.emit({
    "task_id": task_123,
    "status": "Step 5/20",
    "percentage": 25
})

# UI receives and processes on main thread:
engine.progress_updated.connect(self.on_progress_updated)

def on_progress_updated(self, data):
    # Safe to update UI here (Qt ensures main thread)
    self.live_status_label.setText(f"Step {data['step']}/{data['total']}")
```

**Critical Rules**:
1. **NEVER** emit signals directly from worker threads without proper synchronization
2. **ALWAYS** use `QApplication.invokeLater()` for UI updates from non-main threads
3. **DISCONNECT** all signals when closing components to prevent dangling references

**Anti-Pattern Avoided**:
```python
# ❌ WRONG: Direct thread manipulation (causes our original bug)
def on_progress_updated(self, data):
    if False:  # Dead code that should have been removed
        QThread.currentThread().start()  # Never starts!
    
    # This was causing the "stuck at 0%" issue
```

**Fixed Pattern**:
```python
# ✅ CORRECT: Simple, clean signal handling
def on_progress_updated(self, data):
    self._update_live_preview(data)

def _update_live_preview(self, data):
    if data.get("percentage"):
        self.live_progress_label.setText(f"{data['percentage']}%")
```

---

### 3. **Model Manager with Lazy Loading & Caching** 💾

**Decision**: Centralized model management with intelligent caching and versioning

**Design Goals**:
- Load heavy models only when needed (lazy loading)
- Prevent duplicate loads of same model in session
- Support multiple models simultaneously (different tabs/tasks)
- Clean up unused models to free VRAM

**Class Structure**:
```python
class ModelManager:
    def __init__(self):
        self.loaded_models = {}           # {model_name: model_instance}
        self.load_history = []            # Track all loads for cleanup
    
    async def load_model(self, model_name: str) -> DiffusionPipeline:
        if model_name not in self.loaded_models:
            print(f"Loading {model_name}...")  # Status emission
            
            # Offload to thread (asyncio.to_thread fix)
            pipeline = await asyncio.to_thread(
                lambda: StableDiffusionPipeline.from_pretrained(model_name)
            )
            
            self.loaded_models[model_name] = pipeline
            self.load_history.append(model_name)
        
        return self.loaded_models[model_name]
    
    def unload_model(self, model_name: str):
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]  # Free VRAM
```

**Memory Management Strategy**:
- **LRU Caching**: Automatically evict least-recently used models
- **Manual Unload**: `unload_model()` called when switching tabs
- **VRAM Monitoring**: Log memory usage for debugging OOM issues

---

### 4. **ExecutionEngine as Task Orchestrator** ⚙️

**Decision**: Single-threaded execution engine coordinating complex workflows

**Responsibilities**:
1. Receive task requests from UI layer
2. Validate inputs and parameters
3. Load/prepare required models
4. Execute inference pipeline
5. Emit progress updates throughout process
6. Handle errors gracefully with user feedback

**Workflow Diagram**:
```
Task Request (UI) 
    ↓
ExecutionEngine.run_task()
    ├─► Validate Parameters
    ├─► Emit "Starting..." Status
    ├─► Load Model (async thread offload)
    ├─► Execute Inference Loop
    │   └─► Emit "Step X/20" for each iteration
    ├─► Save Output File
    └─► Emit "Completed" + Result
```

**Error Handling Pattern**:
```python
async def run_task(self, task_id: str, params: Dict):
    try:
        # Normal execution flow
        pass
    except Exception as e:
        # User-friendly error message
        self.error_occurred.emit({
            "task_id": task_id,
            "error_type": type(e).__name__,
            "message": str(e)  # For debugging
        })
        raise
```

---

## Component Interaction Patterns

### Pattern 1: Request-Response Cycle

```python
# User clicks Generate Button
def handle_generation(self):
    params = self._collect_params()  # Gather all UI inputs
    
    # Submit to engine (non-blocking)
    task_id = self.engine.submit_task(params)
    
    # Connect callbacks for updates
    self.engine.progress_updated.connect(self.on_progress_updated)
```

### Pattern 2: Progress Monitoring Chain

```python
# Engine emits progress during inference
self.engine.progress_updated.connect(self.on_progress_updated)

def on_progress_updated(self, data):
    # Parse and validate incoming data
    step = data.get("step")
    total = data.get("total")
    
    # Update UI components
    self.live_status_label.setText(f"Generating... Step {step}/{total}")
    QApplication.invokeLater(  # Ensure main thread
        lambda: self.live_progress_label.setText(f"{int(step/total*100)}%")
    )
```

### Pattern 3: Result Handling & Cleanup

```python
# Engine completes task
self.engine.task_completed.connect(self.on_task_completed)

def on_task_completed(self, result):
    # Disconnect to prevent memory leaks
    self.engine.progress_updated.disconnect()
    self.engine.task_completed.disconnect()
    
    # Display results
    self.preview.display_image(result["filepath"])
    
    # Reset UI state
    self.reset_generation_form()
```

---

## Threading & Concurrency Model

### Thread Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Main Event Loop Thread                │
│  (Qt Application, Signal/Slot, UI Rendering)            │
│                 ┌──────────────┐                        │
│                 │ asyncio      │◄── Handles async tasks │
│                 │   .to_thread()│                        │
│                 └───────┬──────┘                        │
│                         │                                │
│              ┌──────────▼───────────┐                   │
│              │  ThreadPoolExecutor  │◄── GPU Workers    │
│              │ (Inference Operations)│                  │
│              └──────────────────────┘                   │
└─────────────────────────────────────────────────────────┘

Worker Thread Responsibilities:
1. Model Loading (Disk I/O + Initial GPU allocation)
2. Diffusion Pipeline Inference (CPU preprocessing)
3. Image Saving (File system writes)

Main Thread Responsibilities:
1. UI rendering and event processing
2. Signal/slot dispatch
3. User input handling
```

### Critical Threading Rules

**Rule 1**: Never call Qt methods from worker threads
```python
# ❌ WRONG: Can cause race conditions or crashes
def worker_function():
    QApplication.processEvents()  # Never do this!
    self.some_widget.setText("Hello")  # Must be main thread only
```

**Rule 2**: Use `invokeLater()` for delayed UI updates from workers
```python
# ✅ CORRECT: Schedule on event loop queue
def worker_function():
    QApplication.invokeLater(
        lambda: self.some_widget.setText("Hello from worker")
    )
```

**Rule 3**: Keep async code pure and side-effect free
```python
async def compute_result(input_data):
    # Pure computation, no direct Qt calls
    result = heavy_computation(input_data)
    return result

# Signal handler bridges to UI layer
def on_compute_complete(result):
    QApplication.invokeLater(lambda: self.update_ui_with(result))
```

---

## Memory Management Strategy

### VRAM Optimization Considerations

**Problem**: Stable Diffusion models require 4-6GB VRAM, but many consumer GPUs have <4GB

**Current Strategy**:
1. Use float16 precision (reduces memory by ~50%)
2. Load only required components (unet, vae, text_encoder separately)
3. Offload non-essential layers to CPU during inference

**Future Optimizations**:
```python
# Potential future implementation:
def optimize_for_low_vram(model):
    # Use 8-bit quantization where possible
    model.enable_attention_slicing(1)
    
    # Offload text encoder to CPU (often unnecessary for image gen)
    model.text_encoder.to("cpu")
```

### Memory Leak Prevention

**Pattern**: Always disconnect signals when components are no longer needed
```python
def close_tab(self):
    # Disconnect all engine callbacks
    self.generate_button.clicked.disconnect()
    self.engine.progress_updated.disconnect()
    self.engine.task_completed.disconnect()
    
    # Clear references for garbage collection
    self._current_image_path = None
    del self.preview
    
    # Optional: Explicitly unload models if exclusive to this tab
    model_manager.unload_current_model()
```

---

## Data Flow Documentation

### Complete Image Generation Flow

```mermaid
sequenceDiagram
    participant User as 👤 User
    participant UI as 🖥️ PyQt6 UI
    participant Engine as ⚙️ ExecutionEngine
    participant Model as 🎭 ModelManager
    participant GPU as 📐 PyTorch GPU
    participant File as 💾 File System

    User->>UI: Click "Generate" button
    UI->>UI: Collect parameters from form
    UI->>Engine: Submit task with params
    Engine->>Engine: Validate inputs
    
    Note over Engine,Model: Async operation starts
    Engine->>Engine: Emit "Starting..." status signal
    Engine->>Model: Request model load (async)
    
    par Model Loading
        Model->>Disk: Load model files
        Model->>GPU: Allocate VRAM
        Model-->>Engine: Return pipeline object
    and GPU Inference Loop
        loop 20 steps
            GPU->>GPU: Forward pass
            Engine->>UI: Emit "Step X/20" progress
            UI->>UI: Update status label
        end
    end
    
    Engine->>File: Save output image
    Engine->>Engine: Emit "Completed" signal
    Engine-->>UI: Return result dict
    UI->>UI: Display image in preview
    UI->>User: Show generated image

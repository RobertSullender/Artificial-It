# 📋 Changelog

All notable changes to the Artificial-It project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed
- **Critical**: Fixed blocking model loading issue causing application crashes (#1)
  - Wrapped synchronous `model_manager.load_model()` with `asyncio.to_thread()` 
  - Prevents event loop freezing during model initialization
  
- **High Priority**: Updated callback signature for Diffusers v0.31+ compatibility
  - Changed from old API `(pipe, step, timestep, callback_kwargs)` to new format `(step_idx, t, latents)`
  - Fixed variable reference: `pipe.vae` → `model_obj.vae`
  - Enables progress bar updates during image generation
  
- **High Priority**: Removed invalid `QApplication.invokeLater()` wrapper in PyQt6
  - PyQt6 signals are already thread-safe; manual wrappers unnecessary
  - Eliminates AttributeError and simplifies code

### Known Issues
- Sampler parameter not affecting generation output (Diffusers v0.31+ architectural limitation)
  - Documented as known issue, disabled for future enhancement
  
- Progress percentage updates working but visual bar still at 0% (incomplete fix)
  - Status text updates correctly (5% → 10% → ... → 100%)
  - Visual progress bar widget needs additional configuration

### Enhanced
- Added comprehensive debug logging throughout execution pipeline
- Created professional documentation system in `src/docs/`
- Implemented session log tracking for development continuity

---

## [0.1.0] - 2025-08-23

### Added
- Initial project structure with PyQt6 main window
- Imagine mode UI with prompt input, model selection, and controls
- Model management system with async loading support
- Live preview widget integration
- Git repository initialization
- Professional documentation framework (PROJECT_SUMMARY.md, TODO_LIST.md, CURRENT_TASK.md)

### Fixed
- Removed dead thread code from Imagine-It tab
- Added missing PreviewWidget initialization
- Created proper signal-slot connections for progress handling

---

*Changelog v0.1 | Last Updated: 2025-08-23*

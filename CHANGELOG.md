# 📋 Changelog

All notable changes to the Artificial-It project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning]((https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - v1.1 (Current Development)
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

- **High Priority**: Moved preview storage to dedicated temporary directory (#2)
  - Changed from `outputs/previews/` to `/tmp/artificial_it_temp/previews/`
  - Temp folder hidden from user-facing outputs/ directory ✅
  - Preview files auto-deleted after generation completes
  - Entire temp directory cleanup on app exit ✅
  - Prevents empty folder confusion in outputs/ (user experience improvement)

### Enhanced
- ✅ **Temp Directory Architecture**: Established dedicated temporary storage for future scalability
  - Location: OS standard temp directory (`/tmp/artificial_it_temp/`)
  - Auto-creates if missing (handles crashes, manual deletion)
  - Ready for future subfolders: cache/, downloads/, batch_temp/, debug/

- ✅ Fixed resolution morphing issue: Previews now use correct target dimensions instead of hardcoded 512×512
- ✅ Implemented automatic cleanup: Intermediate preview files are removed after generation completes
- Added comprehensive debug logging throughout execution pipeline
- Created professional documentation system in `src/docs/`
- Implemented session log tracking for development continuity

### Documentation
- Added comprehensive implementation documentation in `src/docs/TEMP_DIR_IMPLEMENTATION.md`
- Created verification guide in `src/docs/TEMP_DIR_VERIFICATION.md`
- Updated this changelog with detailed version history

### Planned Features (Under Review)
- **Auto-incrementing output filenames**: Generate sequential numbered files (img_001.png, img_002.png, etc.) instead of timestamp-based naming
  - Prevents overwriting previous generations with same filename
  - Maintains organized, sortable output history
  - Priority: High (user requested feature)

### Known Issues
- Sampler parameter not affecting generation output (Diffusers v0.31+ architectural limitation)
  - Documented as known issue, disabled for future enhancement
  
- Progress percentage updates confirmed working by user testing (0% → 100%)
  - Status text updates correctly (5% → 10% → ... → 100%)

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



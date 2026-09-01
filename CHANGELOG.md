# 📋 Changelog

All notable changes to the Artificial-It project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - v1.1 (Future Development)
---

## [v0.33] - 2025-08-25 (Alpha Preview - Pre-Release)
### Status
> ⚠️ **PRE-RELEASE ALPHA**: This is version 0.33 in active development. Only Imagine mode with SD1.5 is fully functional. Talk-2-It, Structure-It, and Train-It features are marked "Coming Soon" as placeholders for future releases.
### Fixed
- **Pre-Release Quality**: Refined placeholder tabs to remove all misleading functionality
  - `talk_2_it.py`: Removed dummy chat code, added clear "Not_Implemented: Coming Soon!" message
  - `structure_it.py`: Removed misleading ControlNet references, replaced with honest placeholder
  - `train_it.py`: Removed training UI elements that didn't work
  - All tabs now consistently display identical "Coming Soon" messaging in both UI and console

### Enhanced
- **Documentation Accuracy**: Updated README.md to reflect true development status
  - Header changed from "Production Ready" to "Alpha Preview - Under Active Development (v0.33)"
  - Added features section distinguishing stable vs under-development capabilities
  - Known limitations updated with version-specific context
---

## [v0.1.0] - 2025-08-23 (Initial Release)

### Added
- Initial project structure with PyQt6 main window
- Imagine mode UI with prompt input, model selection, and controls
- Model management system with async loading support (`asyncio.to_thread()`)
- Live preview widget integration
- Temp directory architecture for previews (`/tmp/artificial_it_temp/previews/`)
- Git repository initialization
- Professional documentation framework in `src/docs/`
  - ARCHITECTURE.md - Technical design patterns
  - PROJECT_SUMMARY.md - Mission and goals
  - CURRENT_TASK.md - Active development issues
  - DEVELOPMENT_LOG.md - Session tracking

### Fixed
- **Critical**: Removed dead thread code from Imagine-It tab (blocking UI issue)
- Added missing PreviewWidget initialization in tabs
- Created proper signal-slot connections for progress handling
- Updated callback signature for Diffusers v0.31+ compatibility:
  - Changed from old `(pipe, step, timestep, callback_kwargs)` format
  - New format: `(step_idx, t, latents)` with `model_obj.vae` reference
- Fixed resolution morphing issue (previews now use correct target dimensions)
- Implemented automatic cleanup of intermediate preview files

### Known Issues (v0.1.0)
- **Sampler Parameter**: Not affecting generation output (Diffusers v0.31+ architectural limitation - sampler set at pipeline creation time)
- **Model Support**: Only SD1.5 implemented; SDXL/SD3.5 planned for future releases
- **Placeholder Features**: Talk-2-It, Structure-It, Train-It tabs are placeholders only

---

## [0.0.1] - 2025-08-22 (Pre-Initial)

### Added
- Project initialization structure
- Basic Git repository setup


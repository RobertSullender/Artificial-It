# 🧪 Testing Strategy & Issue Tracking - Session 2025-08-23

**Date**: 2025-08-23  
**Session Goal**: Test fixes for progress bar and sampler issues, establish commit workflow  
**Status**: Issues Identified | Fixes Required  

---

## 🔴 Issues Found in Testing

### Issue #1: QApplication.invokeLater Doesn't Exist ❌
```
Error: 'QApplication' object has no attribute 'invokeLater'
```
**Files Affected**: `src/ui/tabs/imagine_it.py`  
**Root Cause**: PyQt6 uses different API than older Qt versions

**Diagnosis Steps**:
1. ✅ Confirmed error appears in terminal output for every progress update
2. ❌ Progress bar stuck at 0% confirmed (from previous testing)

**Fix Options**:
- **Option A (Recommended)**: Remove invokeLater entirely - PyQt6 signals are already thread-safe
- **Option B**: Use `QMetaObject.invokeMethod()` with `Qt.QueuedConnection`
- **Option C**: Use simple `emit` pattern since signals already route to main thread

**Testing Method**:
```bash
# Run app, generate image, check:
1. Terminal shows no "invokeLater" errors
2. Progress percentage updates (5% → 10% → ... → 100%)
3. No other exceptions in output
```

---

### Issue #2: set_scheduler Not Available ❌
```
Warning: Could not set sampler "Euler a": 'StableDiffusionPipeline' object has no attribute 'set_scheduler'.
```
**Files Affected**: `src/core/engine.py`  
**Root Cause**: Diffusers v0.31+ uses built-in schedulers, cannot dynamically switch per-call

**Diagnosis Steps**:
1. ✅ Confirmed error appears: "object has no attribute 'set_scheduler'"
2. ⚠️ Sampler parameter extracted but never actually used in inference
3. ❌ Generated images always use default sampler regardless of dropdown selection

**Diffusers API Research Needed**:
- Check if scheduler is determined at pipeline creation time (not per-call)
- Verify available samplers: `model_obj.scheduler` attribute
- Check for alternative methods to change sampling behavior

**Fix Options**:
- **Option A**: Remove set_scheduler call entirely - use default sampler from model config
- **Option B**: Pass `sampler_name` parameter in pipeline call (if supported)
- **Option C**: Use `model_obj.scheduler.set_timesteps()` instead of set_scheduler()
- **Option D**: Accept limitation - sampler dropdown is for informational UI only

**Testing Method**:
```bash
# Run app with different samplers:
1. Select "Euler a", generate image with prompt="cat", seed=12345
2. Select "DPM++ 2M", generate SAME prompt + SAME seed=12345  
3. Compare outputs visually
   - Should see difference in noise reduction patterns
   - OR confirm limitation: images are identical (default sampler always used)
```

---

### Issue #3: Callback Signature Wrong ❌
```
TypeError: callback_on_step_end() missing 1 required positional argument: 'callback_kwargs'
```
**Files Affected**: `src/core/engine.py`  
**Root Cause**: PyQt6 callback signature is `(step_idx, t, latents)` not `(pipe, step, timestep, callback_kwargs)`

**Diagnosis Steps**:
1. ✅ Confirmed error appears once per generation attempt
2. ✅ Generation crashes before completion (no image shown)
3. ❌ Progress callbacks never fire due to crash

**Diffusers Callback Documentation**:
- Old API: `callback(pipe, step, timestep, callback_kwargs)` - deprecated
- New API (v0.31+): `callback(step_idx, t, latents)` - current

**Fix Required**:
```python
# BEFORE (wrong):
def callback_on_step_end(pipe, step, timestep, callback_kwargs):
    latents = callback_kwargs.get("latents")  # ❌ Wrong!

# AFTER (correct for v0.31+):
def callback_on_step_end(step_idx, t, latents):
    print(f'DEBUG Callback called: step={step_idx}')  # ✅ Works
```

**Testing Method**:
```bash
# Run app, generate image:
1. Terminal shows "DEBUG Callback called:" messages for each step
2. Progress percentage updates during generation
3. Final image displays correctly after completion
4. No crash or exception in terminal
```

---

## 🎯 Priority Fix Order

### Phase 1: Critical (Blocks All Functionality) 🔴
1. **Fix Callback Signature** - Issue #3
   - Change from `(pipe, step, timestep, callback_kwargs)` 
   - To `(step_idx, t, latents)`
   - Expected impact: Enables progress tracking + intermediate previews

### Phase 2: High Priority (UX Enhancement) 🟡
2. **Remove invokeLater Wrapper** - Issue #1
   - PyQt6 signals already thread-safe
   - Simply remove the problematic code
   - Expected impact: Clean logs, no errors

3. **Address Sampler Limitation** - Issue #2
   - Remove set_scheduler call (not supported in v0.31+)
   - Add comment explaining limitation
   - Optional: Document as known limitation or defer to future phase
   - Expected impact: Cleaner code, honest documentation

---

## 📝 Testing Protocol for Each Fix

### Before Commit Checklist:
- [ ] Run `python src/main.py`
- [ ] App starts without import errors
- [ ] UI window appears
- [ ] Model loads (shows "Loading sd15..." status)

### Generate Test:
- [ ] Enter prompt: "cat sitting" 
- [ ] Set seed to fixed value (e.g., 12345)
- [ ] Select any sampler (e.g., Euler a)
- [ ] Click "Generate"

### Verify Fixes Applied:
```bash
# Check terminal output for these patterns:

✅ PROGRESS BAR FIX VERIFIED IF:
   - See "Step 1/20", "Step 5/20", etc. messages
   - See percentage updating (not stuck at 0%)
   - NO "invokeLater" errors
   - Image appears in preview window after completion

✅ CALLBACK FIX VERIFIED IF:
   - See "DEBUG Callback called: step=1" message
   - See intermediate images saved (in outputs/previews/)
   - No crash during generation

✅ SAMPLER LIMITATION ACCEPTED IF:
   - No set_scheduler errors OR
   - Documented as future work with comment in code
```

---

## 📊 Expected Output Patterns

### After Fixes Applied (Desired):
```bash
DEBUG Progress data: {'status': 'Initializing...'}
DEBUG Progress data: {'status': 'Loading sd15...'}
DEBUG Using sampler: Euler a  ← Optional, if still trying
DEBUG Progress data: {'status': 'Starting Diffusion...'}
DEBUG Callback called: step=1   ← NEW! Shows callback works
DEBUG Progress data: {'status': 'Step 1/20', 'percentage': 5.0}    ← PROGRESS BAR WORKS!
DEBUG Callback called: step=2
DEBUG Progress data: {'status': 'Step 5/20', 'percentage': 25.0}   ← UPDATING!
... (continues through all steps) ...
DEBUG Progress data: {'status': 'Generation Complete!'}
Image displayed in preview window ✅
```

### Current State (Before Fixes):
```bash
❌ Error: invokeLater doesn't exist (x many times)
❌ Warning: set_scheduler not found
❌ TypeError: callback missing argument (crashes generation)
NO progress messages shown
NO intermediate images created
FINAL IMAGE DOESN'T APPEAR (due to crash before completion)
```

---

## 🎯 Commit Strategy

**Rule**: Only commit when ALL tests pass for that specific fix.

### Commit 1: Callback Signature Fix (if Phase 1#1 passes)
```bash
git add src/core/engine.py
git commit -m "fix(engine): update callback signature for Diffusers v0.31+ API"
```

### Commit 2: Remove invokeLater Wrapper (if Phase 1#2 passes)  
```bash
git add src/ui/tabs/imagine_it.py
git commit -m "fix(ui): remove incorrect QApplication.invokeLater wrapper"
```

### Commit 3: Document Sampler Limitation (Phase 2)
```bash
git add src/core/engine.py
git commit -m "docs(engine): clarify sampler limitation in Diffusers v0.31+"
```

---

## 🔗 Quick Reference Commands

```bash
# Start app and watch for errors
python src/main.py

# Check syntax before running
python -m py_compile src/ui/tabs/imagine_it.py && echo "UI OK"
python -m py_compile src/core/engine.py && echo "Engine OK"

# View recent changes
git status
git diff

# Check specific file
git diff src/core/engine.py

# Run generation test (use in terminal)
echo "Testing with prompt: cat"
```

---

## 📞 Communication Template

When reporting results, include:

1. **Fix Tested**: [Describe which fix was tested]
2. **Terminal Output**: Copy relevant log lines
3. **Result**: ✅ Pass / ❌ Fail (describe why)
4. **Next Step**: What to try next or what needs fixing

Example:
```
Fix Tested: Callback signature fix in engine.py
Terminal Output: "DEBUG Callback called: step=1", "Step 1/20" shown
Result: ✅ Pass - Progress bar now updates, no crash
Next Step: Test progress percentage update (should go 5% → 10%...)
```

---

*Testing Strategy v1.0 | Generated: 2025-08-23 | Status: Ready for Implementation*  
*Part of Artificial-It Development Documentation Suite*